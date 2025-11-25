"""
WebSocket server for streaming gesture control data to the Tauri frontend.

Runs the gesture detection pipeline and streams:
- Video frames (base64 JPEG)
- Gesture detection results
- Clutch state
- Action triggers
- Configuration updates
"""
import asyncio
import base64
import json
import logging
import signal
import cv2
from typing import Set, Optional
import websockets
from websockets.server import WebSocketServerProtocol
from dotenv import load_dotenv

from src.hand_tracker import HandTracker
from src.clutch_detector import ClutchDetector
from src.hybrid_gesture_detector import HybridGestureDetector
from src.gemini_gesture_detector import GeminiGestureDetector
from src.action_handler import ActionHandler
from src.config_manager import ConfigManager
from src.utils.window_manager import WindowManager

# Load environment variables
load_dotenv('.env.local')

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Global state
connected_clients: Set[WebSocketServerProtocol] = set()
shutdown_event = asyncio.Event()


class GestureServer:
    """WebSocket server for gesture control streaming."""

    def __init__(self):
        self.config_manager = ConfigManager()
        self.config = self.config_manager.config

        # Extract settings
        self.camera_width = self.config.get('settings', {}).get('camera_resolution', [640, 480])[0]
        self.camera_height = self.config.get('settings', {}).get('camera_resolution', [640, 480])[1]
        self.camera_fps = self.config.get('settings', {}).get('camera_fps', 20)
        self.confidence_threshold = self.config.get('settings', {}).get('confidence_threshold', 0.7)
        self.cooldown_ms = self.config.get('settings', {}).get('cooldown_ms', 500)
        self.require_terminal_focus = self.config.get('settings', {}).get('require_terminal_focus', False)
        self.require_stable_frames = self.config.get('clutch', {}).get('require_stable_frames', 5)

        # Gemini settings
        gemini_model = self.config.get('gemini', {}).get('model', 'gemini-2.5-flash')
        gemini_sample_interval = self.config.get('gemini', {}).get('sample_interval', 0.5)
        gemini_resize_width = self.config.get('gemini', {}).get('resize_width', 256)
        use_gemini_fallback = self.config.get('hybrid_detection', {}).get('use_gemini_fallback', False)
        gesture_config = self.config.get('hybrid_detection', {}).get('gestures', {})

        # Initialize components
        self.hand_tracker = HandTracker(
            max_num_hands=2,
            min_detection_confidence=self.confidence_threshold
        )
        self.clutch_detector = ClutchDetector(require_stable_frames=self.require_stable_frames)

        # Initialize Gemini fallback (optional)
        self.gemini_fallback = None
        if use_gemini_fallback:
            try:
                self.gemini_fallback = GeminiGestureDetector(
                    model_name=gemini_model,
                    sample_interval=gemini_sample_interval,
                    stability_frames=1,
                    cooldown_ms=self.cooldown_ms,
                    resize_width=gemini_resize_width
                )
                logger.info(f"Gemini fallback initialized (model: {gemini_model})")
            except ValueError as e:
                logger.warning(f"Gemini fallback unavailable: {e}")

        # Initialize hybrid gesture detector
        self.gesture_detector = HybridGestureDetector(
            gemini_detector=self.gemini_fallback,
            cooldown_ms=self.cooldown_ms,
            use_gemini_fallback=use_gemini_fallback and self.gemini_fallback is not None,
            gesture_config=gesture_config
        )

        # Initialize action handler
        self.action_handler = ActionHandler(config_manager=self.config_manager)
        self.window_manager = WindowManager()

        # State tracking
        self.previous_gesture = None
        self.cap: Optional[cv2.VideoCapture] = None

        logger.info("GestureServer initialized")

    async def start_camera(self):
        """Initialize and start the camera."""
        self.cap = cv2.VideoCapture(0)
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.camera_width)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.camera_height)
        self.cap.set(cv2.CAP_PROP_FPS, self.camera_fps)

        if not self.cap.isOpened():
            logger.error("Failed to open webcam")
            raise RuntimeError("Failed to open webcam")

        logger.info(f"Camera started: {self.camera_width}x{self.camera_height} @ {self.camera_fps}fps")

    def stop_camera(self):
        """Stop the camera."""
        if self.cap:
            self.cap.release()
            self.cap = None
            logger.info("Camera stopped")

    def get_config_payload(self):
        """Get current gesture configuration."""
        gestures = {}
        for gesture in self.config_manager.get_all_gestures():
            config = self.config_manager.get_gesture_config(gesture)
            if config:
                gestures[gesture] = config
        return {'gestures': gestures}

    def update_gesture_command(self, gesture: str, command: str):
        """Update a gesture's command."""
        self.config_manager.set_gesture_command(gesture, command)
        self.config_manager.save_config()
        logger.info(f"Updated gesture '{gesture}' command to: {command}")

    def cleanup(self):
        """Clean up resources."""
        self.stop_camera()
        self.action_handler.cleanup()
        self.hand_tracker.close()
        logger.info("GestureServer cleaned up")


