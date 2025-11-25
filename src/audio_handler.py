"""
Audio recording and transcription handler using faster-whisper.
Records audio in background thread and provides streaming transcription.
"""

import threading
import queue
import time
import re
import numpy as np
import sounddevice as sd
from faster_whisper import WhisperModel
from typing import Optional
import logging

logger = logging.getLogger(__name__)

# Common Whisper hallucination artifacts to filter out
# These often appear when audio cuts off or has silence
WHISPER_ARTIFACTS = [
    r'\s+you\.?$',           # Trailing "you" or "you."
    r'\s+you\s*$',           # Trailing "you" with whitespace
    r'^you\s+',              # Leading "you"
    r'\s+thank you\.?$',     # Trailing "thank you"
    r'\s+thanks\.?$',        # Trailing "thanks"
    r'^\s*you\s*$',          # Just "you" by itself
    r'\s+bye\.?$',           # Trailing "bye"
]

def clean_transcription(text: str) -> str:
    """
    Clean up common Whisper transcription artifacts.

    Args:
        text: Raw transcription text

    Returns:
        Cleaned text with artifacts removed
    """
    if not text:
        return text

    cleaned = text.strip()

    # Apply artifact filters
    for pattern in WHISPER_ARTIFACTS:
        cleaned = re.sub(pattern, '', cleaned, flags=re.IGNORECASE)

    # Clean up any double spaces left behind
    cleaned = re.sub(r'\s+', ' ', cleaned).strip()

    return cleaned


