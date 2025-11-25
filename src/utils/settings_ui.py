"""
In-app settings UI for gesture control configuration.
Keyboard-driven interface rendered with OpenCV.
"""
import cv2
import numpy as np
from typing import Optional, List, Tuple
from src.config_manager import ConfigManager
from src.utils.theme import COLORS, GESTURE_COLORS, DIMENSIONS, ALPHA


class SettingsUI:
    """In-app settings UI rendered with OpenCV."""

    def __init__(self, config_manager: ConfigManager):
        """
        Initialize settings UI.

        Args:
            config_manager: ConfigManager instance for reading/writing config
        """
        self.config = config_manager
        self.is_visible = False
        self.selected_index = 0
        self.edit_mode = False
        self.edit_buffer = ""
        self.preset_index = 0

        # Get gesture list from config
        self.gestures = self.config.get_all_gestures()
        self.preset_names = list(self.config.get_command_presets().keys())

    def toggle_visibility(self):
        """Show/hide settings panel."""
        self.is_visible = not self.is_visible
        if self.is_visible:
            self.edit_mode = False
            self.edit_buffer = ""
            self.gestures = self.config.get_all_gestures()

    def handle_key(self, key: int) -> bool:
        """
        Handle keyboard input.

        Args:
            key: OpenCV key code

        Returns:
            True if key was consumed by settings UI
        """
        if not self.is_visible:
            return False

        # Edit mode key handling
        if self.edit_mode:
            return self._handle_edit_key(key)

        # Navigation mode
        if key == ord('s') or key == 27:  # 's' or Escape
            self.toggle_visibility()
            return True

        elif key == 82 or key == ord('k'):  # Up arrow or 'k'
            self.selected_index = max(0, self.selected_index - 1)
            return True

        elif key == 84 or key == ord('j'):  # Down arrow or 'j'
            self.selected_index = min(len(self.gestures) - 1, self.selected_index + 1)
            return True

        elif key == 13:  # Enter - start editing
            gesture = self.gestures[self.selected_index]
            # Only allow editing non-special actions
            if not self.config.is_special_action(gesture):
                self.edit_mode = True
                self.edit_buffer = self.config.get_gesture_command(gesture) or ""
            return True

        elif key == 9:  # Tab - cycle presets
            self.preset_index = (self.preset_index + 1) % len(self.preset_names)
            return True

        elif ord('1') <= key <= ord('9'):  # Number keys - quick select from preset
            preset_idx = key - ord('1')
            preset_name = self.preset_names[self.preset_index]
            commands = self.config.get_preset_commands(preset_name)
            if preset_idx < len(commands):
                gesture = self.gestures[self.selected_index]
                if not self.config.is_special_action(gesture):
                    self.config.set_gesture_command(gesture, commands[preset_idx])
            return True

        elif key == ord('r'):  # Reset to defaults
            self.config.reset_to_defaults()
            return True

        return True  # Consume all keys when visible

    def _handle_edit_key(self, key: int) -> bool:
        """Handle keys in edit mode."""
        if key == 27:  # Escape - cancel edit
            self.edit_mode = False
            self.edit_buffer = ""
            return True

        elif key == 13:  # Enter - save edit
            gesture = self.gestures[self.selected_index]
            if self.edit_buffer.strip():
                self.config.set_gesture_command(gesture, self.edit_buffer.strip())
                self.config.save_config()
            self.edit_mode = False
            self.edit_buffer = ""
            return True

        elif key == 8:  # Backspace
            self.edit_buffer = self.edit_buffer[:-1]
            return True

        elif 32 <= key <= 126:  # Printable ASCII
            self.edit_buffer += chr(key)
            return True

        return True

    def draw(self, frame: np.ndarray) -> np.ndarray:
        """
        Draw settings UI on frame.

        Args:
            frame: Video frame to draw on

        Returns:
            Frame with settings UI overlay
        """
        if not self.is_visible:
            return frame

        height, width = frame.shape[:2]

        # Dim background
        overlay = frame.copy()
        cv2.rectangle(overlay, (0, 0), (width, height), COLORS['background_overlay'], -1)
        cv2.addWeighted(overlay, ALPHA['overlay_dark'], frame, 1 - ALPHA['overlay_dark'], 0, frame)

        # Panel dimensions
        panel_width = min(600, width - 40)
        panel_height = min(450, height - 40)
        panel_x = (width - panel_width) // 2
        panel_y = (height - panel_height) // 2

        # Draw main panel
        self._draw_panel_background(frame, panel_x, panel_y, panel_width, panel_height)

        # Draw content
        if self.edit_mode:
            self._draw_edit_dialog(frame, panel_x, panel_y, panel_width, panel_height)
        else:
            self._draw_gesture_list(frame, panel_x, panel_y, panel_width, panel_height)
            self._draw_presets(frame, panel_x, panel_y, panel_width, panel_height)
            self._draw_help_text(frame, panel_x, panel_y, panel_width, panel_height)

        return frame

    def _draw_panel_background(
        self,
        frame: np.ndarray,
        x: int, y: int, w: int, h: int
    ):
        """Draw the main settings panel background."""
        # Shadow
        shadow_offset = 6
        overlay = frame.copy()
        cv2.rectangle(
            overlay,
            (x + shadow_offset, y + shadow_offset),
            (x + w + shadow_offset, y + h + shadow_offset),
            COLORS['shadow'], -1
        )
        cv2.addWeighted(overlay, ALPHA['shadow'], frame, 1 - ALPHA['shadow'], 0, frame)

        # Main panel
        cv2.rectangle(frame, (x, y), (x + w, y + h), COLORS['background_medium'], -1)
        cv2.rectangle(frame, (x, y), (x + w, y + h), COLORS['border_medium'], 2)

        # Header
        header_height = 40
        cv2.rectangle(frame, (x, y), (x + w, y + header_height), COLORS['background_dark'], -1)

        # Title
        font = cv2.FONT_HERSHEY_SIMPLEX
        cv2.putText(frame, "SETTINGS", (x + 20, y + 28),
                   font, 0.7, COLORS['text_primary'], 2, cv2.LINE_AA)

        # Close hint
        cv2.putText(frame, "Press S or ESC to close", (x + w - 200, y + 28),
                   font, 0.4, COLORS['text_tertiary'], 1, cv2.LINE_AA)

    def _draw_gesture_list(
        self,
        frame: np.ndarray,
        panel_x: int, panel_y: int,
        panel_width: int, panel_height: int
    ):
        """Draw list of gestures with their commands."""
        font = cv2.FONT_HERSHEY_SIMPLEX
        start_y = panel_y + 60
        row_height = 32
        margin = 20

        # Section header
        cv2.putText(frame, "GESTURE MAPPINGS", (panel_x + margin, start_y),
                   font, 0.5, COLORS['text_secondary'], 1, cv2.LINE_AA)
        start_y += 25

        # List visible gestures (max 10)
        visible_count = min(10, len(self.gestures))
        scroll_offset = max(0, self.selected_index - visible_count + 3)

        for i in range(visible_count):
            gesture_idx = scroll_offset + i
            if gesture_idx >= len(self.gestures):
                break

            gesture = self.gestures[gesture_idx]
            row_y = start_y + i * row_height

            # Selection highlight
            if gesture_idx == self.selected_index:
                cv2.rectangle(
                    frame,
                    (panel_x + margin - 5, row_y - 18),
                    (panel_x + panel_width - margin + 5, row_y + 8),
                    COLORS['background_elevated'], -1
                )

            # Gesture color indicator
            color = GESTURE_COLORS.get(gesture, COLORS['text_secondary'])
            cv2.circle(frame, (panel_x + margin + 8, row_y - 5), 5, color, -1)

            # Gesture name
            display_name = gesture.replace('_', ' ').title()
            cv2.putText(frame, display_name, (panel_x + margin + 25, row_y),
                       font, 0.45, COLORS['text_primary'], 1, cv2.LINE_AA)

            # Command or action
            if self.config.is_special_action(gesture):
                action = self.config.get_gesture_action(gesture)
                display_cmd = f"[{action}]"
                cmd_color = COLORS['text_tertiary']
            else:
                cmd = self.config.get_gesture_command(gesture) or ""
                display_cmd = cmd[:30] + "..." if len(cmd) > 30 else cmd
                cmd_color = color

            cmd_x = panel_x + 180
            cv2.putText(frame, display_cmd, (cmd_x, row_y),
                       font, 0.4, cmd_color, 1, cv2.LINE_AA)

            # Edit hint for selected non-special gesture
            if gesture_idx == self.selected_index and not self.config.is_special_action(gesture):
                cv2.putText(frame, "[Enter to edit]",
                           (panel_x + panel_width - margin - 100, row_y),
                           font, 0.35, COLORS['text_tertiary'], 1, cv2.LINE_AA)

    def _draw_presets(
        self,
        frame: np.ndarray,
        panel_x: int, panel_y: int,
        panel_width: int, panel_height: int
    ):
        """Draw preset command buttons."""
        font = cv2.FONT_HERSHEY_SIMPLEX
        margin = 20
        presets_y = panel_y + panel_height - 120

        # Section header
        cv2.putText(frame, "QUICK PRESETS (Tab to switch, 1-9 to apply)",
                   (panel_x + margin, presets_y),
                   font, 0.4, COLORS['text_secondary'], 1, cv2.LINE_AA)
        presets_y += 25

        # Preset tabs
        tab_width = (panel_width - margin * 2) // len(self.preset_names)
        for i, preset_name in enumerate(self.preset_names):
            tab_x = panel_x + margin + i * tab_width
            display_name = preset_name.replace('_', ' ').title()

            # Highlight selected preset
            if i == self.preset_index:
                cv2.rectangle(
                    frame,
                    (tab_x, presets_y - 15),
                    (tab_x + tab_width - 5, presets_y + 5),
                    COLORS['background_elevated'], -1
                )

            cv2.putText(frame, display_name[:12], (tab_x + 5, presets_y),
                       font, 0.35,
                       COLORS['text_primary'] if i == self.preset_index else COLORS['text_tertiary'],
                       1, cv2.LINE_AA)

        # Show commands for selected preset
        presets_y += 20
        commands = self.config.get_preset_commands(self.preset_names[self.preset_index])
        for i, cmd in enumerate(commands[:5]):  # Show max 5
            display_cmd = f"{i+1}. {cmd[:35]}"
            cv2.putText(frame, display_cmd, (panel_x + margin, presets_y + i * 18),
                       font, 0.35, COLORS['text_secondary'], 1, cv2.LINE_AA)

    def _draw_help_text(
        self,
        frame: np.ndarray,
        panel_x: int, panel_y: int,
        panel_width: int, panel_height: int
    ):
        """Draw help text at bottom."""
        font = cv2.FONT_HERSHEY_SIMPLEX
        margin = 20
        help_y = panel_y + panel_height - 25

        help_text = "Up/Down: Navigate | Enter: Edit | Tab: Presets | R: Reset"
        cv2.putText(frame, help_text, (panel_x + margin, help_y),
                   font, 0.35, COLORS['text_tertiary'], 1, cv2.LINE_AA)

    def _draw_edit_dialog(
        self,
        frame: np.ndarray,
        panel_x: int, panel_y: int,
        panel_width: int, panel_height: int
    ):
        """Draw command edit dialog."""
        font = cv2.FONT_HERSHEY_SIMPLEX
        margin = 20

        gesture = self.gestures[self.selected_index]
        display_name = gesture.replace('_', ' ').title()

        # Title
        title_y = panel_y + 80
        cv2.putText(frame, f"EDIT COMMAND FOR: {display_name}",
                   (panel_x + margin, title_y),
                   font, 0.5, COLORS['text_primary'], 1, cv2.LINE_AA)

        # Current value
        current_y = title_y + 40
        current_cmd = self.config.get_gesture_command(gesture) or ""
        cv2.putText(frame, f"Current: {current_cmd}",
                   (panel_x + margin, current_y),
                   font, 0.4, COLORS['text_secondary'], 1, cv2.LINE_AA)

        # Edit field
        edit_y = current_y + 40
        cv2.putText(frame, "New:",
                   (panel_x + margin, edit_y),
                   font, 0.45, COLORS['text_primary'], 1, cv2.LINE_AA)

        # Input box
        input_x = panel_x + margin + 50
        input_width = panel_width - margin * 2 - 50
        input_height = 30

        cv2.rectangle(
            frame,
            (input_x, edit_y - 20),
            (input_x + input_width, edit_y + 10),
            COLORS['background_dark'], -1
        )
        cv2.rectangle(
            frame,
            (input_x, edit_y - 20),
            (input_x + input_width, edit_y + 10),
            COLORS['accent_git'], 1
        )

        # Input text with cursor
        display_text = self.edit_buffer + "|"
        cv2.putText(frame, display_text, (input_x + 10, edit_y),
                   font, 0.45, COLORS['text_primary'], 1, cv2.LINE_AA)

        # Presets for quick selection
        presets_y = edit_y + 50
        cv2.putText(frame, "PRESETS (press 1-5):",
                   (panel_x + margin, presets_y),
                   font, 0.4, COLORS['text_secondary'], 1, cv2.LINE_AA)

        preset_name = self.preset_names[self.preset_index]
        commands = self.config.get_preset_commands(preset_name)
        for i, cmd in enumerate(commands[:5]):
            cv2.putText(frame, f"{i+1}. {cmd}",
                       (panel_x + margin, presets_y + 25 + i * 22),
                       font, 0.4, COLORS['text_secondary'], 1, cv2.LINE_AA)

        # Help text
        help_y = panel_y + panel_height - 40
        cv2.putText(frame, "Enter: Save | Escape: Cancel | 1-5: Quick select preset",
                   (panel_x + margin, help_y),
                   font, 0.35, COLORS['text_tertiary'], 1, cv2.LINE_AA)