# Global server instance
server: Optional[GestureServer] = None


async def broadcast(message: dict):
    """Broadcast a message to all connected clients."""
    if not connected_clients:
        return

    data = json.dumps(message)
    disconnected = set()

    for client in connected_clients:
        try:
            await client.send(data)
        except websockets.exceptions.ConnectionClosed:
            disconnected.add(client)

    connected_clients.difference_update(disconnected)


async def handle_client(websocket: WebSocketServerProtocol):
    """Handle a WebSocket client connection."""
    global server

    connected_clients.add(websocket)
    logger.info(f"Client connected. Total clients: {len(connected_clients)}")

    try:
        # Send initial config
        if server:
            await websocket.send(json.dumps({
                'type': 'config',
                'payload': server.get_config_payload()
            }))

        async for message in websocket:
            try:
                data = json.loads(message)
                msg_type = data.get('type')

                if msg_type == 'get_config':
                    if server:
                        await websocket.send(json.dumps({
                            'type': 'config',
                            'payload': server.get_config_payload()
                        }))

                elif msg_type == 'update_gesture':
                    payload = data.get('payload', {})
                    gesture = payload.get('gesture')
                    command = payload.get('command')
                    if gesture and command and server:
                        server.update_gesture_command(gesture, command)
                        # Broadcast updated config
                        await broadcast({
                            'type': 'config',
                            'payload': server.get_config_payload()
                        })

            except json.JSONDecodeError:
                logger.warning(f"Invalid JSON from client: {message}")

    except websockets.exceptions.ConnectionClosed:
        pass
    finally:
        connected_clients.discard(websocket)
        logger.info(f"Client disconnected. Total clients: {len(connected_clients)}")


