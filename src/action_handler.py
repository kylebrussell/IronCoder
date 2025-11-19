"""
Action handler for executing commands based on detected gestures.
"""
import pyautogui
import logging
import time
from typing import Optional
from src.audio_handler import AudioHandler


class ActionHandler:
    """Handles execution of actions triggered by gestures."""

    def __init__(self):
        """Initialize action handler."""
        self.logger = logging.getLogger(__name__)

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

    def send_yes_enter(self) -> bool:
        """
        Type 'Yes, proceed to the next steps' and press Enter.

        Returns:
            True if successful
        """
        try:
            self.logger.info("Action: Sending 'Yes, proceed to the next steps'")
            pyautogui.write('Yes, proceed to the next steps', interval=0.05)
            time.sleep(0.1)
            pyautogui.press('enter')
            return True
        except Exception as e:
            self.logger.error(f"Failed to send yes+enter: {e}")
            return False

    def git_commit_push(self) -> bool:
        """
        Type 'commit and push' command and press Enter.

        This tells Claude Code to commit changes and push them.

        Returns:
            True if successful
        """
        try:
            self.logger.info("Action: Sending 'commit and push' command")
            pyautogui.write('commit and push', interval=0.05)
            time.sleep(0.1)
            pyautogui.press('enter')
            return True
        except Exception as e:
            self.logger.error(f"Failed to send git commit+push: {e}")
            return False

    def start_dev_server(self) -> bool:
        """
        Type 'start the dev server' command and press Enter.

        This tells Claude Code to start the development server for the current project.

        Returns:
            True if successful
        """
        try:
            self.logger.info("Action: Sending 'start the dev server' command")
            pyautogui.write('start the dev server', interval=0.05)
            time.sleep(0.1)
            pyautogui.press('enter')
            return True
        except Exception as e:
            self.logger.error(f"Failed to send start dev server: {e}")
            return False

    def stop_dev_server(self) -> bool:
        """
        Type 'kill the running server' command and press Enter.

        This tells Claude Code to stop the currently running development server.

        Returns:
            True if successful
        """
        try:
            self.logger.info("Action: Sending 'kill the running server' command")
            pyautogui.write('kill the running server', interval=0.05)
            time.sleep(0.1)
            pyautogui.press('enter')
            return True
        except Exception as e:
            self.logger.error(f"Failed to send stop dev server: {e}")
            return False

    def execute_gesture_action(self, gesture: str) -> Optional[str]:
        """
        Execute the appropriate action for a detected gesture.

        Note: open_palm is handled separately in main loop for push-to-talk behavior.

        Args:
            gesture: Gesture name from CommandGestureRecognizer

        Returns:
            Human-readable description of the action taken, or None if no action
        """
        action_map = {
            'peace_sign': (self.start_dev_server, "Start Dev Server"),
            'thumbs_up': (self.git_commit_push, "Commit & Push"),
            'thumbs_down': (self.send_escape_escape, "Input Cleared"),
            'pointing': (self.stop_dev_server, "Stop Dev Server")
        }

        if gesture in action_map:
            action_func, action_name = action_map[gesture]
            success = action_func()

            if success:
                return action_name
            else:
                return f"{action_name} (FAILED)"

        return None

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
