"""
Action handler for executing commands based on detected gestures.
Supports configurable gesture-to-command mappings via ConfigManager.
"""
import pyautogui
import logging
import time
from typing import Optional
from src.audio_handler import AudioHandler
from src.config_manager import ConfigManager


class ActionHandler:
    """Handles execution of actions triggered by gestures."""

    def __init__(self, config_manager: Optional[ConfigManager] = None):
        """
        Initialize action handler.

        Args:
            config_manager: Optional ConfigManager for gesture-command mappings.
                          If not provided, creates a default one.
        """
        self.logger = logging.getLogger(__name__)

        # Use provided config manager or create default
        self.config = config_manager or ConfigManager()

        # Set PyAutoGUI settings for safety
        pyautogui.PAUSE = 0.1  # Pause between actions
        pyautogui.FAILSAFE = True  # Move mouse to corner to abort

        # Initialize audio handler for voice input
        try:
            self.audio_handler = AudioHandler(model_name="small")
            self.logger.info("Audio handler initialized successfully")
        except Exception as e:
            self.logger.error(f"Failed to initialize audio handler: {e}")
            self.audio_handler = None

    def send_escape_escape(self) -> bool:
        """
        Send double-escape key press to clear input prompt.

        Returns:
            True if successful
        """
        try:
            self.logger.info("Action: Sending double-escape")
            pyautogui.press('escape')
            time.sleep(0.1)
            pyautogui.press('escape')
            return True
        except Exception as e:
            self.logger.error(f"Failed to send double-escape: {e}")
            return False

    def start_recording(self) -> bool:
        """
        Start recording audio for voice input (push-to-talk).
        Non-blocking - recording happens in background thread.

        Returns:
            True if recording started successfully
        """
        if not self.audio_handler:
            self.logger.error("Audio handler not initialized")
            return False

        try:
            self.audio_handler.start_recording()
            self.logger.info("Action: Started voice recording (push-to-talk)")
            return True
        except Exception as e:
            self.logger.error(f"Failed to start recording: {e}")
            return False

    def stop_recording(self) -> bool:
        """
        Stop recording audio and process final chunk.

        Returns:
            True if recording stopped successfully
        """
        if not self.audio_handler:
            return False

        try:
            self.audio_handler.stop_recording()
            self.logger.info("Action: Stopped voice recording")
            return True
        except Exception as e:
            self.logger.error(f"Failed to stop recording: {e}")
            return False

    def process_transcription_queue(self):
        """
        Check for new transcribed text and type it immediately.
        Should be called frequently from main loop to enable streaming.
        """
        if not self.audio_handler:
            return

        # Process all available transcriptions
        while True:
            text = self.audio_handler.get_transcribed_text()
            if text is None:
                break

            # Type the transcribed chunk immediately
            try:
                self.logger.info(f"Typing transcription: {text[:50]}...")
                pyautogui.write(text + " ", interval=0.02)  # Add space between chunks
            except Exception as e:
                self.logger.error(f"Failed to type transcription: {e}")

    def execute_command(self, command: str) -> bool:
        """
        Type a command string and press Enter.

        Args:
            command: The command text to type

        Returns:
            True if successful
        """
        try:
            self.logger.info(f"Action: Executing command '{command}'")
            pyautogui.write(command, interval=0.05)
            time.sleep(0.1)
            pyautogui.press('enter')
            return True
        except Exception as e:
            self.logger.error(f"Failed to execute command: {e}")
            return False

    def execute_gesture_action(self, gesture: str) -> Optional[str]:
        """
        Execute the appropriate action for a detected gesture.

        Uses ConfigManager to look up the command/action for the gesture.
        Note: open_palm (voice_dictation) is handled separately in main loop
        for push-to-talk behavior.

        Args:
            gesture: Gesture name from CommandGestureRecognizer

        Returns:
            Human-readable description of the action taken, or None if no action
        """
        # Get gesture configuration
        gesture_config = self.config.get_gesture_config(gesture)

        if not gesture_config:
            self.logger.warning(f"No configuration found for gesture: {gesture}")
            return None

        # Get description for feedback
        description = self.config.get_gesture_description(gesture)

        # Check for special action
        action = gesture_config.get('action')
        if action:
            if action == 'voice_dictation':
                # Handled separately in main loop
                return None
            elif action == 'clear_input':
                success = self.send_escape_escape()
                return description if success else f"{description} (FAILED)"
            else:
                self.logger.warning(f"Unknown action: {action}")
                return None

        # Execute text command
        command = gesture_config.get('command')
        if command:
            success = self.execute_command(command)
            return description if success else f"{description} (FAILED)"

        return None

    def is_voice_gesture(self, gesture: str) -> bool:
        """
        Check if a gesture is configured for voice dictation.

        Args:
            gesture: Gesture name

        Returns:
            True if gesture uses voice_dictation action
        """
        action = self.config.get_gesture_action(gesture)
        return action == 'voice_dictation'

    def is_dictation_active(self) -> bool:
        """
        Check if dictation is currently active.

        Returns:
            True if audio recording is active
        """
        if not self.audio_handler:
            return False
        return self.audio_handler.is_recording()

    def cleanup(self):
        """Clean up resources on shutdown."""
        if self.audio_handler:
            self.audio_handler.cleanup()
