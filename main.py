"""
IronCoder Gesture Control for Claude Code
Main entry point for the gesture control system.
"""
import cv2
import yaml
import logging
from src.hand_tracker import HandTracker
from src.clutch_detector import ClutchDetector
from src.gesture_recognizer import CommandGestureRecognizer
from src.action_handler import ActionHandler
from src.utils.window_manager import WindowManager
from src.utils.visual_feedback import VisualFeedback


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

    # Get visual feedback colors
    clutch_engaged_color = tuple(config.get('visual_feedback', {}).get('clutch_indicator_color', [0, 255, 0]))
    clutch_disengaged_color = tuple(config.get('visual_feedback', {}).get('clutch_disengaged_color', [255, 0, 0]))

    logger.info("=== IronCoder Gesture Control for Claude Code ===")
    logger.info(f"Camera: {camera_width}x{camera_height} @ {camera_fps}fps")
    logger.info(f"Confidence threshold: {confidence_threshold}")
    logger.info(f"Cooldown: {cooldown_ms}ms")
    logger.info(f"Require terminal focus: {require_terminal_focus}")
    logger.info(f"Clutch stable frames: {require_stable_frames}")

    # Initialize components
    hand_tracker = HandTracker(
        max_num_hands=2,
        min_detection_confidence=confidence_threshold
    )
    clutch_detector = ClutchDetector(require_stable_frames=require_stable_frames)
    gesture_recognizer = CommandGestureRecognizer(
        confidence_frames=require_stable_frames,
        cooldown_ms=cooldown_ms
    )
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
            if clutch_engaged:
                # Check if terminal is focused (if required)
                terminal_focused = not require_terminal_focus or window_manager.is_terminal_active()

                if terminal_focused:
                    # Update gesture recognizer with right hand
                    triggered_gesture = gesture_recognizer.update(right_hand)

                    # Execute action if gesture was triggered
                    if triggered_gesture:
                        action_text = action_handler.execute_gesture_action(triggered_gesture)
                        if action_text:
                            action_feedback_text = action_text
                            action_feedback_timer = 60  # Show for 60 frames (~2 seconds at 30fps)
                else:
                    logger.debug("Terminal not focused - gestures disabled")
            else:
                # Reset gesture recognizer when clutch is disengaged
                gesture_recognizer.reset()

            # Reset hand detection if no hands found
            if left_hand is None:
                clutch_detector.reset()

            # Visual feedback
            if show_overlay:
                # Draw clutch border indicator
                visual_feedback.draw_clutch_indicator(processed_frame, clutch_engaged)

                # Draw status text
                current_gesture = gesture_recognizer.get_status()['current_gesture']
                visual_feedback.draw_status_text(
                    processed_frame,
                    clutch_engaged,
                    current_gesture
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
        cap.release()
        cv2.destroyAllWindows()
        hand_tracker.close()
        logger.info("=== Gesture control system stopped ===")


if __name__ == "__main__":
    main()