def sync_process_frame(server_instance):
    """Synchronous wrapper for process_frame."""
    if not server_instance.cap or not server_instance.cap.isOpened():
        return None

    ret, frame = server_instance.cap.read()
    if not ret:
        return None

    # Mirror effect
    frame = cv2.flip(frame, 1)

    # Process with hand tracker
    processed_frame, hands_data = server_instance.hand_tracker.process_frame(frame)

    # Get hand data
    left_hand = hands_data.get('left')
    right_hand = hands_data.get('right')

    # Update clutch detector
    clutch_engaged = server_instance.clutch_detector.update(left_hand)

    # Initialize result data
    result = {
        'frame': None,
        'clutch': {'engaged': clutch_engaged, 'stableFrames': len(server_instance.clutch_detector.detection_history)},
        'gesture': None,
        'action': None,
        'dictation': {'active': server_instance.action_handler.is_dictation_active()},
    }

    # Encode frame as base64 JPEG
    _, buffer = cv2.imencode('.jpg', processed_frame, [cv2.IMWRITE_JPEG_QUALITY, 70])
    result['frame'] = base64.b64encode(buffer).decode('utf-8')

    # Process gestures if clutch engaged
    if clutch_engaged:
        terminal_focused = not server_instance.require_terminal_focus or server_instance.window_manager.is_terminal_active()

        if terminal_focused:
            # Update gesture detector
            gesture_result = server_instance.gesture_detector.update(frame, right_hand)
            current_gesture = server_instance.gesture_detector.get_current_gesture()

            # Send gesture state
            status = server_instance.gesture_detector.get_status()
            result['gesture'] = {
                'gesture': status.get('current_gesture', 'none'),
                'confidence': status.get('current_confidence', 0),
                'source': 'local',
                'triggered': gesture_result is not None,
            }

            # Handle push-to-talk voice gestures
            if server_instance.action_handler.is_voice_gesture(current_gesture) and \
               not server_instance.action_handler.is_voice_gesture(server_instance.previous_gesture):
                if server_instance.action_handler.start_recording():
                    result['action'] = {
                        'gesture': current_gesture,
                        'description': 'Recording...',
                        'success': True,
                    }
            elif server_instance.action_handler.is_voice_gesture(server_instance.previous_gesture) and \
                 not server_instance.action_handler.is_voice_gesture(current_gesture):
                server_instance.action_handler.stop_recording()

            # Execute triggered non-voice gestures
            if gesture_result and not server_instance.action_handler.is_voice_gesture(gesture_result[0]):
                triggered_gesture = gesture_result[0]
                if triggered_gesture != 'none':
                    action_result = server_instance.action_handler.execute_gesture_action(triggered_gesture)
                    if action_result:
                        result['action'] = {
                            'gesture': triggered_gesture,
                            'description': action_result,
                            'success': True,
                        }

            server_instance.previous_gesture = current_gesture
    else:
        # Reset when clutch disengaged
        server_instance.gesture_detector.reset()
        if server_instance.action_handler.is_dictation_active():
            server_instance.action_handler.stop_recording()
        server_instance.previous_gesture = None

    # Reset clutch if no left hand
    if left_hand is None:
        server_instance.clutch_detector.reset()

    # Process transcription queue
    server_instance.action_handler.process_transcription_queue()

    return result


async def frame_loop():
    """Main loop for processing and broadcasting frames."""
    global server

    while not shutdown_event.is_set():
        if server and connected_clients:
            try:
                loop = asyncio.get_event_loop()
                result = await loop.run_in_executor(None, sync_process_frame, server)

                if result:
                    # Send frame
                    if result['frame']:
                        await broadcast({
                            'type': 'frame',
                            'payload': {'frame': result['frame']}
                        })

                    # Send clutch state
                    await broadcast({
                        'type': 'clutch',
                        'payload': result['clutch']
                    })

                    # Send gesture state if available
                    if result['gesture']:
                        await broadcast({
                            'type': 'gesture',
                            'payload': result['gesture']
                        })

                    # Send action if triggered
                    if result['action']:
                        await broadcast({
                            'type': 'action',
                            'payload': result['action']
                        })

                    # Send dictation state
                    await broadcast({
                        'type': 'dictation',
                        'payload': result['dictation']
                    })

            except Exception as e:
                logger.error(f"Error in frame loop: {e}")

        await asyncio.sleep(1 / 30)  # Target ~30fps


async def main():
    """Main entry point."""
    global server

    # Initialize server
    server = GestureServer()

    # Start camera
    await server.start_camera()

    # Handle shutdown signals
    loop = asyncio.get_event_loop()

    def signal_handler():
        logger.info("Shutdown signal received")
        shutdown_event.set()

    for sig in (signal.SIGINT, signal.SIGTERM):
        loop.add_signal_handler(sig, signal_handler)

    # Start WebSocket server
    async with websockets.serve(handle_client, "localhost", 8765):
        logger.info("WebSocket server started on ws://localhost:8765")

        # Run frame processing loop
        try:
            await frame_loop()
        except asyncio.CancelledError:
            pass

    # Cleanup
    server.cleanup()
    logger.info("Server shutdown complete")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Interrupted by user")
