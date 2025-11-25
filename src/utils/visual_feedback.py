"""
Visual feedback overlay for gesture control system.
Minimal/clean design inspired by macOS/iOS aesthetics.
"""
import cv2
import numpy as np
import math
from typing import Tuple, Optional, List, Dict
from src.utils.theme import COLORS, GESTURE_COLORS, DIMENSIONS, ALPHA, ANIMATION


class VisualFeedback:
    """Provides visual overlays for gesture control feedback."""

    def __init__(
        self,
        config_manager=None,
    ):
        """
        Initialize visual feedback.

        Args:
            config_manager: Optional ConfigManager for gesture descriptions
        """
        self.config = config_manager
        self.frame_count = 0
        self.action_feedback_text = None
        self.action_feedback_frames = 0
        self.action_feedback_color = COLORS['accent_git']

    def _draw_transparent_rect(
        self,
        frame: np.ndarray,
        x: int, y: int, w: int, h: int,
        color: Tuple[int, int, int],
        alpha: float
    ):
        """Draw a semi-transparent rectangle."""
        overlay = frame.copy()
        cv2.rectangle(overlay, (x, y), (x + w, y + h), color, -1)
        cv2.addWeighted(overlay, alpha, frame, 1 - alpha, 0, frame)

    def _draw_rounded_rect(
        self,
        frame: np.ndarray,
        x: int, y: int, w: int, h: int,
        color: Tuple[int, int, int],
        radius: int,
        thickness: int = -1,
        alpha: float = 1.0
    ):
        """Draw a rectangle with rounded corners."""
        if alpha < 1.0:
            overlay = frame.copy()
            self._draw_rounded_rect_solid(overlay, x, y, w, h, color, radius, thickness)
            cv2.addWeighted(overlay, alpha, frame, 1 - alpha, 0, frame)
        else:
            self._draw_rounded_rect_solid(frame, x, y, w, h, color, radius, thickness)

    def _draw_rounded_rect_solid(
        self,
        frame: np.ndarray,
        x: int, y: int, w: int, h: int,
        color: Tuple[int, int, int],
        radius: int,
        thickness: int = -1
    ):
        """Draw a solid rounded rectangle."""
        # Clamp radius
        radius = min(radius, h // 2, w // 2)

        if thickness == -1:
            # Filled rounded rectangle
            # Draw corners
            cv2.circle(frame, (x + radius, y + radius), radius, color, -1)
            cv2.circle(frame, (x + w - radius, y + radius), radius, color, -1)
            cv2.circle(frame, (x + radius, y + h - radius), radius, color, -1)
            cv2.circle(frame, (x + w - radius, y + h - radius), radius, color, -1)
            # Fill center areas
            cv2.rectangle(frame, (x + radius, y), (x + w - radius, y + h), color, -1)
            cv2.rectangle(frame, (x, y + radius), (x + w, y + h - radius), color, -1)
        else:
            # Outlined rounded rectangle
            cv2.line(frame, (x + radius, y), (x + w - radius, y), color, thickness)
            cv2.line(frame, (x + radius, y + h), (x + w - radius, y + h), color, thickness)
            cv2.line(frame, (x, y + radius), (x, y + h - radius), color, thickness)
            cv2.line(frame, (x + w, y + radius), (x + w, y + h - radius), color, thickness)
            cv2.ellipse(frame, (x + radius, y + radius), (radius, radius), 180, 0, 90, color, thickness)
            cv2.ellipse(frame, (x + w - radius, y + radius), (radius, radius), 270, 0, 90, color, thickness)
            cv2.ellipse(frame, (x + radius, y + h - radius), (radius, radius), 90, 0, 90, color, thickness)
            cv2.ellipse(frame, (x + w - radius, y + h - radius), (radius, radius), 0, 0, 90, color, thickness)

    def draw_clutch_indicator(
        self,
        frame: np.ndarray,
        is_engaged: bool
    ) -> np.ndarray:
        """
        Draw subtle border glow to indicate clutch status.

        Args:
            frame: Video frame to draw on
            is_engaged: True if clutch is engaged

        Returns:
            Frame with border overlay
        """
        height, width = frame.shape[:2]
        color = COLORS['clutch_engaged'] if is_engaged else COLORS['clutch_disengaged']
        thickness = DIMENSIONS['border_thickness']

        if is_engaged:
            # Draw glowing border effect with multiple layers
            for i in range(DIMENSIONS['glow_layers']):
                layer_thickness = thickness + i * 2
                layer_alpha = ALPHA['glow_base'] * (DIMENSIONS['glow_layers'] - i)

                overlay = frame.copy()
                cv2.rectangle(
                    overlay,
                    (i, i),
                    (width - 1 - i, height - 1 - i),
                    color,
                    layer_thickness
                )
                cv2.addWeighted(overlay, layer_alpha, frame, 1 - layer_alpha, 0, frame)

            # Inner solid border
            cv2.rectangle(frame, (0, 0), (width - 1, height - 1), color, thickness)
        else:
            # Subtle thin border when disengaged
            cv2.rectangle(frame, (0, 0), (width - 1, height - 1), color, 1)

        return frame

    def draw_status_pill(
        self,
        frame: np.ndarray,
        clutch_engaged: bool,
        current_gesture: str,
    ) -> np.ndarray:
        """
        Draw status pill in top-left corner.

        Args:
            frame: Video frame to draw on
            clutch_engaged: True if clutch is engaged
            current_gesture: Current detected gesture name

        Returns:
            Frame with status pill
        """
        margin = DIMENSIONS['panel_margin']
        pill_height = DIMENSIONS['status_pill_height']
        padding = DIMENSIONS['status_pill_padding']

        # Determine text and color
        if not clutch_engaged:
            text = "READY"
            bg_color = COLORS['background_dark']
            text_color = COLORS['text_secondary']
        elif current_gesture and current_gesture != "none":
            text = current_gesture.replace('_', ' ').upper()
            bg_color = GESTURE_COLORS.get(current_gesture, COLORS['background_elevated'])
            text_color = COLORS['text_primary']
        else:
            text = "ENGAGED"
            bg_color = COLORS['clutch_engaged']
            text_color = COLORS['background_dark']

        # Calculate pill width
        font = cv2.FONT_HERSHEY_SIMPLEX
        font_scale = 0.5
        thickness = 1
        (text_width, text_height), baseline = cv2.getTextSize(text, font, font_scale, thickness)
        pill_width = text_width + padding * 2

        # Draw pill background
        x, y = margin, margin
        self._draw_rounded_rect(
            frame, x, y, pill_width, pill_height,
            bg_color, pill_height // 2,
            alpha=ALPHA['panel_background']
        )

        # Draw text centered in pill
        text_x = x + padding
        text_y = y + (pill_height + text_height) // 2 - 2
        cv2.putText(frame, text, (text_x, text_y), font, font_scale, text_color, thickness, cv2.LINE_AA)

        return frame

    def draw_gesture_hint(
        self,
        frame: np.ndarray,
        show_hints: bool = True
    ) -> np.ndarray:
        """
        Draw gesture hints panel at bottom of frame.

        Args:
            frame: Video frame to draw on
            show_hints: Whether to show hints

        Returns:
            Frame with gesture hints
        """
        if not show_hints:
            return frame

        height, width = frame.shape[:2]
        margin = DIMENSIONS['panel_margin']
        panel_height = DIMENSIONS['panel_height']
        card_height = DIMENSIONS['card_height']
        card_gap = DIMENSIONS['card_gap']
        corner_radius = DIMENSIONS['corner_radius']

        # Define gestures with their display info
        gestures = self._get_gesture_display_list()

        # Panel position
        panel_x = margin
        panel_y = height - panel_height - margin
        panel_width = width - margin * 2

        # Draw panel background
        self._draw_rounded_rect(
            frame, panel_x, panel_y, panel_width, panel_height,
            COLORS['background_dark'], corner_radius,
            alpha=ALPHA['panel_background']
        )

        # Calculate card dimensions
        num_gestures = len(gestures)
        available_width = panel_width - margin * 2 - (num_gestures - 1) * card_gap
        card_width = available_width // num_gestures

        # Draw cards
        card_y = panel_y + (panel_height - card_height) // 2

        for i, (gesture_key, gesture_name, description, color) in enumerate(gestures):
            card_x = panel_x + margin + i * (card_width + card_gap)

            # Card background
            self._draw_rounded_rect(
                frame, card_x, card_y, card_width, card_height,
                COLORS['background_elevated'], corner_radius - 2,
                alpha=ALPHA['card_background']
            )

            # Colored top accent bar
            cv2.rectangle(
                frame,
                (card_x, card_y),
                (card_x + card_width, card_y + 3),
                color, -1
            )

            # Gesture name
            font = cv2.FONT_HERSHEY_SIMPLEX
            name_scale = 0.4
            (name_w, name_h), _ = cv2.getTextSize(gesture_name, font, name_scale, 1)
            name_x = card_x + (card_width - name_w) // 2
            name_y = card_y + 32
            cv2.putText(frame, gesture_name, (name_x, name_y), font, name_scale,
                       COLORS['text_primary'], 1, cv2.LINE_AA)

            # Separator line
            line_y = card_y + 45
            cv2.line(frame, (card_x + 8, line_y), (card_x + card_width - 8, line_y),
                    COLORS['border_light'], 1)

            # Description (command)
            desc_scale = 0.35
            # Truncate if too long
            max_chars = card_width // 6
            display_desc = description[:max_chars] + "..." if len(description) > max_chars else description
            (desc_w, desc_h), _ = cv2.getTextSize(display_desc, font, desc_scale, 1)
            desc_x = card_x + (card_width - desc_w) // 2
            desc_y = card_y + card_height - 15
            cv2.putText(frame, display_desc, (desc_x, desc_y), font, desc_scale,
                       color, 1, cv2.LINE_AA)

        return frame

    def _get_gesture_display_list(self) -> List[Tuple[str, str, str, Tuple[int, int, int]]]:
        """Get list of gestures with display info."""
        # Define gesture order and display names
        gesture_order = [
            ('open_palm', 'PALM'),
            ('peace_sign', 'PEACE'),
            ('thumbs_up', 'THUMB UP'),
            ('thumbs_down', 'THUMB DN'),
            ('pointing', 'POINT'),
            ('ok_sign', 'OK'),
            ('rock_sign', 'ROCK'),
            ('shaka', 'SHAKA'),
            ('three_fingers', 'THREE'),
            ('four_fingers', 'FOUR'),
        ]

        result = []
        for gesture_key, display_name in gesture_order:
            # Get description from config or use default
            if self.config:
                description = self.config.get_gesture_description(gesture_key)
            else:
                description = gesture_key.replace('_', ' ').title()

            color = GESTURE_COLORS.get(gesture_key, COLORS['text_secondary'])
            result.append((gesture_key, display_name, description, color))

        return result

    def draw_action_feedback(
        self,
        frame: np.ndarray,
        action_text: Optional[str] = None,
        gesture: Optional[str] = None,
    ) -> np.ndarray:
        """
        Draw feedback when an action is triggered.

        Args:
            frame: Video frame to draw on
            action_text: Text describing the triggered action (or None to use stored)
            gesture: Gesture that triggered the action (for color)

        Returns:
            Frame with action feedback
        """
        # Update stored feedback if new action provided
        if action_text:
            self.action_feedback_text = action_text
            self.action_feedback_frames = ANIMATION['fade_frames']
            self.action_feedback_color = GESTURE_COLORS.get(gesture, COLORS['accent_git'])

        # Don't draw if no feedback or expired
        if not self.action_feedback_text or self.action_feedback_frames <= 0:
            return frame

        # Calculate fade alpha
        fade_progress = self.action_feedback_frames / ANIMATION['fade_frames']
        alpha = min(fade_progress * 1.2, ALPHA['panel_background'])

        height, width = frame.shape[:2]
        popup_width = DIMENSIONS['action_popup_width']
        popup_height = DIMENSIONS['action_popup_height']
        corner_radius = DIMENSIONS['corner_radius']

        # Center position
        x = (width - popup_width) // 2
        y = (height - popup_height) // 2 - 50  # Slightly above center

        # Draw popup background with shadow
        shadow_offset = 4
        self._draw_rounded_rect(
            frame, x + shadow_offset, y + shadow_offset,
            popup_width, popup_height,
            COLORS['shadow'], corner_radius,
            alpha=ALPHA['shadow'] * fade_progress
        )

        # Main popup
        self._draw_rounded_rect(
            frame, x, y, popup_width, popup_height,
            self.action_feedback_color, corner_radius,
            alpha=alpha
        )

        # Text
        font = cv2.FONT_HERSHEY_SIMPLEX
        font_scale = 0.6
        (text_w, text_h), _ = cv2.getTextSize(self.action_feedback_text, font, font_scale, 2)
        text_x = x + (popup_width - text_w) // 2
        text_y = y + (popup_height + text_h) // 2
        text_alpha = int(255 * fade_progress)
        cv2.putText(frame, self.action_feedback_text, (text_x, text_y),
                   font, font_scale, COLORS['text_primary'], 2, cv2.LINE_AA)

        # Decrement frame counter
        self.action_feedback_frames -= 1

        return frame

    def draw_dictation_indicator(
        self,
        frame: np.ndarray,
        is_dictating: bool
    ) -> np.ndarray:
        """
        Draw indicator when dictation is active.

        Args:
            frame: Video frame to draw on
            is_dictating: True if dictation is currently active

        Returns:
            Frame with dictation indicator
        """
        if not is_dictating:
            return frame

        height, width = frame.shape[:2]
        margin = DIMENSIONS['panel_margin']

        # Pulsing effect
        self.frame_count += 1
        pulse = ANIMATION['pulse_min'] + (ANIMATION['pulse_max'] - ANIMATION['pulse_min']) * \
                (0.5 + 0.5 * math.sin(self.frame_count * ANIMATION['pulse_speed']))

        # Position in top-right
        dot_x = width - margin - 50
        dot_y = margin + 15
        dot_radius = int(8 * pulse)

        # Outer glow
        for i in range(3):
            glow_radius = dot_radius + i * 3
            glow_alpha = 0.15 * (3 - i) / 3
            overlay = frame.copy()
            cv2.circle(overlay, (dot_x, dot_y), glow_radius, COLORS['recording'], -1)
            cv2.addWeighted(overlay, glow_alpha, frame, 1 - glow_alpha, 0, frame)

        # Solid dot
        cv2.circle(frame, (dot_x, dot_y), dot_radius, COLORS['recording'], -1)

        # "REC" text
        font = cv2.FONT_HERSHEY_SIMPLEX
        cv2.putText(frame, "REC", (dot_x + 15, dot_y + 5),
                   font, 0.45, COLORS['recording'], 1, cv2.LINE_AA)

        return frame

    def draw_all(
        self,
        frame: np.ndarray,
        clutch_engaged: bool,
        current_gesture: str,
        is_dictating: bool,
        show_hints: bool = True,
        action_text: Optional[str] = None,
        action_gesture: Optional[str] = None,
    ) -> np.ndarray:
        """
        Draw all visual feedback elements.

        Args:
            frame: Video frame to draw on
            clutch_engaged: True if clutch is engaged
            current_gesture: Current detected gesture name
            is_dictating: True if dictation is active
            show_hints: Whether to show gesture hints
            action_text: Optional action feedback text
            action_gesture: Optional gesture that triggered action

        Returns:
            Frame with all overlays
        """
        # Draw in order (back to front)
        frame = self.draw_clutch_indicator(frame, clutch_engaged)
        frame = self.draw_gesture_hint(frame, show_hints)
        frame = self.draw_status_pill(frame, clutch_engaged, current_gesture)
        frame = self.draw_dictation_indicator(frame, is_dictating)
        frame = self.draw_action_feedback(frame, action_text, action_gesture)

        return frame