class AudioHandler:
    """Handles audio recording and transcription in a separate thread."""

    def __init__(self, model_name: str = "small", sample_rate: int = 16000, chunk_duration: float = 3.0):
        """
        Initialize audio handler with Whisper model.

        Args:
            model_name: Whisper model to use (tiny, base, small, medium, large)
            sample_rate: Audio sample rate in Hz (16000 is optimal for Whisper)
            chunk_duration: Duration of audio chunks to process in seconds
        """
        self.sample_rate = sample_rate
        self.chunk_duration = chunk_duration
        self.chunk_size = int(sample_rate * chunk_duration)

        # Thread-safe state
        self.recording = False
        self.recording_lock = threading.Lock()

        # Queue for passing transcribed text to main thread
        self.text_queue = queue.Queue()

        # Audio buffer for accumulating samples
        self.audio_buffer = []
        self.buffer_lock = threading.Lock()

        # Background thread
        self.record_thread: Optional[threading.Thread] = None
        self.should_stop = threading.Event()

        # Initialize Whisper model
        logger.info(f"Loading Whisper {model_name} model...")
        try:
            # faster-whisper uses CTranslate2 for efficient inference
            # compute_type: int8 for speed, float16 for accuracy
            self.model = WhisperModel(model_name, device="cpu", compute_type="int8")
            logger.info("Whisper model loaded successfully")
        except Exception as e:
            logger.error(f"Failed to load Whisper model: {e}")
            raise

    def start_recording(self):
        """Start recording audio in background thread."""
        with self.recording_lock:
            if self.recording:
                logger.warning("Already recording, ignoring start request")
                return

            self.recording = True
            self.should_stop.clear()
            self.audio_buffer = []

            # Start background recording thread
            self.record_thread = threading.Thread(target=self._recording_loop, daemon=True)
            self.record_thread.start()
            logger.info("Started audio recording")

    def stop_recording(self):
        """Stop recording and process any remaining audio."""
        with self.recording_lock:
            if not self.recording:
                return

            self.recording = False
            self.should_stop.set()

            # Wait for thread to finish
            if self.record_thread and self.record_thread.is_alive():
                self.record_thread.join(timeout=2.0)

            # Process any remaining audio in buffer
            self._process_remaining_buffer()
            logger.info("Stopped audio recording")

    def is_recording(self) -> bool:
        """Check if currently recording."""
        with self.recording_lock:
            return self.recording

    def get_transcribed_text(self) -> Optional[str]:
        """
        Get next transcribed text chunk from queue (non-blocking).

        Returns:
            Transcribed text or None if queue is empty
        """
        try:
            return self.text_queue.get_nowait()
        except queue.Empty:
            return None

    def _recording_loop(self):
        """Main recording loop running in background thread."""
        try:
            with sd.InputStream(
                samplerate=self.sample_rate,
                channels=1,
                dtype='float32',
                blocksize=int(self.sample_rate * 0.1),  # 100ms blocks
                callback=self._audio_callback
            ):
                logger.info("Audio stream opened")
                # Keep thread alive while recording
                while not self.should_stop.is_set():
                    time.sleep(0.1)

                    # Check if we have enough audio to process a chunk
                    should_process = False
                    with self.buffer_lock:
                        buffer_size = len(self.audio_buffer)
                        if buffer_size >= self.chunk_size:
                            logger.info(f"📊 Buffer has {buffer_size} samples ({buffer_size/self.sample_rate:.1f}s), processing chunk...")
                            should_process = True

                    # Process chunk outside the lock to avoid deadlock
                    if should_process:
                        self._process_chunk()

        except Exception as e:
            logger.error(f"❌ Error in recording loop: {e}", exc_info=True)
            with self.recording_lock:
                self.recording = False

    def _audio_callback(self, indata, frames, time_info, status):
        """Callback for audio stream - adds samples to buffer."""
        if status:
            logger.warning(f"Audio stream status: {status}")

        # Add audio data to buffer
        with self.buffer_lock:
            self.audio_buffer.extend(indata[:, 0].copy())
            # Log buffer size every second
            if len(self.audio_buffer) % self.sample_rate < frames:
                logger.debug(f"🎤 Audio buffer: {len(self.audio_buffer)} samples ({len(self.audio_buffer)/self.sample_rate:.1f}s)")

    def _process_chunk(self):
        """Process accumulated audio chunk with Whisper."""
        with self.buffer_lock:
            if len(self.audio_buffer) < self.chunk_size:
                return

            # Extract chunk from buffer
            chunk = np.array(self.audio_buffer[:self.chunk_size], dtype=np.float32)
            # Keep remaining audio in buffer for next chunk
            self.audio_buffer = self.audio_buffer[self.chunk_size:]

        logger.info(f"🎙️  Processing {len(chunk)} samples ({len(chunk)/self.sample_rate:.1f}s) with Whisper...")

        # Transcribe chunk (this may take ~0.3-0.5s)
        try:
            # Ensure chunk is contiguous and properly formatted
            chunk = np.ascontiguousarray(chunk, dtype=np.float32)

            # Validate audio data
            if not np.isfinite(chunk).all():
                logger.error("❌ Audio chunk contains NaN or Inf values!")
                return

            # faster-whisper returns segments generator
            segments, info = self.model.transcribe(
                chunk,
                language="en",
                beam_size=1,  # Faster with beam_size=1
                vad_filter=False,  # No VAD for real-time
                without_timestamps=True  # Faster without timestamps
            )

            # Collect all segments into text
            text_parts = [segment.text for segment in segments]
            text = " ".join(text_parts).strip()

            logger.info(f"🎙️  Whisper raw: '{text}'")

            # Clean up common Whisper artifacts
            text = clean_transcription(text)

            # Only queue non-empty transcriptions
            if text:
                self.text_queue.put(text)
                logger.info(f"✅ Transcribed: {text}")
            else:
                logger.info(f"⚠️  Whisper returned empty text (silence or noise)")

        except Exception as e:
            logger.error(f"❌ Error transcribing audio chunk: {e}", exc_info=True)

    def _process_remaining_buffer(self):
        """Process any remaining audio in buffer when recording stops."""
        with self.buffer_lock:
            if len(self.audio_buffer) < self.sample_rate * 0.5:  # Skip if less than 0.5s
                return

            # Pad to minimum size if needed
            chunk = np.array(self.audio_buffer, dtype=np.float32)
            if len(chunk) < self.sample_rate:  # Whisper needs at least 1s
                chunk = np.pad(chunk, (0, self.sample_rate - len(chunk)))

        # Transcribe final chunk
        try:
            segments, info = self.model.transcribe(
                chunk,
                language="en",
                beam_size=1,
                vad_filter=False,
                without_timestamps=True
            )
            text_parts = [segment.text for segment in segments]
            text = " ".join(text_parts).strip()

            # Clean up common Whisper artifacts
            text = clean_transcription(text)

            if text:
                self.text_queue.put(text)
                logger.info(f"Transcribed final chunk: {text}")

        except Exception as e:
            logger.error(f"Error transcribing final chunk: {e}")

    def cleanup(self):
        """Clean up resources."""
        self.stop_recording()
        logger.info("Audio handler cleaned up")
