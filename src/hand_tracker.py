"""
Hand tracking module using MediaPipe for dual hand detection.
"""
import cv2
import mediapipe as mp
import numpy as np
from typing import Optional, Dict, Tuple, List


class HandTracker:
    """Tracks hands using MediaPipe and provides landmark data for both hands."""

    def __init__(
        self,
        max_num_hands: int = 2,
        min_detection_confidence: float = 0.7,
        min_tracking_confidence: float = 0.5
    ):
        """
        Initialize the hand tracker.

        Args:
            max_num_hands: Maximum number of hands to detect (default: 2)
            min_detection_confidence: Minimum confidence for hand detection
            min_tracking_confidence: Minimum confidence for hand tracking
        """
        self.mp_hands = mp.solutions.hands
        self.mp_drawing = mp.solutions.drawing_utils
        self.mp_drawing_styles = mp.solutions.drawing_styles

        self.hands = self.mp_hands.Hands(
            max_num_hands=max_num_hands,
            min_detection_confidence=min_detection_confidence,
            min_tracking_confidence=min_tracking_confidence
        )

        # Hand landmark indices (for reference)
        self.WRIST = 0
        self.THUMB_CMC = 1
        self.THUMB_MCP = 2
        self.THUMB_IP = 3
        self.THUMB_TIP = 4
        self.INDEX_FINGER_MCP = 5
        self.INDEX_FINGER_PIP = 6
        self.INDEX_FINGER_DIP = 7
        self.INDEX_FINGER_TIP = 8
        self.MIDDLE_FINGER_MCP = 9
        self.MIDDLE_FINGER_PIP = 10
        self.MIDDLE_FINGER_DIP = 11
        self.MIDDLE_FINGER_TIP = 12
        self.RING_FINGER_MCP = 13
        self.RING_FINGER_PIP = 14
        self.RING_FINGER_DIP = 15
        self.RING_FINGER_TIP = 16
        self.PINKY_MCP = 17
        self.PINKY_PIP = 18
        self.PINKY_DIP = 19
        self.PINKY_TIP = 20

    def process_frame(self, frame: np.ndarray) -> Tuple[np.ndarray, Dict[str, any]]:
        """
        Process a video frame and detect hands.

        Args:
            frame: BGR image from OpenCV

        Returns:
            Tuple of (processed_frame, hands_data)
            - processed_frame: Frame with hand landmarks drawn
            - hands_data: Dict with 'left' and 'right' hand data (or None if not detected)
        """
        # Convert BGR to RGB
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

        # Process the frame
        results = self.hands.process(rgb_frame)

        # Initialize hands data
        hands_data = {
            'left': None,
            'right': None
        }

        # Draw hand landmarks if detected
        if results.multi_hand_landmarks and results.multi_handedness:
            for hand_landmarks, handedness in zip(results.multi_hand_landmarks, results.multi_handedness):
                # Draw landmarks on the frame
                self.mp_drawing.draw_landmarks(
                    frame,
                    hand_landmarks,
                    self.mp_hands.HAND_CONNECTIONS,
                    self.mp_drawing_styles.get_default_hand_landmarks_style(),
                    self.mp_drawing_styles.get_default_hand_connections_style()
                )

                # Determine which hand it is
                hand_label = handedness.classification[0].label.lower()  # 'left' or 'right'
                confidence = handedness.classification[0].score

                # Extract normalized landmarks (0-1 range)
                landmarks = []
                for landmark in hand_landmarks.landmark:
                    landmarks.append({
                        'x': landmark.x,
                        'y': landmark.y,
                        'z': landmark.z
                    })

                # Store hand data
                hands_data[hand_label] = {
                    'landmarks': landmarks,
                    'confidence': confidence,
                    'raw_landmarks': hand_landmarks
                }

        return frame, hands_data

    def get_landmark_position(
        self,
        hand_data: Dict,
        landmark_id: int,
        frame_shape: Tuple[int, int]
    ) -> Optional[Tuple[int, int]]:
        """
        Get pixel coordinates of a specific landmark.

        Args:
            hand_data: Hand data from process_frame
            landmark_id: Landmark ID (e.g., THUMB_TIP)
            frame_shape: (height, width) of the frame

        Returns:
            (x, y) pixel coordinates or None if hand_data is None
        """
        if hand_data is None or landmark_id >= len(hand_data['landmarks']):
            return None

        landmark = hand_data['landmarks'][landmark_id]
        height, width = frame_shape

        x = int(landmark['x'] * width)
        y = int(landmark['y'] * height)

        return (x, y)

    def calculate_distance(
        self,
        landmark1: Dict[str, float],
        landmark2: Dict[str, float]
    ) -> float:
        """
        Calculate Euclidean distance between two landmarks.

        Args:
            landmark1: First landmark dict with 'x', 'y', 'z'
            landmark2: Second landmark dict with 'x', 'y', 'z'

        Returns:
            Distance between landmarks
        """
        return np.sqrt(
            (landmark1['x'] - landmark2['x']) ** 2 +
            (landmark1['y'] - landmark2['y']) ** 2 +
            (landmark1['z'] - landmark2['z']) ** 2
        )

    def calculate_angle(
        self,
        point1: Dict[str, float],
        point2: Dict[str, float],
        point3: Dict[str, float]
    ) -> float:
        """
        Calculate angle between three points (in degrees).

        Args:
            point1: First point (e.g., fingertip)
            point2: Middle point (e.g., PIP joint)
            point3: Third point (e.g., MCP joint)

        Returns:
            Angle in degrees
        """
        # Convert to numpy arrays for easier calculation
        p1 = np.array([point1['x'], point1['y'], point1['z']])
        p2 = np.array([point2['x'], point2['y'], point2['z']])
        p3 = np.array([point3['x'], point3['y'], point3['z']])

        # Calculate vectors
        v1 = p1 - p2
        v2 = p3 - p2

        # Calculate angle
        cos_angle = np.dot(v1, v2) / (np.linalg.norm(v1) * np.linalg.norm(v2))
        cos_angle = np.clip(cos_angle, -1.0, 1.0)  # Avoid numerical errors
        angle = np.arccos(cos_angle)

        return np.degrees(angle)

    def is_finger_extended(
        self,
        hand_data: Dict,
        finger_tip_id: int,
        finger_pip_id: int
    ) -> bool:
        """
        Check if a finger is extended based on tip and PIP joint positions.

        Args:
            hand_data: Hand data from process_frame
            finger_tip_id: ID of fingertip landmark
            finger_pip_id: ID of PIP joint landmark

        Returns:
            True if finger is extended, False otherwise
        """
        if hand_data is None:
            return False

        landmarks = hand_data['landmarks']
        tip = landmarks[finger_tip_id]
        pip = landmarks[finger_pip_id]

        # For most fingers, extended means tip is higher (smaller y) than PIP
        # This is a simple heuristic that works reasonably well
        return tip['y'] < pip['y']

    def close(self):
        """Clean up resources."""
        if self.hands:
            self.hands.close()

    def __del__(self):
        """Destructor to ensure cleanup."""
        self.close()
