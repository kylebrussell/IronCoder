"""
Command gesture recognizer for right hand gestures.
Detects: open palm, peace sign, thumbs up, and pointing finger.
"""
from typing import Dict, Optional, Deque
from collections import deque
import logging
import time


class CommandGestureRecognizer:
    """Recognizes command gestures from right hand."""

    # Gesture types
    GESTURE_NONE = "none"
    GESTURE_OPEN_PALM = "open_palm"
    GESTURE_PEACE_SIGN = "peace_sign"
    GESTURE_THUMBS_UP = "thumbs_up"
    GESTURE_POINTING = "pointing"

    def __init__(
        self,
        confidence_frames: int = 3,
        cooldown_ms: int = 500
    ):
        """
        Initialize gesture recognizer.

        Args:
            confidence_frames: Number of consecutive frames required for gesture detection
            cooldown_ms: Cooldown period in milliseconds between gesture triggers
        """
        self.confidence_frames = confidence_frames
        self.cooldown_ms = cooldown_ms
        self.gesture_history: Deque[str] = deque(maxlen=confidence_frames)
        self.current_gesture = self.GESTURE_NONE
        self.last_triggered_gesture = None
        self.last_trigger_time = 0
        self.logger = logging.getLogger(__name__)

    def is_finger_extended(
        self,
        landmarks: list,
        tip_id: int,
        pip_id: int,
        mcp_id: int = None
    ) -> bool:
        """
        Check if a finger is extended.

        Args:
            landmarks: List of hand landmarks
            tip_id: Fingertip landmark ID
            pip_id: PIP joint landmark ID
            mcp_id: Optional MCP joint landmark ID for more accurate detection

        Returns:
            True if finger is extended
        """
        tip = landmarks[tip_id]
        pip = landmarks[pip_id]

        # Basic check: tip should be higher (smaller y value) than PIP
        is_extended = tip['y'] < pip['y']

        # Additional check if MCP is provided
        if mcp_id is not None:
            mcp = landmarks[mcp_id]
            # Tip should also be higher than MCP for a fully extended finger
            is_extended = is_extended and (tip['y'] < mcp['y'])

        return is_extended

    def is_thumb_extended_up(self, landmarks: list) -> bool:
        """
        Check if thumb is extended upward (for thumbs up gesture).

        Args:
            landmarks: List of hand landmarks

        Returns:
            True if thumb is extended upward
        """
        thumb_tip = landmarks[4]  # THUMB_TIP
        thumb_ip = landmarks[3]   # THUMB_IP
        thumb_mcp = landmarks[2]  # THUMB_MCP

        # Thumb is extended if tip is higher than IP and MCP
        return thumb_tip['y'] < thumb_ip['y'] < thumb_mcp['y']

    def detect_open_palm(self, hand_data: Optional[Dict]) -> bool:
        """
        Detect open palm gesture (all 5 fingers extended).

        Args:
            hand_data: Hand data from HandTracker

        Returns:
            True if open palm is detected
        """
        if hand_data is None:
            return False

        landmarks = hand_data['landmarks']

        # Check if all 5 fingers are extended
        index_extended = self.is_finger_extended(landmarks, 8, 6, 5)
        middle_extended = self.is_finger_extended(landmarks, 12, 10, 9)
        ring_extended = self.is_finger_extended(landmarks, 16, 14, 13)
        pinky_extended = self.is_finger_extended(landmarks, 20, 18, 17)

        # For thumb, check if it's extended outward
        thumb_tip = landmarks[4]
        thumb_mcp = landmarks[2]
        wrist = landmarks[0]

        # Thumb is extended if tip is farther from wrist than MCP
        thumb_extended = abs(thumb_tip['x'] - wrist['x']) > abs(thumb_mcp['x'] - wrist['x'])

        return all([index_extended, middle_extended, ring_extended, pinky_extended, thumb_extended])

    def detect_peace_sign(self, hand_data: Optional[Dict]) -> bool:
        """
        Detect peace sign gesture (index and middle fingers up, others down).

        Args:
            hand_data: Hand data from HandTracker

        Returns:
            True if peace sign is detected
        """
        if hand_data is None:
            return False

        landmarks = hand_data['landmarks']

        # Index and middle fingers should be extended
        index_extended = self.is_finger_extended(landmarks, 8, 6, 5)
        middle_extended = self.is_finger_extended(landmarks, 12, 10, 9)

        # Ring and pinky should NOT be extended
        ring_extended = self.is_finger_extended(landmarks, 16, 14, 13)
        pinky_extended = self.is_finger_extended(landmarks, 20, 18, 17)

        # Thumb should be tucked in
        thumb_tip = landmarks[4]
        thumb_ip = landmarks[3]
        thumb_tucked = thumb_tip['y'] >= thumb_ip['y']

        return (index_extended and middle_extended and
                not ring_extended and not pinky_extended and thumb_tucked)

    def detect_thumbs_up(self, hand_data: Optional[Dict]) -> bool:
        """
        Detect thumbs up gesture (thumb up, fist closed).

        Args:
            hand_data: Hand data from HandTracker

        Returns:
            True if thumbs up is detected
        """
        if hand_data is None:
            return False

        landmarks = hand_data['landmarks']

        # Thumb should be extended upward
        thumb_up = self.is_thumb_extended_up(landmarks)

        # All other fingers should be curled (not extended)
        index_extended = self.is_finger_extended(landmarks, 8, 6)
        middle_extended = self.is_finger_extended(landmarks, 12, 10)
        ring_extended = self.is_finger_extended(landmarks, 16, 14)
        pinky_extended = self.is_finger_extended(landmarks, 20, 18)

        fingers_curled = not (index_extended or middle_extended or ring_extended or pinky_extended)

        return thumb_up and fingers_curled

    def detect_pointing(self, hand_data: Optional[Dict]) -> bool:
        """
        Detect pointing gesture (only index finger extended).

        Args:
            hand_data: Hand data from HandTracker

        Returns:
            True if pointing gesture is detected
        """
        if hand_data is None:
            return False

        landmarks = hand_data['landmarks']

        # Only index finger should be extended
        index_extended = self.is_finger_extended(landmarks, 8, 6, 5)

        # All other fingers should NOT be extended
        middle_extended = self.is_finger_extended(landmarks, 12, 10)
        ring_extended = self.is_finger_extended(landmarks, 16, 14)
        pinky_extended = self.is_finger_extended(landmarks, 20, 18)

        # Thumb should be tucked
        thumb_tip = landmarks[4]
        thumb_ip = landmarks[3]
        thumb_tucked = thumb_tip['y'] >= thumb_ip['y']

        return (index_extended and not middle_extended and
                not ring_extended and not pinky_extended and thumb_tucked)

    def recognize_gesture(self, hand_data: Optional[Dict]) -> str:
        """
        Recognize gesture from hand data.

        Priority order: pointing > peace_sign > thumbs_up > open_palm

        Args:
            hand_data: Hand data from HandTracker

        Returns:
            Gesture name or GESTURE_NONE
        """
        if hand_data is None:
            return self.GESTURE_NONE

        # Check gestures in priority order
        # (more specific gestures first to avoid false positives)
        if self.detect_pointing(hand_data):
            return self.GESTURE_POINTING

        if self.detect_peace_sign(hand_data):
            return self.GESTURE_PEACE_SIGN

        if self.detect_thumbs_up(hand_data):
            return self.GESTURE_THUMBS_UP

        if self.detect_open_palm(hand_data):
            return self.GESTURE_OPEN_PALM

        return self.GESTURE_NONE

    def update(self, hand_data: Optional[Dict]) -> Optional[str]:
        """
        Update gesture recognition with new hand data.

        Uses frame history for smoothing and cooldown for debouncing.

        Args:
            hand_data: Hand data from HandTracker

        Returns:
            Gesture name if a stable gesture is detected and cooldown period has passed,
            None otherwise
        """
        # Recognize current gesture
        detected_gesture = self.recognize_gesture(hand_data)

        # Add to history
        self.gesture_history.append(detected_gesture)

        # Check if we have enough frames for confidence
        if len(self.gesture_history) < self.confidence_frames:
            return None

        # Check if gesture is stable (same gesture in all recent frames)
        if len(set(self.gesture_history)) == 1:
            stable_gesture = self.gesture_history[0]

            # Update current gesture
            self.current_gesture = stable_gesture

            # Check if this is a new gesture (not NONE) and cooldown has passed
            current_time = time.time() * 1000  # Convert to milliseconds
            cooldown_passed = (current_time - self.last_trigger_time) >= self.cooldown_ms

            if (stable_gesture != self.GESTURE_NONE and
                stable_gesture != self.last_triggered_gesture and
                cooldown_passed):

                # Trigger the gesture
                self.last_triggered_gesture = stable_gesture
                self.last_trigger_time = current_time
                self.logger.info(f"Gesture triggered: {stable_gesture}")
                return stable_gesture

        return None

    def reset(self):
        """Reset gesture recognition state."""
        self.gesture_history.clear()
        self.current_gesture = self.GESTURE_NONE
        self.last_triggered_gesture = None
        self.logger.debug("Gesture recognizer state reset")

    def get_status(self) -> Dict[str, any]:
        """
        Get current gesture recognition status.

        Returns:
            Dict with current gesture and history
        """
        return {
            'current_gesture': self.current_gesture,
            'last_triggered': self.last_triggered_gesture,
            'history': list(self.gesture_history),
            'frames_tracked': len(self.gesture_history)
        }
