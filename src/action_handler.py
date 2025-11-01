"""
Action handler for executing commands based on detected gestures.
"""
import pyautogui
import logging
import time
import subprocess
from typing import Optional


class ActionHandler:
    """Handles execution of actions triggered by gestures."""

    def __init__(self):
        """Initialize action handler."""
        self.logger = logging.getLogger(__name__)
        self.dictation_active = False

        # Set PyAutoGUI settings for safety
        pyautogui.PAUSE = 0.1  # Pause between actions
        pyautogui.FAILSAFE = True  # Move mouse to corner to abort

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

    def activate_voice_dictation(self) -> bool:
        """
        Activate macOS voice dictation using Apple Shortcuts and type the result.

        Note: This requires a Quick Action shortcut named "Dictate Text"
        to be created in the Shortcuts app that uses the "Dictate Text" action.

        Returns:
            True if successful
        """
        try:
            self.logger.info("Action: Activating voice dictation via Shortcuts")

            # Run the Apple Shortcut to trigger dictation
            # The shortcut will wait for speech and return the transcribed text
            result = subprocess.run(
                ['shortcuts', 'run', 'Dictate Text'],
                capture_output=True,
                text=True,
                timeout=30  # Give user time to speak
            )

            if result.returncode == 0:
                # Get the dictated text from stdout
                dictated_text = result.stdout.strip()

                if dictated_text:
                    self.logger.info(f"Dictated text: {dictated_text[:50]}...")

                    # Type the dictated text into the active window
                    pyautogui.write(dictated_text, interval=0.02)

                    self.logger.info("Successfully typed dictated text")
                    return True
                else:
                    self.logger.warning("No text was dictated")
                    return False
            else:
                self.logger.error(f"Shortcut failed: {result.stderr}")
                return False

        except subprocess.TimeoutExpired:
            self.logger.warning("Dictation timed out (took longer than 30 seconds)")
            return False
        except FileNotFoundError:
            self.logger.error("shortcuts command not found - is this macOS Monterey or later?")
            return False
        except Exception as e:
            self.logger.error(f"Failed to activate voice dictation: {e}")
            return False

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

    def execute_gesture_action(self, gesture: str) -> Optional[str]:
        """
        Execute the appropriate action for a detected gesture.

        Args:
            gesture: Gesture name from CommandGestureRecognizer

        Returns:
            Human-readable description of the action taken, or None if no action
        """
        action_map = {
            'open_palm': (self.activate_voice_dictation, "Voice Dictation Toggled"),
            'peace_sign': (self.send_escape_escape, "Input Cleared"),
            'thumbs_up': (self.git_commit_push, "Commit & Push"),
            'pointing': (self.send_yes_enter, "Approved Next Steps")
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
            True if dictation is active
        """
        return self.dictation_active
