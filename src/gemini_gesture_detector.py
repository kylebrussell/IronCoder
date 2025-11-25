"""
Gemini-powered gesture detection using vision API.
Sends frames to Google Gemini for natural language-based gesture recognition.
"""

import threading
import time
import logging
import os
import cv2
import numpy as np
from typing import Optional, Dict
from google import genai
from google.genai import types

logger = logging.getLogger(__name__)


class GeminiGestureDetector:
    """
    Detects gestures using Google Gemini's vision capabilities.
    More flexible and reliable than landmark-based detection.
    """

    # Supported gestures and their descriptions
    GESTURES = {
        'open_palm': 'All 5 fingers extended, palm facing forward',
        'peace_sign': 'Index and middle finger extended in V-shape, other fingers closed',
        'thumbs_up': 'Thumb pointing up, other fingers closed in fist',
        'thumbs_down': 'Thumb pointing down, other fingers closed in fist',
        'pointing': 'Index finger extended pointing forward, other fingers closed',
        'none': 'No recognizable gesture or hand not visible'
    }

    def __init__(
        self,
        api_key: Optional[str] = None,
        model_name: str = "gemini-2.5-flash",
        sample_interval: float = 0.5,
        stability_frames: int = 2,
        cooldown_ms: int = 500,
        resize_width: int = 512
    ):
        """
        Initialize Gemini gesture detector.

        Args:
            api_key: Gemini API key (if None, reads from GEMINI_API_KEY env var)
            model_name: Gemini model to use (gemini-2.5-flash recommended)
            sample_interval: How often to sample frames in seconds (default 0.5s)
            stability_frames: Require N consecutive detections before confirming gesture
            cooldown_ms: Cooldown period between gesture triggers in milliseconds
            resize_width: Resize frame width before sending to API (saves tokens)
        """
        # Get API key
        self.api_key = api_key or os.getenv('GEMINI_API_KEY')
        if not self.api_key:
            raise ValueError(
                "Gemini API key not provided. Set GEMINI_API_KEY environment variable "
                "or pass api_key parameter."
            )

        self.model_name = model_name
        self.sample_interval = sample_interval
        self.stability_frames = stability_frames
        self.cooldown_ms = cooldown_ms
        self.resize_width = resize_width

        # Initialize Gemini client
        try:
            self.client = genai.Client(api_key=self.api_key)
            logger.info(f"Gemini client initialized with model: {model_name}")
        except Exception as e:
            logger.error(f"Failed to initialize Gemini client: {e}")
            raise

        # State tracking
        self.current_gesture: Optional[str] = None
        self.gesture_history = []  # For stability checking
        self.last_sample_time = 0.0
        self.last_trigger_time = 0.0
        self.is_processing = False
        self.processing_lock = threading.Lock()

        # Build the prompt
        self.prompt = self._build_prompt()

    def _build_prompt(self) -> str:
        """Build the gesture detection prompt for Gemini."""
        gesture_list = "\n".join([
            f"- {name}: {desc}"
            for name, desc in self.GESTURES.items()
        ])

        return f"""You are a gesture recognition system. Analyze the RIGHT HAND in this image.

Identify which gesture the right hand is making from this list:
{gesture_list}

IMPORTANT RULES:
- Focus ONLY on the RIGHT HAND (ignore left hand)
- The gesture must be clear and confident
- If unsure or hand is ambiguous, respond with "none"
- Respond with ONLY the gesture name in lowercase
- Do not include explanations, just the gesture name

Gesture:"""

    def _resize_frame(self, frame: np.ndarray) -> np.ndarray:
        """Resize frame to reduce API costs while maintaining aspect ratio."""
        height, width = frame.shape[:2]
        if width <= self.resize_width:
            return frame

        # Calculate new height maintaining aspect ratio
        ratio = self.resize_width / width
        new_height = int(height * ratio)

        return cv2.resize(frame, (self.resize_width, new_height), interpolation=cv2.INTER_AREA)

    def _frame_to_jpeg_bytes(self, frame: np.ndarray) -> bytes:
        """Convert OpenCV frame to JPEG bytes."""
        # Resize to save tokens/costs
        resized = self._resize_frame(frame)

        # Encode as JPEG
        success, buffer = cv2.imencode('.jpg', resized, [cv2.IMWRITE_JPEG_QUALITY, 85])
        if not success:
            raise ValueError("Failed to encode frame as JPEG")

        return buffer.tobytes()

    def _detect_gesture_sync(self, frame: np.ndarray) -> Optional[str]:
        """
        Synchronously detect gesture in frame using Gemini API.
        This is called from a background thread.
        """
        try:
            # Convert frame to JPEG bytes
            jpeg_bytes = self._frame_to_jpeg_bytes(frame)
            logger.info(f"📡 Sending frame to Gemini API ({self.model_name})...")

            # Create the request
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=[
                    types.Part.from_bytes(
                        data=jpeg_bytes,
                        mime_type='image/jpeg'
                    ),
                    self.prompt
                ]
            )

            # Parse response
            gesture_name = response.text.strip().lower()
            logger.info(f"✅ Gemini response received: '{gesture_name}'")

            # Validate response
            if gesture_name in self.GESTURES:
                logger.info(f"🎯 Valid gesture detected: {gesture_name}")
                return gesture_name
            else:
                logger.warning(f"⚠️  Gemini returned invalid gesture: '{gesture_name}' (expected one of {list(self.GESTURES.keys())})")
                return 'none'

        except Exception as e:
            logger.error(f"❌ Error detecting gesture with Gemini: {e}")
            return 'none'

    def _process_frame_async(self, frame: np.ndarray):
        """Process frame in background thread to avoid blocking main loop."""
        with self.processing_lock:
            if self.is_processing:
                logger.debug("Already processing frame, skipping")
                return

            self.is_processing = True

        try:
            # Detect gesture
            detected_gesture = self._detect_gesture_sync(frame)

            # Update gesture history for stability
            self.gesture_history.append(detected_gesture)
            if len(self.gesture_history) > self.stability_frames:
                self.gesture_history.pop(0)

            # Check if gesture is stable (same for N frames)
            if len(self.gesture_history) == self.stability_frames:
                if all(g == detected_gesture for g in self.gesture_history):
                    self.current_gesture = detected_gesture
                else:
                    # Mixed detections, keep previous gesture
                    logger.debug(f"Unstable gesture detection: {self.gesture_history}")

        finally:
            with self.processing_lock:
                self.is_processing = False

    def update(self, frame: Optional[np.ndarray]) -> Optional[str]:
        """
        Update gesture detector with new frame.
        Returns gesture name if a new gesture was just triggered, None otherwise.

        Args:
            frame: OpenCV frame (BGR format) or None if no frame available

        Returns:
            Gesture name if newly triggered, None otherwise
        """
        if frame is None:
            self.reset()
            return None

        current_time = time.time()

        # Check if enough time has passed since last sample
        if current_time - self.last_sample_time < self.sample_interval:
            return None

        # Check if we're still processing previous frame
        with self.processing_lock:
            if self.is_processing:
                logger.debug("⏳ Still processing previous frame, skipping...")
                return None

        # Update sample time
        self.last_sample_time = current_time

        logger.info(f"⏰ Sample interval reached ({self.sample_interval}s) - starting gesture detection...")

        # Process frame in background thread (non-blocking)
        thread = threading.Thread(
            target=self._process_frame_async,
            args=(frame.copy(),),
            daemon=True
        )
        thread.start()
        logger.debug("🔄 Background processing thread started")

        # Check if current gesture should trigger an action
        if self.current_gesture and self.current_gesture != 'none':
            # Check cooldown
            if (current_time - self.last_trigger_time) * 1000 >= self.cooldown_ms:
                self.last_trigger_time = current_time
                logger.info(f"Triggered gesture: {self.current_gesture}")
                return self.current_gesture

        return None

    def get_status(self) -> Dict[str, any]:
        """
        Get current detector status.

        Returns:
            Dictionary with current_gesture, is_processing, gesture_history
        """
        return {
            'current_gesture': self.current_gesture,
            'is_processing': self.is_processing,
            'gesture_history': self.gesture_history.copy()
        }

    def reset(self):
        """Reset detector state."""
        self.current_gesture = None
        self.gesture_history = []
        logger.debug("Gesture detector reset")

    def get_current_gesture(self) -> Optional[str]:
        """Get the current detected gesture."""
        return self.current_gesture

    # ============================================================
    # Quick Verification Methods for Hybrid Detection Fallback
    # ============================================================

    def _crop_hand_region(
        self,
        frame: np.ndarray,
        landmarks: list,
        padding: float = 0.2
    ) -> np.ndarray:
        """
        Crop frame to just the hand region for faster/cheaper API calls.

        Args:
            frame: Full OpenCV frame
            landmarks: List of hand landmark dicts with 'x', 'y' keys (normalized 0-1)
            padding: Padding around hand region as fraction of frame size

        Returns:
            Cropped frame containing just the hand
        """
        h, w = frame.shape[:2]

        # Get bounding box from landmarks
        xs = [l['x'] for l in landmarks]
        ys = [l['y'] for l in landmarks]

        # Convert to pixel coordinates with padding
        pad_w = int(padding * w)
        pad_h = int(padding * h)

        x_min = int(max(0, min(xs) * w - pad_w))
        x_max = int(min(w, max(xs) * w + pad_w))
        y_min = int(max(0, min(ys) * h - pad_h))
        y_max = int(min(h, max(ys) * h + pad_h))

        # Ensure we have a valid region
        if x_max <= x_min or y_max <= y_min:
            return frame

        return frame[y_min:y_max, x_min:x_max]

    def _resize_to_max_dim(self, frame: np.ndarray, max_dim: int = 256) -> np.ndarray:
        """
        Resize frame so largest dimension is max_dim.
        Smaller images = faster API calls.

        Args:
            frame: OpenCV frame
            max_dim: Maximum dimension in pixels

        Returns:
            Resized frame
        """
        h, w = frame.shape[:2]
        if max(h, w) <= max_dim:
            return frame

        if w > h:
            new_w = max_dim
            new_h = int(h * max_dim / w)
        else:
            new_h = max_dim
            new_w = int(w * max_dim / h)

        return cv2.resize(frame, (new_w, new_h), interpolation=cv2.INTER_AREA)

    def verify_gesture_quick(
        self,
        frame: np.ndarray,
        suspected_gesture: str,
        landmarks: Optional[list] = None
    ) -> bool:
        """
        Quick verification of a suspected gesture.
        Uses smaller image and simpler prompt for faster response.

        Args:
            frame: Current video frame
            suspected_gesture: What local detection thinks it is
            landmarks: Optional hand landmarks for cropping

        Returns:
            True if Gemini confirms the gesture
        """
        try:
            # Crop to hand region if landmarks provided (much smaller image)
            if landmarks:
                frame = self._crop_hand_region(frame, landmarks)

            # Resize to small dimension for speed
            small = self._resize_to_max_dim(frame, 256)

            # Encode as JPEG with lower quality for speed
            success, buffer = cv2.imencode('.jpg', small, [cv2.IMWRITE_JPEG_QUALITY, 70])
            if not success:
                return False
            jpeg_bytes = buffer.tobytes()

            # Simple yes/no verification prompt
            gesture_desc = self.GESTURES.get(suspected_gesture, suspected_gesture)
            verify_prompt = (
                f"Is the right hand making a {suspected_gesture.replace('_', ' ')} gesture "
                f"({gesture_desc})? Answer ONLY 'yes' or 'no'."
            )

            logger.debug(f"Quick verify: {suspected_gesture}")

            response = self.client.models.generate_content(
                model=self.model_name,
                contents=[
                    types.Part.from_bytes(data=jpeg_bytes, mime_type='image/jpeg'),
                    verify_prompt
                ]
            )

            answer = response.text.strip().lower()
            confirmed = answer.startswith('yes')

            logger.debug(f"Gemini verify response: '{answer}' -> {confirmed}")
            return confirmed

        except Exception as e:
            logger.warning(f"Gemini quick verification failed: {e}")
            return False  # Default to not verified on error
