"""
Audio recording and transcription handler using whisper.cpp.
Records audio in background thread and provides streaming transcription.
"""

import threading
import queue
import time
import numpy as np
import sounddevice as sd
from pywhispercpp.model import Model
from typing import Optional
import logging

logger = logging.getLogger(__name__)


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
            self.model = Model(model_name, n_threads=4)
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
                    with self.buffer_lock:
                        if len(self.audio_buffer) >= self.chunk_size:
                            self._process_chunk()

        except Exception as e:
            logger.error(f"Error in recording loop: {e}")
            with self.recording_lock:
                self.recording = False

    def _audio_callback(self, indata, frames, time_info, status):
        """Callback for audio stream - adds samples to buffer."""
        if status:
            logger.warning(f"Audio stream status: {status}")

        # Add audio data to buffer
        with self.buffer_lock:
            self.audio_buffer.extend(indata[:, 0].copy())

    def _process_chunk(self):
        """Process accumulated audio chunk with Whisper."""
        with self.buffer_lock:
            if len(self.audio_buffer) < self.chunk_size:
                return

            # Extract chunk from buffer
            chunk = np.array(self.audio_buffer[:self.chunk_size], dtype=np.float32)
            # Keep remaining audio in buffer for next chunk
            self.audio_buffer = self.audio_buffer[self.chunk_size:]

        # Transcribe chunk (this may take ~0.3-0.5s)
        try:
            # Whisper expects audio normalized to [-1, 1]
            # sounddevice already provides float32 in this range
            text = self.model.transcribe(chunk, language='en')

            # Only queue non-empty transcriptions
            if text and text.strip():
                self.text_queue.put(text.strip())
                logger.info(f"Transcribed: {text.strip()}")

        except Exception as e:
            logger.error(f"Error transcribing audio chunk: {e}")

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
            text = self.model.transcribe(chunk, language='en')
            if text and text.strip():
                self.text_queue.put(text.strip())
                logger.info(f"Transcribed final chunk: {text.strip()}")

        except Exception as e:
            logger.error(f"Error transcribing final chunk: {e}")

    def cleanup(self):
        """Clean up resources."""
        self.stop_recording()
        logger.info("Audio handler cleaned up")
