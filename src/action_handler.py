"""
Action handler for executing commands based on detected gestures.
"""
import pyautogui
import logging
import time
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
        Activate macOS voice dictation by simulating Fn+Fn key press.

        Note: This toggles dictation on/off.

        Returns:
            True if successful
        """
        try:
            # Toggle dictation state
            self.dictation_active = not self.dictation_active

            self.logger.info(f"Action: {'Activating' if self.dictation_active else 'Deactivating'} voice dictation")

            # Simulate Fn key press twice
            # On macOS, the Fn key simulation might not work directly with pyautogui
            # We'll use the keyboard shortcut approach
            pyautogui.press('fn')
            time.sleep(0.2)
            pyautogui.press('fn')

            return True
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
