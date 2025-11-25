"""
Command gesture recognizer for right hand gestures.
Detects: open palm, peace sign, thumbs up, thumbs down, and pointing finger.
Supports both boolean detection and confidence scoring for hybrid detection.
"""
from typing import Dict, Optional, Deque, Tuple
from collections import deque
import logging
import time
import math


class CommandGestureRecognizer:
    """Recognizes command gestures from right hand."""

    # Gesture types
    GESTURE_NONE = "none"
    GESTURE_OPEN_PALM = "open_palm"
    GESTURE_PEACE_SIGN = "peace_sign"
    GESTURE_THUMBS_UP = "thumbs_up"
    GESTURE_THUMBS_DOWN = "thumbs_down"
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

    def is_thumb_extended_down(self, landmarks: list) -> bool:
        """
        Check if thumb is extended downward (for thumbs down gesture).
        Requires thumb to be clearly pointing down with significant extension.

        Args:
            landmarks: List of hand landmarks

        Returns:
            True if thumb is extended downward
        """
        thumb_tip = landmarks[4]  # THUMB_TIP
        thumb_ip = landmarks[3]   # THUMB_IP
        thumb_mcp = landmarks[2]  # THUMB_MCP
        wrist = landmarks[0]

        # Thumb must be pointing downward (tip lower than IP and MCP)
        pointing_down = thumb_tip['y'] > thumb_ip['y'] > thumb_mcp['y']

        # Thumb tip must be significantly below the wrist (actually extended down)
        # This prevents confusion with tucked thumbs
        thumb_below_wrist = thumb_tip['y'] > wrist['y']

        # Thumb must have significant vertical extension
        vertical_extension = thumb_tip['y'] - thumb_mcp['y']
        has_extension = vertical_extension > 0.05  # At least 5% of frame height

        return pointing_down and thumb_below_wrist and has_extension

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
        Detect peace sign gesture (index and middle fingers up in V-shape, others down).
        Requires clear V-shape separation between index and middle fingers.

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

        # Ring and pinky should NOT be extended - check they're clearly curled
        ring_tip = landmarks[16]
        ring_pip = landmarks[14]
        pinky_tip = landmarks[20]
        pinky_pip = landmarks[18]

        ring_curled = ring_tip['y'] > ring_pip['y']
        pinky_curled = pinky_tip['y'] > pinky_pip['y']

        # Thumb should be tucked in (not extended outward)
        thumb_tip = landmarks[4]
        thumb_ip = landmarks[3]
        thumb_tucked = thumb_tip['y'] >= thumb_ip['y']

        # Require V-shape: index and middle tips must be separated horizontally
        index_tip = landmarks[8]
        middle_tip = landmarks[12]
        v_separation = abs(index_tip['x'] - middle_tip['x'])
        has_v_shape = v_separation > 0.03  # At least 3% frame width apart

        return (index_extended and middle_extended and
                ring_curled and pinky_curled and thumb_tucked and has_v_shape)

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

    def detect_thumbs_down(self, hand_data: Optional[Dict]) -> bool:
        """
        Detect thumbs down gesture (thumb down, fist closed).

        Args:
            hand_data: Hand data from HandTracker

        Returns:
            True if thumbs down is detected
        """
        if hand_data is None:
            return False

        landmarks = hand_data['landmarks']

        # Thumb should be extended downward
        thumb_down = self.is_thumb_extended_down(landmarks)

        # All other fingers should be curled (not extended)
        index_extended = self.is_finger_extended(landmarks, 8, 6)
        middle_extended = self.is_finger_extended(landmarks, 12, 10)
        ring_extended = self.is_finger_extended(landmarks, 16, 14)
        pinky_extended = self.is_finger_extended(landmarks, 20, 18)

        fingers_curled = not (index_extended or middle_extended or ring_extended or pinky_extended)

        return thumb_down and fingers_curled

    def detect_pointing(self, hand_data: Optional[Dict]) -> bool:
        """
        Detect pointing gesture (only index finger extended, others clearly curled).
        Requires index to be significantly more extended than other fingers.

        Args:
            hand_data: Hand data from HandTracker

        Returns:
            True if pointing gesture is detected
        """
        if hand_data is None:
            return False

        landmarks = hand_data['landmarks']

        # Index finger should be clearly extended
        index_extended = self.is_finger_extended(landmarks, 8, 6, 5)

        # Other fingers must be clearly curled (tips below PIPs)
        middle_tip = landmarks[12]
        middle_pip = landmarks[10]
        ring_tip = landmarks[16]
        ring_pip = landmarks[14]
        pinky_tip = landmarks[20]
        pinky_pip = landmarks[18]

        middle_curled = middle_tip['y'] > middle_pip['y']
        ring_curled = ring_tip['y'] > ring_pip['y']
        pinky_curled = pinky_tip['y'] > pinky_pip['y']

        # Thumb should be tucked or neutral (not extended up)
        thumb_tip = landmarks[4]
        thumb_ip = landmarks[3]
        thumb_mcp = landmarks[2]
        thumb_not_up = thumb_tip['y'] >= thumb_ip['y'] or thumb_tip['y'] >= thumb_mcp['y']

        # Index tip must be significantly higher than middle tip (clear pointing)
        index_tip = landmarks[8]
        index_clearly_up = (middle_tip['y'] - index_tip['y']) > 0.05  # 5% frame height difference

        return (index_extended and middle_curled and ring_curled and
                pinky_curled and thumb_not_up and index_clearly_up)

    def recognize_gesture(self, hand_data: Optional[Dict]) -> str:
        """
        Recognize gesture from hand data.

        Priority order: pointing > peace_sign > thumbs_up > thumbs_down > open_palm

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

        if self.detect_thumbs_down(hand_data):
            return self.GESTURE_THUMBS_DOWN

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

    # ============================================================
    # Confidence Scoring Methods for Hybrid Detection
    # ============================================================

    def _calculate_fingertip_spread(self, landmarks: list) -> float:
        """Calculate the spread of non-thumb fingertips (normalized 0-1)."""
        tips = [landmarks[8], landmarks[12], landmarks[16], landmarks[20]]
        xs = [t['x'] for t in tips]
        ys = [t['y'] for t in tips]
        return math.sqrt((max(xs) - min(xs))**2 + (max(ys) - min(ys))**2)

    def _calculate_fingertip_height_variance(self, landmarks: list) -> float:
        """Calculate variance in fingertip y positions (lower = flatter palm)."""
        tips = [landmarks[8], landmarks[12], landmarks[16], landmarks[20]]
        ys = [t['y'] for t in tips]
        return max(ys) - min(ys)

    def _calculate_thumb_verticality(self, landmarks: list, direction: str = 'up') -> float:
        """
        Calculate how vertical the thumb is (0 = horizontal, 1 = vertical).

        Args:
            landmarks: Hand landmarks
            direction: 'up' or 'down'
        """
        thumb_tip = landmarks[4]
        thumb_mcp = landmarks[2]

        dx = abs(thumb_tip['x'] - thumb_mcp['x'])
        dy = abs(thumb_tip['y'] - thumb_mcp['y'])

        if dy == 0:
            return 0.0

        # Check direction is correct
        if direction == 'up' and thumb_tip['y'] >= thumb_mcp['y']:
            return 0.0
        if direction == 'down' and thumb_tip['y'] <= thumb_mcp['y']:
            return 0.0

        # Return how vertical (0 = horizontal, 1 = vertical)
        return 1.0 - min(dx / dy, 1.0)

    def open_palm_confidence(self, hand_data: Optional[Dict]) -> float:
        """
        Calculate confidence score for open palm gesture (0.0-1.0).

        Scoring:
        - Base 0.50: All 5 fingers extended
        - +0.15: Good finger spread (>0.15 normalized)
        - +0.15: Fingertips at similar height (palm facing camera)
        - +0.10: Thumb clearly extended outward
        """
        if hand_data is None:
            return 0.0

        landmarks = hand_data['landmarks']
        confidence = 0.0

        # Check all fingers extended
        index_ext = self.is_finger_extended(landmarks, 8, 6, 5)
        middle_ext = self.is_finger_extended(landmarks, 12, 10, 9)
        ring_ext = self.is_finger_extended(landmarks, 16, 14, 13)
        pinky_ext = self.is_finger_extended(landmarks, 20, 18, 17)

        thumb_tip = landmarks[4]
        thumb_mcp = landmarks[2]
        wrist = landmarks[0]
        thumb_ext = abs(thumb_tip['x'] - wrist['x']) > abs(thumb_mcp['x'] - wrist['x'])

        fingers_extended = [index_ext, middle_ext, ring_ext, pinky_ext, thumb_ext]

        # Base score: all fingers extended
        if all(fingers_extended):
            confidence = 0.50
        elif sum(fingers_extended) >= 4:
            confidence = 0.30
        else:
            return 0.0  # Not open palm

        # Bonus: good finger spread
        spread = self._calculate_fingertip_spread(landmarks)
        if spread > 0.20:
            confidence += 0.15
        elif spread > 0.12:
            confidence += 0.08

        # Bonus: fingertips at similar height (palm facing camera)
        height_var = self._calculate_fingertip_height_variance(landmarks)
        if height_var < 0.06:
            confidence += 0.15
        elif height_var < 0.12:
            confidence += 0.08

        # Bonus: thumb clearly extended
        thumb_spread = abs(thumb_tip['x'] - wrist['x']) - abs(thumb_mcp['x'] - wrist['x'])
        if thumb_spread > 0.08:
            confidence += 0.10
        elif thumb_spread > 0.04:
            confidence += 0.05

        return min(confidence, 1.0)

    def peace_sign_confidence(self, hand_data: Optional[Dict]) -> float:
        """
        Calculate confidence score for peace sign gesture (0.0-1.0).

        Scoring:
        - Base 0.50: Index and middle extended, ring and pinky curled, V-shape present
        - +0.15: Thumb clearly tucked
        - +0.15: Good V-shape angle between index and middle (15-60 degrees)
        - +0.10: Ring and pinky tightly curled
        """
        if hand_data is None:
            return 0.0

        landmarks = hand_data['landmarks']
        confidence = 0.0

        # Check finger states
        index_ext = self.is_finger_extended(landmarks, 8, 6, 5)
        middle_ext = self.is_finger_extended(landmarks, 12, 10, 9)

        # Ring and pinky must be curled
        ring_tip = landmarks[16]
        ring_pip = landmarks[14]
        pinky_tip = landmarks[20]
        pinky_pip = landmarks[18]
        ring_curled = ring_tip['y'] > ring_pip['y']
        pinky_curled = pinky_tip['y'] > pinky_pip['y']

        thumb_tip = landmarks[4]
        thumb_ip = landmarks[3]
        thumb_tucked = thumb_tip['y'] >= thumb_ip['y']

        # Must have V-shape separation
        index_tip = landmarks[8]
        middle_tip = landmarks[12]
        v_separation = abs(index_tip['x'] - middle_tip['x'])
        has_v_shape = v_separation > 0.03

        # Base score - requires V-shape now
        if index_ext and middle_ext and ring_curled and pinky_curled and has_v_shape:
            confidence = 0.50
        else:
            return 0.0

        # Bonus: thumb clearly tucked
        if thumb_tucked:
            confidence += 0.15

        # Bonus: V-shape angle
        idx_mcp = landmarks[5]

        v1 = (index_tip['x'] - idx_mcp['x'], index_tip['y'] - idx_mcp['y'])
        v2 = (middle_tip['x'] - idx_mcp['x'], middle_tip['y'] - idx_mcp['y'])

        mag1 = math.sqrt(v1[0]**2 + v1[1]**2)
        mag2 = math.sqrt(v2[0]**2 + v2[1]**2)

        if mag1 > 0 and mag2 > 0:
            dot = v1[0]*v2[0] + v1[1]*v2[1]
            cos_angle = max(-1, min(1, dot / (mag1 * mag2)))
            angle_deg = math.degrees(math.acos(cos_angle))

            if 15 <= angle_deg <= 60:
                confidence += 0.15
            elif 10 <= angle_deg <= 75:
                confidence += 0.08

        # Bonus: ring and pinky tightly curled
        ring_curl = ring_tip['y'] - ring_pip['y']
        pinky_curl = pinky_tip['y'] - pinky_pip['y']
        if ring_curl > 0.03 and pinky_curl > 0.03:
            confidence += 0.10

        return min(confidence, 1.0)

    def thumbs_up_confidence(self, hand_data: Optional[Dict]) -> float:
        """
        Calculate confidence score for thumbs up gesture (0.0-1.0).

        Scoring:
        - Base 0.50: Thumb extended up, all fingers curled
        - +0.20: Thumb is roughly vertical
        - +0.15: Tight fist (fingertips close together)
        """
        if hand_data is None:
            return 0.0

        landmarks = hand_data['landmarks']
        confidence = 0.0

        # Check thumb up and fingers curled
        thumb_up = self.is_thumb_extended_up(landmarks)
        index_ext = self.is_finger_extended(landmarks, 8, 6)
        middle_ext = self.is_finger_extended(landmarks, 12, 10)
        ring_ext = self.is_finger_extended(landmarks, 16, 14)
        pinky_ext = self.is_finger_extended(landmarks, 20, 18)

        fingers_curled = not (index_ext or middle_ext or ring_ext or pinky_ext)

        # Base score
        if thumb_up and fingers_curled:
            confidence = 0.50
        else:
            return 0.0

        # Bonus: thumb verticality
        verticality = self._calculate_thumb_verticality(landmarks, 'up')
        if verticality > 0.7:
            confidence += 0.20
        elif verticality > 0.5:
            confidence += 0.10

        # Bonus: tight fist
        spread = self._calculate_fingertip_spread(landmarks)
        if spread < 0.08:
            confidence += 0.15
        elif spread < 0.12:
            confidence += 0.08

        return min(confidence, 1.0)

    def thumbs_down_confidence(self, hand_data: Optional[Dict]) -> float:
        """
        Calculate confidence score for thumbs down gesture (0.0-1.0).

        Scoring:
        - Base 0.50: Thumb extended down, all fingers curled
        - +0.20: Thumb is roughly vertical (pointing down)
        - +0.15: Tight fist (fingertips close together)
        - +0.10: Thumb clearly below wrist level
        """
        if hand_data is None:
            return 0.0

        landmarks = hand_data['landmarks']
        confidence = 0.0

        # Check thumb down and fingers curled
        thumb_down = self.is_thumb_extended_down(landmarks)
        index_ext = self.is_finger_extended(landmarks, 8, 6)
        middle_ext = self.is_finger_extended(landmarks, 12, 10)
        ring_ext = self.is_finger_extended(landmarks, 16, 14)
        pinky_ext = self.is_finger_extended(landmarks, 20, 18)

        fingers_curled = not (index_ext or middle_ext or ring_ext or pinky_ext)

        # Base score - require both thumb down AND fingers curled
        if thumb_down and fingers_curled:
            confidence = 0.50
        else:
            return 0.0

        # Bonus: thumb verticality (pointing down)
        verticality = self._calculate_thumb_verticality(landmarks, 'down')
        if verticality > 0.7:
            confidence += 0.20
        elif verticality > 0.5:
            confidence += 0.10

        # Bonus: tight fist
        spread = self._calculate_fingertip_spread(landmarks)
        if spread < 0.08:
            confidence += 0.15
        elif spread < 0.12:
            confidence += 0.08

        # Bonus: thumb clearly below wrist (strong thumbs down)
        thumb_tip = landmarks[4]
        wrist = landmarks[0]
        thumb_below_wrist = thumb_tip['y'] - wrist['y']
        if thumb_below_wrist > 0.10:  # Significantly below
            confidence += 0.10
        elif thumb_below_wrist > 0.05:
            confidence += 0.05

        return min(confidence, 1.0)

    def pointing_confidence(self, hand_data: Optional[Dict]) -> float:
        """
        Calculate confidence score for pointing gesture (0.0-1.0).

        Scoring:
        - Base 0.50: Index extended, others clearly curled, index significantly higher
        - +0.15: Thumb tucked
        - +0.15: Index finger straight (high angle at PIP)
        - +0.10: Other fingers tightly curled
        """
        if hand_data is None:
            return 0.0

        landmarks = hand_data['landmarks']
        confidence = 0.0

        # Check index extended
        index_ext = self.is_finger_extended(landmarks, 8, 6, 5)

        # Other fingers must be clearly curled
        middle_tip = landmarks[12]
        middle_pip = landmarks[10]
        ring_tip = landmarks[16]
        ring_pip = landmarks[14]
        pinky_tip = landmarks[20]
        pinky_pip = landmarks[18]

        middle_curled = middle_tip['y'] > middle_pip['y']
        ring_curled = ring_tip['y'] > ring_pip['y']
        pinky_curled = pinky_tip['y'] > pinky_pip['y']

        thumb_tip = landmarks[4]
        thumb_ip = landmarks[3]
        thumb_mcp = landmarks[2]
        thumb_not_up = thumb_tip['y'] >= thumb_ip['y'] or thumb_tip['y'] >= thumb_mcp['y']

        # Index must be clearly higher than middle
        index_tip = landmarks[8]
        index_clearly_up = (middle_tip['y'] - index_tip['y']) > 0.05

        # Base score - stricter requirements
        if index_ext and middle_curled and ring_curled and pinky_curled and index_clearly_up:
            confidence = 0.50
        else:
            return 0.0

        # Bonus: thumb tucked/not pointing up
        if thumb_not_up:
            confidence += 0.15

        # Bonus: index finger straight (calculate angle at PIP)
        idx_pip = landmarks[6]
        idx_mcp = landmarks[5]

        v1 = (index_tip['x'] - idx_pip['x'], index_tip['y'] - idx_pip['y'])
        v2 = (idx_mcp['x'] - idx_pip['x'], idx_mcp['y'] - idx_pip['y'])

        mag1 = math.sqrt(v1[0]**2 + v1[1]**2)
        mag2 = math.sqrt(v2[0]**2 + v2[1]**2)

        if mag1 > 0 and mag2 > 0:
            dot = v1[0]*v2[0] + v1[1]*v2[1]
            cos_angle = max(-1, min(1, dot / (mag1 * mag2)))
            angle_deg = math.degrees(math.acos(cos_angle))

            if angle_deg > 160:
                confidence += 0.15
            elif angle_deg > 140:
                confidence += 0.08

        # Bonus: other fingers tightly curled
        middle_curl = middle_tip['y'] - middle_pip['y']
        ring_curl = ring_tip['y'] - ring_pip['y']
        pinky_curl = pinky_tip['y'] - pinky_pip['y']
        if middle_curl > 0.03 and ring_curl > 0.03 and pinky_curl > 0.03:
            confidence += 0.10

        return min(confidence, 1.0)

    def recognize_with_confidence(self, hand_data: Optional[Dict]) -> Tuple[str, float]:
        """
        Recognize gesture and return confidence score.

        Args:
            hand_data: Hand data from HandTracker

        Returns:
            Tuple of (gesture_name, confidence_score)
        """
        if hand_data is None:
            return (self.GESTURE_NONE, 0.0)

        # Calculate confidence for each gesture
        scores = {
            self.GESTURE_OPEN_PALM: self.open_palm_confidence(hand_data),
            self.GESTURE_PEACE_SIGN: self.peace_sign_confidence(hand_data),
            self.GESTURE_THUMBS_UP: self.thumbs_up_confidence(hand_data),
            self.GESTURE_THUMBS_DOWN: self.thumbs_down_confidence(hand_data),
            self.GESTURE_POINTING: self.pointing_confidence(hand_data),
        }

        # Find best match
        best_gesture = max(scores, key=scores.get)
        best_confidence = scores[best_gesture]

        if best_confidence < 0.40:  # Minimum threshold
            return (self.GESTURE_NONE, 0.0)

        return (best_gesture, best_confidence)
