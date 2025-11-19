"""
IronCoder Gesture Control for Claude Code
Main entry point for the gesture control system.
"""
import cv2
import yaml
import logging
from dotenv import load_dotenv
from src.hand_tracker import HandTracker
from src.clutch_detector import ClutchDetector
from src.gemini_gesture_detector import GeminiGestureDetector
from src.action_handler import ActionHandler
from src.utils.window_manager import WindowManager
from src.utils.visual_feedback import VisualFeedback

# Load environment variables from .env.local
load_dotenv('.env.local')


def load_config(config_path: str = "config.yaml") -> dict:
    """Load configuration from YAML file."""
    try:
        with open(config_path, 'r') as f:
            return yaml.safe_load(f)
    except FileNotFoundError:
        logging.warning(f"Config file {config_path} not found. Using defaults.")
        return {}


def main():
    """Main entry point for the gesture control system."""
    # Set up logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    logger = logging.getLogger(__name__)

    # Load configuration
    config = load_config()

    # Extract settings
    camera_width = config.get('settings', {}).get('camera_resolution', [640, 480])[0]
    camera_height = config.get('settings', {}).get('camera_resolution', [640, 480])[1]
    camera_fps = config.get('settings', {}).get('camera_fps', 20)
    confidence_threshold = config.get('settings', {}).get('confidence_threshold', 0.7)
    cooldown_ms = config.get('settings', {}).get('cooldown_ms', 500)
    require_terminal_focus = config.get('settings', {}).get('require_terminal_focus', True)
    require_stable_frames = config.get('clutch', {}).get('require_stable_frames', 5)
    show_overlay = config.get('visual_feedback', {}).get('show_overlay', True)

    # Gemini settings
    gemini_model = config.get('gemini', {}).get('model', 'gemini-2.0-flash-exp')
    gemini_sample_interval = config.get('gemini', {}).get('sample_interval', 0.5)
    gemini_stability_frames = config.get('gemini', {}).get('stability_frames', 2)
    gemini_resize_width = config.get('gemini', {}).get('resize_width', 512)

    # Get visual feedback colors
    clutch_engaged_color = tuple(config.get('visual_feedback', {}).get('clutch_indicator_color', [0, 255, 0]))
    clutch_disengaged_color = tuple(config.get('visual_feedback', {}).get('clutch_disengaged_color', [255, 0, 0]))

    logger.info("=== IronCoder Gesture Control for Claude Code ===")
    logger.info(f"Camera: {camera_width}x{camera_height} @ {camera_fps}fps")
    logger.info(f"Confidence threshold: {confidence_threshold}")
    logger.info(f"Cooldown: {cooldown_ms}ms")
    logger.info(f"Require terminal focus: {require_terminal_focus}")
    logger.info(f"Clutch stable frames: {require_stable_frames}")
    logger.info(f"Gemini model: {gemini_model}")
    logger.info(f"Gemini sample interval: {gemini_sample_interval}s")

    # Initialize components
    hand_tracker = HandTracker(
        max_num_hands=2,
        min_detection_confidence=confidence_threshold
    )
    clutch_detector = ClutchDetector(require_stable_frames=require_stable_frames)

    # Initialize Gemini gesture detector
    try:
        gesture_detector = GeminiGestureDetector(
            model_name=gemini_model,
            sample_interval=gemini_sample_interval,
            stability_frames=gemini_stability_frames,
            cooldown_ms=cooldown_ms,
            resize_width=gemini_resize_width
        )
        logger.info("Gemini gesture detector initialized")
    except ValueError as e:
        logger.error(f"Failed to initialize Gemini: {e}")
        logger.error("Make sure GEMINI_API_KEY environment variable is set")
        return

    action_handler = ActionHandler()
    window_manager = WindowManager()
    visual_feedback = VisualFeedback(
        clutch_engaged_color=clutch_engaged_color,
        clutch_disengaged_color=clutch_disengaged_color
    )

    # Initialize webcam
    cap = cv2.VideoCapture(0)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, camera_width)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, camera_height)
    cap.set(cv2.CAP_PROP_FPS, camera_fps)

    if not cap.isOpened():
        logger.error("Failed to open webcam")
        return

    logger.info("System initialized. Press 'q' to quit, 'h' to toggle hints.")
    logger.info("LEFT HAND: Close fist to ENGAGE clutch")
    logger.info("RIGHT HAND: Make gestures when clutch is ENGAGED")

    show_hints = True
    action_feedback_text = None
    action_feedback_timer = 0
    previous_gesture = None  # Track previous gesture for push-to-talk

    try:
        while True:
            ret, frame = cap.read()
            if not ret:
                logger.error("Failed to read frame from webcam")
                break

            # Flip frame horizontally for mirror effect
            frame = cv2.flip(frame, 1)

            # Process frame with hand tracker
            processed_frame, hands_data = hand_tracker.process_frame(frame)

            # Get left and right hand data
            left_hand = hands_data.get('left')
            right_hand = hands_data.get('right')

            # Update clutch detector with left hand
            clutch_engaged = clutch_detector.update(left_hand)

            # Only process gestures if clutch is engaged
            triggered_gesture = None
            current_gesture = None
            if clutch_engaged:
                # Check if terminal is focused (if required)
                terminal_focused = not require_terminal_focus or window_manager.is_terminal_active()

                if not terminal_focused:
                    logger.info("🖥️  Terminal not focused - gestures disabled (set require_terminal_focus: false in config to disable this check)")
                else:
                    # Update Gemini gesture detector with full frame
                    # (Gemini needs the image, not just hand landmarks)
                    triggered_gesture = gesture_detector.update(frame)

                    # Get current gesture state (not just newly triggered)
                    current_gesture = gesture_detector.get_status()['current_gesture']

                    # Handle push-to-talk for open_palm gesture
                    if current_gesture == 'open_palm' and previous_gesture != 'open_palm':
                        # Open palm just started - begin recording
                        if action_handler.start_recording():
                            action_feedback_text = "Recording..."
                            action_feedback_timer = 9999  # Keep showing while recording
                    elif previous_gesture == 'open_palm' and current_gesture != 'open_palm':
                        # Open palm just ended - stop recording
                        action_handler.stop_recording()
                        action_feedback_text = None
                        action_feedback_timer = 0

                    # Execute action if non-voice gesture was triggered
                    if triggered_gesture and triggered_gesture != 'open_palm':
                        action_text = action_handler.execute_gesture_action(triggered_gesture)
                        if action_text:
                            action_feedback_text = action_text
                            action_feedback_timer = 60  # Show for 60 frames (~2 seconds at 30fps)
            else:
                # Reset gesture detector when clutch is disengaged
                gesture_detector.reset()
                # Stop recording if clutch is disengaged
                if action_handler.is_dictation_active():
                    action_handler.stop_recording()
                    action_feedback_text = None
                    action_feedback_timer = 0

            # Update previous gesture for next iteration
            previous_gesture = current_gesture

            # Process any transcribed text from the queue (streaming)
            action_handler.process_transcription_queue()

            # Reset hand detection if no hands found
            if left_hand is None:
                clutch_detector.reset()

            # Visual feedback
            if show_overlay:
                # Draw clutch border indicator
                visual_feedback.draw_clutch_indicator(processed_frame, clutch_engaged)

                # Draw status text
                status_gesture = gesture_detector.get_status()['current_gesture']
                visual_feedback.draw_status_text(
                    processed_frame,
                    clutch_engaged,
                    status_gesture
                )

                # Draw gesture hints
                visual_feedback.draw_gesture_hint(processed_frame, show_hints)

                # Draw action feedback
                if action_feedback_timer > 0:
                    visual_feedback.draw_action_feedback(
                        processed_frame,
                        action_feedback_text
                    )
                    action_feedback_timer -= 1
                else:
                    action_feedback_text = None

                # Draw dictation indicator
                visual_feedback.draw_dictation_indicator(
                    processed_frame,
                    action_handler.is_dictation_active()
                )

            # Display the frame
            cv2.imshow('IronCoder Gesture Control', processed_frame)

            # Handle keyboard input
            key = cv2.waitKey(1) & 0xFF
            if key == ord('q'):
                logger.info("Quit signal received")
                break
            elif key == ord('h'):
                show_hints = not show_hints
                logger.info(f"Hints {'enabled' if show_hints else 'disabled'}")

    except KeyboardInterrupt:
        logger.info("Interrupted by user")
    except Exception as e:
        logger.error(f"Error during execution: {e}", exc_info=True)
    finally:
        # Clean up
        action_handler.cleanup()
        cap.release()
        cv2.destroyAllWindows()
        hand_tracker.close()
        logger.info("=== Gesture control system stopped ===")


if __name__ == "__main__":
    main()
