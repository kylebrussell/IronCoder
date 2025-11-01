"""
Clutch detector for left hand fist detection.
Uses frame-based smoothing to prevent false positives.
"""
from typing import Dict, Optional, Deque
from collections import deque
import logging


class ClutchDetector:
    """Detects closed fist gesture for clutch engagement."""

    def __init__(self, require_stable_frames: int = 5):
        """
        Initialize clutch detector.

        Args:
            require_stable_frames: Number of consecutive frames required for stable detection
        """
        self.require_stable_frames = require_stable_frames
        self.detection_history: Deque[bool] = deque(maxlen=require_stable_frames)
        self.is_engaged = False
        self.logger = logging.getLogger(__name__)

    def is_fist_closed(self, hand_data: Optional[Dict]) -> bool:
        """
        Check if hand is making a closed fist gesture.

        A closed fist is detected when:
        - All fingertips are below their respective PIP joints
        - Thumb is tucked in (thumb tip close to index finger MCP)

        Args:
            hand_data: Hand data from HandTracker

        Returns:
            True if fist is closed, False otherwise
        """
        if hand_data is None:
            return False

        landmarks = hand_data['landmarks']

        # Check if all fingers are curled (fingertips below PIP joints)
        fingers_curled = []

        # Index finger
        fingers_curled.append(
            landmarks[8]['y'] > landmarks[6]['y']  # INDEX_TIP > INDEX_PIP
        )

        # Middle finger
        fingers_curled.append(
            landmarks[12]['y'] > landmarks[10]['y']  # MIDDLE_TIP > MIDDLE_PIP
        )

        # Ring finger
        fingers_curled.append(
            landmarks[16]['y'] > landmarks[14]['y']  # RING_TIP > RING_PIP
        )

        # Pinky finger
        fingers_curled.append(
            landmarks[20]['y'] > landmarks[18]['y']  # PINKY_TIP > PINKY_PIP
        )

        # Check if thumb is tucked in
        # Thumb tip should be close to or below thumb IP joint
        thumb_tucked = landmarks[4]['y'] > landmarks[3]['y']  # THUMB_TIP > THUMB_IP

        # Fist is closed if all fingers are curled and thumb is tucked
        return all(fingers_curled) and thumb_tucked

    def update(self, hand_data: Optional[Dict]) -> bool:
        """
        Update clutch state with new hand data.

        Uses frame history for smoothing to prevent jitter.

        Args:
            hand_data: Hand data from HandTracker

        Returns:
            True if clutch is engaged, False otherwise
        """
        # Check if fist is currently closed
        fist_closed = self.is_fist_closed(hand_data)

        # Add to history
        self.detection_history.append(fist_closed)

        # Require stable detection over multiple frames
        if len(self.detection_history) == self.require_stable_frames:
            # Clutch is engaged if fist was closed in all recent frames
            was_engaged = self.is_engaged
            self.is_engaged = all(self.detection_history)

            # Log state changes
            if self.is_engaged and not was_engaged:
                self.logger.info("Clutch ENGAGED")
            elif not self.is_engaged and was_engaged:
                self.logger.info("Clutch DISENGAGED")

        return self.is_engaged

    def reset(self):
        """Reset clutch state and history."""
        self.detection_history.clear()
        self.is_engaged = False
        self.logger.debug("Clutch state reset")

    def get_status(self) -> Dict[str, any]:
        """
        Get current clutch status.

        Returns:
            Dict with 'engaged' status and 'stability' (0.0-1.0)
        """
        stability = 0.0
        if len(self.detection_history) > 0:
            stability = sum(self.detection_history) / len(self.detection_history)

        return {
            'engaged': self.is_engaged,
            'stability': stability,
            'frames_tracked': len(self.detection_history)
        }
