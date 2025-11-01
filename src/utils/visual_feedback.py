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

        # Draw semi-transparent background for hints
        overlay = frame.copy()
        hints_height = 150
        cv2.rectangle(
            overlay,
            (0, height - hints_height),
            (width, height),
            (0, 0, 0),
            -1
        )
        cv2.addWeighted(overlay, 0.6, frame, 0.4, 0, frame)

        # Draw gesture hints
        hints = [
            "Open Palm: Voice Dictation",
            "Peace Sign: Clear Input",
            "Thumbs Up: Commit & Push",
            "Pointing: Approve Next Steps"
        ]

        y_start = height - hints_height + 30
        for i, hint in enumerate(hints):
            cv2.putText(
                frame,
                hint,
                (10, y_start + i * 30),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.6,
                (255, 255, 255),
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
