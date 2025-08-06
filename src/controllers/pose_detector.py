"""
Pose detection controller using MediaPipe Pose.

This module provides the PoseDetector class that handles real-time pose detection
and keypoint extraction for arm tracking in the OpenCV Minecraft Controller.
"""

import cv2
import numpy as np
import mediapipe as mp
from typing import Optional, NamedTuple

from ..models.data_models import Point, ArmKeypoints


class PoseLandmarks(NamedTuple):
    """Container for MediaPipe pose landmarks."""
    landmarks: list


class PoseDetector:
    """Handles pose detection and arm keypoint extraction using MediaPipe Pose.
    
    This class manages the MediaPipe Pose model for detecting human poses in video frames
    and extracting specific arm keypoints (shoulder, elbow, wrist) with confidence filtering.
    """
    
    # MediaPipe pose landmark indices for arm keypoints
    LEFT_SHOULDER = 11
    LEFT_ELBOW = 13
    LEFT_WRIST = 15
    RIGHT_SHOULDER = 12
    RIGHT_ELBOW = 14
    RIGHT_WRIST = 16
    
    def __init__(self, confidence_threshold: float = 0.5, model_complexity: int = 1):
        """Initialize the pose detector with MediaPipe Pose model.
        
        Args:
            confidence_threshold: Minimum confidence score for pose detection (0.0-1.0)
            model_complexity: Model complexity (0=Lite, 1=Full, 2=Heavy)
            
        Raises:
            ValueError: If confidence_threshold is not between 0.0 and 1.0 or model_complexity is invalid
        """
        if not 0.0 <= confidence_threshold <= 1.0:
            raise ValueError("confidence_threshold must be between 0.0 and 1.0")
        if model_complexity not in [0, 1, 2]:
            raise ValueError("model_complexity must be 0 (Lite), 1 (Full), or 2 (Heavy)")
            
        self.confidence_threshold = confidence_threshold
        self.model_complexity = model_complexity
        self._mp_pose = mp.solutions.pose
        self._pose_detector = self._mp_pose.Pose(
            static_image_mode=False,
            model_complexity=model_complexity,
            smooth_landmarks=True,
            enable_segmentation=False,
            smooth_segmentation=False,
            min_detection_confidence=confidence_threshold,
            min_tracking_confidence=confidence_threshold
        )
        self._last_detection_successful = False
    
    def detect_pose(self, frame: np.ndarray) -> Optional[PoseLandmarks]:
        """Detect pose landmarks in the given frame.
        
        Args:
            frame: Input video frame as numpy array (BGR format)
            
        Returns:
            PoseLandmarks object if pose detected successfully, None otherwise
            
        Raises:
            ValueError: If frame is not a valid numpy array
        """
        if not isinstance(frame, np.ndarray):
            raise ValueError("frame must be a numpy array")
        if len(frame.shape) != 3 or frame.shape[2] != 3:
            raise ValueError("frame must be a 3-channel BGR image")
            
        try:
            # Convert BGR to RGB for MediaPipe
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            
            # Process the frame
            results = self._pose_detector.process(rgb_frame)
            
            if results.pose_landmarks:
                self._last_detection_successful = True
                return PoseLandmarks(landmarks=results.pose_landmarks.landmark)
            else:
                self._last_detection_successful = False
                return None
                
        except Exception as e:
            self._last_detection_successful = False
            # Log error in real implementation, for now just return None
            return None
    
    def get_arm_keypoints(self, landmarks: PoseLandmarks) -> Optional[ArmKeypoints]:
        """Extract arm keypoints from pose landmarks.
        
        Prioritizes left arm, falls back to right arm if left arm confidence is low.
        
        Args:
            landmarks: PoseLandmarks object from pose detection
            
        Returns:
            ArmKeypoints object if valid arm keypoints found, None otherwise
            
        Raises:
            ValueError: If landmarks is not a valid PoseLandmarks object
        """
        if not isinstance(landmarks, PoseLandmarks):
            raise ValueError("landmarks must be a PoseLandmarks object")
        if not landmarks.landmarks:
            raise ValueError("landmarks.landmarks cannot be empty")
            
        try:
            # Try left arm first
            left_arm = self._extract_arm_keypoints(
                landmarks, 
                self.LEFT_SHOULDER, 
                self.LEFT_ELBOW, 
                self.LEFT_WRIST
            )
            
            if left_arm and left_arm.confidence >= self.confidence_threshold:
                return left_arm
            
            # Fall back to right arm
            right_arm = self._extract_arm_keypoints(
                landmarks,
                self.RIGHT_SHOULDER,
                self.RIGHT_ELBOW,
                self.RIGHT_WRIST
            )
            
            if right_arm and right_arm.confidence >= self.confidence_threshold:
                return right_arm
                
            return None
            
        except (IndexError, AttributeError):
            return None
    
    def _extract_arm_keypoints(
        self, 
        landmarks: PoseLandmarks, 
        shoulder_idx: int, 
        elbow_idx: int, 
        wrist_idx: int
    ) -> Optional[ArmKeypoints]:
        """Extract keypoints for a specific arm (left or right).
        
        Args:
            landmarks: PoseLandmarks object from pose detection
            shoulder_idx: Index of shoulder landmark
            elbow_idx: Index of elbow landmark
            wrist_idx: Index of wrist landmark
            
        Returns:
            ArmKeypoints object if extraction successful, None otherwise
        """
        try:
            landmark_list = landmarks.landmarks
            
            # Check if indices are valid
            max_idx = max(shoulder_idx, elbow_idx, wrist_idx)
            if len(landmark_list) <= max_idx:
                return None
            
            # Extract landmarks
            shoulder_lm = landmark_list[shoulder_idx]
            elbow_lm = landmark_list[elbow_idx]
            wrist_lm = landmark_list[wrist_idx]
            
            # Check visibility/confidence
            min_confidence = min(
                shoulder_lm.visibility,
                elbow_lm.visibility,
                wrist_lm.visibility
            )
            
            if min_confidence < self.confidence_threshold:
                return None
            
            # Convert to Point objects
            shoulder = Point(
                x=shoulder_lm.x,
                y=shoulder_lm.y,
                z=shoulder_lm.z
            )
            elbow = Point(
                x=elbow_lm.x,
                y=elbow_lm.y,
                z=elbow_lm.z
            )
            wrist = Point(
                x=wrist_lm.x,
                y=wrist_lm.y,
                z=wrist_lm.z
            )
            
            return ArmKeypoints(
                shoulder=shoulder,
                elbow=elbow,
                wrist=wrist,
                confidence=min_confidence
            )
            
        except (AttributeError, IndexError):
            return None
    
    def is_pose_detected(self) -> bool:
        """Check if the last pose detection was successful.
        
        Returns:
            True if last detection was successful, False otherwise
        """
        return self._last_detection_successful
    
    def __del__(self):
        """Clean up MediaPipe resources."""
        if hasattr(self, '_pose_detector'):
            self._pose_detector.close()