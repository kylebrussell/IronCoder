"""
Visual feedback overlay for gesture control system.
Shows clutch status and detected gestures on video feed.
"""
import cv2
import numpy as np
from typing import Tuple, Optional


class VisualFeedback:
    """Provides visual overlays for gesture control feedback."""

    def __init__(
        self,
        clutch_engaged_color: Tuple[int, int, int] = (0, 255, 0),  # Green
        clutch_disengaged_color: Tuple[int, int, int] = (0, 0, 255),  # Red
        border_thickness: int = 10
    ):
        """
        Initialize visual feedback.

        Args:
            clutch_engaged_color: BGR color for engaged clutch (default: green)
            clutch_disengaged_color: BGR color for disengaged clutch (default: red)
            border_thickness: Thickness of border in pixels
        """
        self.clutch_engaged_color = clutch_engaged_color
        self.clutch_disengaged_color = clutch_disengaged_color
        self.border_thickness = border_thickness

    def draw_clutch_indicator(
        self,
        frame: np.ndarray,
        is_engaged: bool
    ) -> np.ndarray:
        """
        Draw colored border to indicate clutch status.

        Args:
            frame: Video frame to draw on
            is_engaged: True if clutch is engaged

        Returns:
            Frame with border overlay
        """
        color = self.clutch_engaged_color if is_engaged else self.clutch_disengaged_color
        height, width = frame.shape[:2]

        # Draw border rectangle
        cv2.rectangle(
            frame,
            (0, 0),
            (width - 1, height - 1),
            color,
            self.border_thickness
        )

        return frame

    def draw_status_text(
        self,
        frame: np.ndarray,
        clutch_engaged: bool,
        current_gesture: str,
        x: int = 10,
        y: int = 30
    ) -> np.ndarray:
        """
        Draw status text showing clutch and gesture state.

        Args:
            frame: Video frame to draw on
            clutch_engaged: True if clutch is engaged
            current_gesture: Current detected gesture name
            x: X position for text
            y: Y position for text (top line)

        Returns:
            Frame with status text
        """
        # Clutch status
        clutch_text = "CLUTCH: ENGAGED" if clutch_engaged else "CLUTCH: DISENGAGED"
        clutch_color = self.clutch_engaged_color if clutch_engaged else self.clutch_disengaged_color

        cv2.putText(
            frame,
            clutch_text,
            (x, y),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.7,
            clutch_color,
            2
        )

        # Gesture status (only show if clutch is engaged and gesture is not "none")
        if clutch_engaged and current_gesture and current_gesture != "none":
            gesture_display = current_gesture.replace('_', ' ').title()
            cv2.putText(
                frame,
                f"GESTURE: {gesture_display}",
                (x, y + 35),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.7,
                (255, 255, 0),  # Yellow
                2
            )

        return frame

    def draw_gesture_hint(
        self,
        frame: np.ndarray,
        show_hints: bool = True
    ) -> np.ndarray:
        """
        Draw gesture hints on the frame.

        Args:
            frame: Video frame to draw on
            show_hints: Whether to show hints

        Returns:
            Frame with gesture hints
        """
        if not show_hints:
            return frame

        height, width = frame.shape[:2]

        # Define gestures with name, action, and color
        gestures = [
            ("OPEN PALM", "Voice Dictation", (147, 112, 219)),      # Medium purple
            ("PEACE SIGN", "Start Dev Server", (46, 204, 113)),     # Green
            ("THUMBS UP", "Commit & Push", (52, 152, 219)),         # Blue
            ("THUMBS DOWN", "Clear Input", (231, 76, 60)),          # Red
            ("POINTING", "Stop Dev Server", (230, 126, 34))         # Orange
        ]

        # Panel dimensions
        panel_height = 220
        panel_margin = 20
        panel_y = height - panel_height - panel_margin

        # Draw main background panel with gradient effect
        overlay = frame.copy()

        # Dark background
        cv2.rectangle(
            overlay,
            (panel_margin, panel_y),
            (width - panel_margin, height - panel_margin),
            (30, 30, 40),  # Dark blue-grey
            -1
        )

        # Add subtle border
        cv2.rectangle(
            overlay,
            (panel_margin, panel_y),
            (width - panel_margin, height - panel_margin),
            (70, 70, 80),  # Light grey border
            2
        )

        cv2.addWeighted(overlay, 0.85, frame, 0.15, 0, frame)

        # Draw title
        title = "GESTURE CONTROLS"
        title_y = panel_y + 35
        cv2.putText(
            frame,
            title,
            (panel_margin + 20, title_y),
            cv2.FONT_HERSHEY_DUPLEX,
            0.7,
            (255, 255, 255),
            2
        )

        # Draw underline
        cv2.line(
            frame,
            (panel_margin + 20, title_y + 8),
            (width - panel_margin - 20, title_y + 8),
            (100, 100, 120),
            1
        )

        # Calculate card dimensions
        num_gestures = len(gestures)
        card_width = (width - 2 * panel_margin - 40 - (num_gestures - 1) * 10) // num_gestures
        card_height = 120
        card_y = panel_y + 70

        # Draw gesture cards
        for i, (gesture_name, action, color) in enumerate(gestures):
            card_x = panel_margin + 20 + i * (card_width + 10)

            # Draw card background
            card_overlay = frame.copy()
            cv2.rectangle(
                card_overlay,
                (card_x, card_y),
                (card_x + card_width, card_y + card_height),
                (50, 50, 60),  # Slightly lighter than panel
                -1
            )
            cv2.addWeighted(card_overlay, 0.7, frame, 0.3, 0, frame)

            # Draw colored top border
            cv2.rectangle(
                frame,
                (card_x, card_y),
                (card_x + card_width, card_y + 4),
                color,
                -1
            )

            # Draw gesture name (centered, larger)
            name_y = card_y + 50
            # Calculate text width for centering
            (text_width, _), _ = cv2.getTextSize(
                gesture_name,
                cv2.FONT_HERSHEY_SIMPLEX,
                0.5,
                2
            )
            name_x = card_x + (card_width - text_width) // 2
            cv2.putText(
                frame,
                gesture_name,
                (name_x, name_y),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.5,
                (255, 255, 255),
                2
            )

            # Draw action text with icon-style separator
            cv2.line(
                frame,
                (card_x + 10, name_y + 15),
                (card_x + card_width - 10, name_y + 15),
                (70, 70, 80),
                1
            )

            action_y = name_y + 45
            (text_width, _), _ = cv2.getTextSize(
                action,
                cv2.FONT_HERSHEY_SIMPLEX,
                0.45,
                1
            )
            action_x = card_x + (card_width - text_width) // 2
            cv2.putText(
                frame,
                action,
                (action_x, action_y),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.45,
                color,
                1
            )

        return frame

    def draw_action_feedback(
        self,
        frame: np.ndarray,
        action_text: Optional[str],
        duration_frames: int = 30
    ) -> np.ndarray:
        """
        Draw feedback when an action is triggered.

        Args:
            frame: Video frame to draw on
            action_text: Text describing the triggered action
            duration_frames: Number of frames to show the feedback

        Returns:
            Frame with action feedback
        """
        if not action_text:
            return frame

        height, width = frame.shape[:2]

        # Draw semi-transparent background
        overlay = frame.copy()
        box_height = 80
        box_y = (height // 2) - (box_height // 2)
        cv2.rectangle(
            overlay,
            (width // 4, box_y),
            (3 * width // 4, box_y + box_height),
            (0, 200, 0),  # Green background
            -1
        )
        cv2.addWeighted(overlay, 0.7, frame, 0.3, 0, frame)

        # Draw action text
        text_size = cv2.getTextSize(
            action_text,
            cv2.FONT_HERSHEY_SIMPLEX,
            1.0,
            2
        )[0]
        text_x = (width - text_size[0]) // 2
        text_y = box_y + (box_height + text_size[1]) // 2

        cv2.putText(
            frame,
            action_text,
            (text_x, text_y),
            cv2.FONT_HERSHEY_SIMPLEX,
            1.0,
            (255, 255, 255),
            2
        )

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

        # Draw pulsing red circle in top-right corner
        cv2.circle(
            frame,
            (width - 40, 40),
            15,
            (0, 0, 255),  # Red
            -1
        )

        # Add "RECORDING" text
        cv2.putText(
            frame,
            "RECORDING",
            (width - 150, 45),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.6,
            (0, 0, 255),
            2
        )

        return frame
