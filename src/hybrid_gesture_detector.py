"""
Hybrid gesture detector combining fast local detection with optional Gemini fallback.

Detection flow:
1. Run geometric detection on every frame (instant, ~1ms)
2. Calculate confidence score based on landmark clarity
3. If confidence > threshold: trigger immediately (no Gemini needed)
4. If confidence is medium and Gemini enabled: verify with Gemini
5. If confidence < threshold: return none
"""

import time
import logging
from typing import Optional, Dict, Tuple
from collections import deque

from src.gesture_recognizer import CommandGestureRecognizer

logger = logging.getLogger(__name__)


class HybridGestureDetector:
    """
    Hybrid gesture detection using local geometric analysis with optional Gemini fallback.

    Prioritizes speed by using MediaPipe landmark-based detection first,
    only falling back to Gemini for low-confidence cases when enabled.
    """

    # Default thresholds
    DEFAULT_HIGH_CONFIDENCE = 0.80  # Skip Gemini entirely above this
    DEFAULT_MEDIUM_CONFIDENCE = 0.60  # Use Gemini verification between medium and high
    DEFAULT_LOW_CONFIDENCE = 0.40  # Below this, gesture not recognized

    # Per-gesture configuration (open_palm prioritized for push-to-talk)
    DEFAULT_GESTURE_CONFIG = {
        'open_palm': {
            'stability_frames': 2,  # Fastest - for push-to-talk
            'skip_gemini_above': 0.75,  # Lower threshold for speed
        },
        'peace_sign': {
            'stability_frames': 3,
            'skip_gemini_above': 0.80,
        },
        'thumbs_up': {
            'stability_frames': 3,
            'skip_gemini_above': 0.80,
        },
        'thumbs_down': {
            'stability_frames': 3,
            'skip_gemini_above': 0.80,
        },
        'pointing': {
            'stability_frames': 3,
            'skip_gemini_above': 0.80,
        },
    }

    def __init__(
        self,
        gemini_detector=None,
        cooldown_ms: int = 500,
        use_gemini_fallback: bool = True,
        gesture_config: Optional[Dict] = None,
    ):
        """
        Initialize hybrid gesture detector.

        Args:
            gemini_detector: Optional GeminiGestureDetector for fallback verification
            cooldown_ms: Cooldown between gesture triggers in milliseconds
            use_gemini_fallback: Whether to use Gemini for low-confidence cases
            gesture_config: Per-gesture configuration overrides
        """
        self.local_detector = CommandGestureRecognizer(
            confidence_frames=2,  # Minimal for speed
            cooldown_ms=cooldown_ms
        )
        self.gemini_detector = gemini_detector
        self.use_gemini_fallback = use_gemini_fallback
        self.cooldown_ms = cooldown_ms

        # Merge gesture config with defaults
        self.gesture_config = self.DEFAULT_GESTURE_CONFIG.copy()
        if gesture_config:
            for gesture, config in gesture_config.items():
                if gesture in self.gesture_config:
                    self.gesture_config[gesture].update(config)

        # Per-gesture history for stability checking
        self.gesture_histories: Dict[str, deque] = {}
        for gesture, config in self.gesture_config.items():
            max_frames = config.get('stability_frames', 3)
            self.gesture_histories[gesture] = deque(maxlen=max_frames)
        self.gesture_histories['none'] = deque(maxlen=3)

        # State tracking
        self.current_gesture: Optional[str] = None
        self.current_confidence: float = 0.0
        self.last_trigger_time: float = 0.0
        self.last_triggered_gesture: Optional[str] = None

        logger.info(
            f"HybridGestureDetector initialized (gemini_fallback={use_gemini_fallback})"
        )

    def update(
        self,
        frame,
        hand_data: Optional[Dict],
    ) -> Optional[Tuple[str, float, str]]:
        """
        Update gesture detection with new frame data.

        Args:
            frame: OpenCV frame (for potential Gemini fallback)
            hand_data: Hand data from HandTracker with 'landmarks' and 'confidence'

        Returns:
            Tuple of (gesture_name, confidence, source) if gesture triggered,
            None otherwise. Source is 'local' or 'gemini'.
        """
        if hand_data is None:
            self._clear_histories()
            return None

        # Step 1: Run local geometric detection (instant)
        gesture, confidence = self.local_detector.recognize_with_confidence(hand_data)

        # Apply hand tracking confidence as a multiplier
        hand_confidence = hand_data.get('confidence', 1.0)
        confidence = confidence * (0.9 + 0.1 * hand_confidence)

        # Step 2: Update gesture history
        self._update_history(gesture, confidence)

        # Step 3: Check for stable gesture
        stable_gesture, avg_confidence = self._get_stable_gesture()

        if stable_gesture and stable_gesture != 'none':
            config = self.gesture_config.get(stable_gesture, {})
            skip_threshold = config.get('skip_gemini_above', self.DEFAULT_HIGH_CONFIDENCE)

            # High confidence: trigger immediately without Gemini
            if avg_confidence >= skip_threshold:
                result = self._try_trigger(stable_gesture, avg_confidence, 'local')
                if result:
                    logger.info(
                        f"Local detection: {stable_gesture} "
                        f"(conf={avg_confidence:.2f}, threshold={skip_threshold:.2f})"
                    )
                return result

            # Medium confidence: optionally verify with Gemini
            elif (
                avg_confidence >= self.DEFAULT_MEDIUM_CONFIDENCE
                and self.use_gemini_fallback
                and self.gemini_detector is not None
            ):
                # Try Gemini verification
                if self._verify_with_gemini(frame, stable_gesture):
                    result = self._try_trigger(stable_gesture, avg_confidence, 'gemini')
                    if result:
                        logger.info(
                            f"Gemini verified: {stable_gesture} (conf={avg_confidence:.2f})"
                        )
                    return result
                else:
                    logger.debug(
                        f"Gemini rejected: {stable_gesture} (conf={avg_confidence:.2f})"
                    )

            # Medium confidence but no Gemini: trigger anyway (speed priority)
            elif avg_confidence >= self.DEFAULT_MEDIUM_CONFIDENCE:
                result = self._try_trigger(stable_gesture, avg_confidence, 'local')
                if result:
                    logger.info(
                        f"Local detection (no Gemini): {stable_gesture} "
                        f"(conf={avg_confidence:.2f})"
                    )
                return result

        # Update current state for status queries
        self.current_gesture = gesture if confidence >= self.DEFAULT_LOW_CONFIDENCE else 'none'
        self.current_confidence = confidence

        return None

    def _update_history(self, gesture: str, confidence: float):
        """Update gesture history for stability checking."""
        # Add to the appropriate gesture's history
        if gesture in self.gesture_histories:
            self.gesture_histories[gesture].append((gesture, confidence))

        # Clear other gesture histories when confident in a different gesture
        if confidence >= self.DEFAULT_MEDIUM_CONFIDENCE:
            for g in self.gesture_histories:
                if g != gesture:
                    self.gesture_histories[g].clear()

    def _get_stable_gesture(self) -> Tuple[Optional[str], float]:
        """
        Check if any gesture has been stable for required frames.

        Returns:
            Tuple of (gesture_name, average_confidence) or (None, 0.0)
        """
        for gesture, history in self.gesture_histories.items():
            if gesture == 'none':
                continue

            config = self.gesture_config.get(gesture, {})
            required_frames = config.get('stability_frames', 3)

            if len(history) >= required_frames:
                # Check all recent detections are this gesture
                if all(h[0] == gesture for h in history):
                    avg_conf = sum(h[1] for h in history) / len(history)
                    return (gesture, avg_conf)

        return (None, 0.0)

    def _try_trigger(
        self,
        gesture: str,
        confidence: float,
        source: str
    ) -> Optional[Tuple[str, float, str]]:
        """
        Try to trigger a gesture, checking cooldown.

        Returns:
            Tuple if triggered, None if on cooldown
        """
        current_time = time.time() * 1000  # ms

        # Check cooldown
        if current_time - self.last_trigger_time < self.cooldown_ms:
            return None

        # Check if same gesture as last triggered (require gesture to change)
        if gesture == self.last_triggered_gesture:
            return None

        # Trigger!
        self.last_trigger_time = current_time
        self.last_triggered_gesture = gesture
        self.current_gesture = gesture
        self.current_confidence = confidence

        return (gesture, confidence, source)

    def _verify_with_gemini(self, frame, suspected_gesture: str) -> bool:
        """
        Use Gemini to verify a suspected gesture.

        Args:
            frame: OpenCV frame
            suspected_gesture: What local detection thinks it is

        Returns:
            True if Gemini confirms the gesture
        """
        if self.gemini_detector is None:
            return False

        try:
            # Use quick verification if available
            if hasattr(self.gemini_detector, 'verify_gesture_quick'):
                return self.gemini_detector.verify_gesture_quick(
                    frame, suspected_gesture
                )

            # Fall back to standard detection
            result = self.gemini_detector.get_current_gesture()
            return result == suspected_gesture

        except Exception as e:
            logger.warning(f"Gemini verification failed: {e}")
            return False

    def _clear_histories(self):
        """Clear all gesture histories."""
        for history in self.gesture_histories.values():
            history.clear()

    def reset(self):
        """Reset detector state."""
        self._clear_histories()
        self.current_gesture = None
        self.current_confidence = 0.0
        self.last_triggered_gesture = None
        self.local_detector.reset()
        logger.debug("HybridGestureDetector reset")

    def get_current_gesture(self) -> Optional[str]:
        """Get the current detected gesture (may not be triggered yet)."""
        return self.current_gesture

    def get_status(self) -> Dict:
        """Get current detector status."""
        return {
            'current_gesture': self.current_gesture,
            'current_confidence': self.current_confidence,
            'last_triggered': self.last_triggered_gesture,
            'use_gemini_fallback': self.use_gemini_fallback,
            'gesture_histories': {
                g: [(h[0], round(h[1], 2)) for h in hist]
                for g, hist in self.gesture_histories.items()
                if len(hist) > 0
            }
        }

    def set_gemini_fallback(self, enabled: bool):
        """Enable or disable Gemini fallback at runtime."""
        self.use_gemini_fallback = enabled
        logger.info(f"Gemini fallback {'enabled' if enabled else 'disabled'}")
