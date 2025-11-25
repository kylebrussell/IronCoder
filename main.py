"""
IronCoder Gesture Control for Claude Code
Main entry point for the gesture control system.

Uses hybrid gesture detection: fast local detection with optional Gemini fallback.
"""
import cv2
import logging
from dotenv import load_dotenv
from src.hand_tracker import HandTracker
from src.clutch_detector import ClutchDetector
from src.hybrid_gesture_detector import HybridGestureDetector
from src.gemini_gesture_detector import GeminiGestureDetector
from src.action_handler import ActionHandler
from src.config_manager import ConfigManager
from src.utils.window_manager import WindowManager
from src.utils.visual_feedback import VisualFeedback
from src.utils.settings_ui import SettingsUI

# Load environment variables from .env.local
load_dotenv('.env.local')


def main():
    """Main entry point for the gesture control system."""
    # Set up logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    logger = logging.getLogger(__name__)

    # Load configuration using ConfigManager
    config_manager = ConfigManager()
    config = config_manager.config

    # Extract settings
    camera_width = config.get('settings', {}).get('camera_resolution', [640, 480])[0]
    camera_height = config.get('settings', {}).get('camera_resolution', [640, 480])[1]
    camera_fps = config.get('settings', {}).get('camera_fps', 20)
    confidence_threshold = config.get('settings', {}).get('confidence_threshold', 0.7)
    cooldown_ms = config.get('settings', {}).get('cooldown_ms', 500)
    require_terminal_focus = config.get('settings', {}).get('require_terminal_focus', False)
    require_stable_frames = config.get('clutch', {}).get('require_stable_frames', 5)
    show_overlay = config.get('visual_feedback', {}).get('show_overlay', True)

    # Gemini settings (for fallback)
    gemini_model = config.get('gemini', {}).get('model', 'gemini-2.5-flash')
    gemini_sample_interval = config.get('gemini', {}).get('sample_interval', 0.5)
    gemini_resize_width = config.get('gemini', {}).get('resize_width', 256)

    # Hybrid detection settings
    use_gemini_fallback = config.get('hybrid_detection', {}).get('use_gemini_fallback', False)
    gesture_config = config.get('hybrid_detection', {}).get('gestures', {})

    logger.info("=== IronCoder Gesture Control for Claude Code ===")
    logger.info(f"Camera: {camera_width}x{camera_height} @ {camera_fps}fps")
    logger.info(f"Confidence threshold: {confidence_threshold}")
    logger.info(f"Cooldown: {cooldown_ms}ms")
    logger.info(f"Require terminal focus: {require_terminal_focus}")
    logger.info(f"Clutch stable frames: {require_stable_frames}")
    logger.info(f"Hybrid detection with Gemini fallback: {use_gemini_fallback}")

    # Initialize components
    hand_tracker = HandTracker(
        max_num_hands=2,
        min_detection_confidence=confidence_threshold
    )
    clutch_detector = ClutchDetector(require_stable_frames=require_stable_frames)

    # Initialize Gemini detector for fallback (optional)
    gemini_fallback = None
    if use_gemini_fallback:
        try:
            gemini_fallback = GeminiGestureDetector(
                model_name=gemini_model,
                sample_interval=gemini_sample_interval,
                stability_frames=1,  # Single verification, no stability needed
                cooldown_ms=cooldown_ms,
                resize_width=gemini_resize_width
            )
            logger.info(f"Gemini fallback initialized (model: {gemini_model})")
        except ValueError as e:
            logger.warning(f"Gemini fallback unavailable: {e}")
            logger.info("Continuing with local-only detection")

    # Initialize hybrid gesture detector
    gesture_detector = HybridGestureDetector(
        gemini_detector=gemini_fallback,
        cooldown_ms=cooldown_ms,
        use_gemini_fallback=use_gemini_fallback and gemini_fallback is not None,
        gesture_config=gesture_config
    )
    logger.info("Hybrid gesture detector initialized (fast local + optional Gemini fallback)")

    # Initialize action handler with config manager
    action_handler = ActionHandler(config_manager=config_manager)
    window_manager = WindowManager()

    # Initialize visual feedback with config manager
    visual_feedback = VisualFeedback(config_manager=config_manager)

    # Initialize settings UI
    settings_ui = SettingsUI(config_manager)

    # Initialize webcam
    cap = cv2.VideoCapture(0)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, camera_width)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, camera_height)
    cap.set(cv2.CAP_PROP_FPS, camera_fps)

    if not cap.isOpened():
        logger.error("Failed to open webcam")
        return

    logger.info("System initialized. Press 'q' to quit, 'h' to toggle hints, 's' for settings.")
    logger.info("LEFT HAND: Close fist to ENGAGE clutch")
    logger.info("RIGHT HAND: Make gestures when clutch is ENGAGED")

    show_hints = True
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

            # Only process gestures if clutch is engaged and settings UI is not visible
            triggered_gesture = None
            current_gesture = None
            detection_source = None
            action_text = None
            action_gesture = None

            if clutch_engaged and not settings_ui.is_visible:
                # Check if terminal is focused (if required)
                terminal_focused = not require_terminal_focus or window_manager.is_terminal_active()

                if not terminal_focused:
                    logger.debug("Terminal not focused - gestures disabled")
                else:
                    # Update hybrid gesture detector with frame and right hand data
                    result = gesture_detector.update(frame, right_hand)

                    if result:
                        triggered_gesture, confidence, detection_source = result

                    # Get current gesture state (not just newly triggered)
                    current_gesture = gesture_detector.get_current_gesture()

                    # Handle push-to-talk for voice gestures
                    if action_handler.is_voice_gesture(current_gesture) and not action_handler.is_voice_gesture(previous_gesture):
                        # Voice gesture just started - begin recording
                        if action_handler.start_recording():
                            action_text = "Recording..."
                            action_gesture = current_gesture
                    elif action_handler.is_voice_gesture(previous_gesture) and not action_handler.is_voice_gesture(current_gesture):
                        # Voice gesture just ended - stop recording
                        action_handler.stop_recording()

                    # Execute action if non-voice gesture was triggered
                    if triggered_gesture and not action_handler.is_voice_gesture(triggered_gesture) and triggered_gesture != 'none':
                        result_text = action_handler.execute_gesture_action(triggered_gesture)
                        if result_text:
                            # Show source (local/gemini) in feedback
                            source_indicator = "fast" if detection_source == 'local' else "verified"
                            action_text = f"{result_text} ({source_indicator})"
                            action_gesture = triggered_gesture
            else:
                # Reset gesture detector when clutch is disengaged
                if not clutch_engaged:
                    gesture_detector.reset()
                # Stop recording if clutch is disengaged or settings visible
                if action_handler.is_dictation_active():
                    action_handler.stop_recording()

            # Update previous gesture for next iteration
            previous_gesture = current_gesture

            # Process any transcribed text from the queue (streaming)
            action_handler.process_transcription_queue()

            # Reset hand detection if no hands found
            if left_hand is None:
                clutch_detector.reset()

            # Visual feedback
            if show_overlay:
                # Get current gesture state
                status = gesture_detector.get_status()
                status_gesture = status.get('current_gesture')

                # Draw all visual feedback
                processed_frame = visual_feedback.draw_all(
                    processed_frame,
                    clutch_engaged=clutch_engaged,
                    current_gesture=status_gesture,
                    is_dictating=action_handler.is_dictation_active(),
                    show_hints=show_hints and not settings_ui.is_visible,
                    action_text=action_text,
                    action_gesture=action_gesture
                )

            # Draw settings UI if visible
            processed_frame = settings_ui.draw(processed_frame)

            # Display the frame
            cv2.imshow('IronCoder Gesture Control', processed_frame)

            # Handle keyboard input
            key = cv2.waitKey(1) & 0xFF

            # Route keyboard input through settings UI first
            if settings_ui.handle_key(key):
                continue

            # Main app key handling
            if key == ord('q'):
                logger.info("Quit signal received")
                break
            elif key == ord('h'):
                show_hints = not show_hints
                logger.info(f"Hints {'enabled' if show_hints else 'disabled'}")
            elif key == ord('s'):
                settings_ui.toggle_visibility()
                logger.info(f"Settings {'opened' if settings_ui.is_visible else 'closed'}")

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
