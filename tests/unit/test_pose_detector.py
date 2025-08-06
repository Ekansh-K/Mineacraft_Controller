"""
Unit tests for the PoseDetector class.

Tests pose detection functionality, keypoint extraction, and error handling
using mocked MediaPipe results.
"""

import pytest
import numpy as np
from unittest.mock import Mock, patch, MagicMock
from typing import NamedTuple

from src.controllers.pose_detector import PoseDetector, PoseLandmarks
from src.models.data_models import Point, ArmKeypoints


class MockLandmark:
    """Mock MediaPipe landmark for testing."""
    def __init__(self, x: float, y: float, z: float, visibility: float):
        self.x = x
        self.y = y
        self.z = z
        self.visibility = visibility


class TestPoseDetector:
    """Test cases for PoseDetector class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.confidence_threshold = 0.7
        self.detector = PoseDetector(confidence_threshold=self.confidence_threshold)
    
    def test_init_valid_confidence(self):
        """Test PoseDetector initialization with valid confidence threshold."""
        detector = PoseDetector(0.5)
        assert detector.confidence_threshold == 0.5
        assert hasattr(detector, '_mp_pose')
        assert hasattr(detector, '_pose_detector')
        assert detector._last_detection_successful is False
    
    def test_init_invalid_confidence_low(self):
        """Test PoseDetector initialization with confidence threshold too low."""
        with pytest.raises(ValueError, match="confidence_threshold must be between 0.0 and 1.0"):
            PoseDetector(-0.1)
    
    def test_init_invalid_confidence_high(self):
        """Test PoseDetector initialization with confidence threshold too high."""
        with pytest.raises(ValueError, match="confidence_threshold must be between 0.0 and 1.0"):
            PoseDetector(1.1)
    
    @patch('cv2.cvtColor')
    def test_detect_pose_success(self, mock_cvtcolor):
        """Test successful pose detection."""
        # Create mock frame
        frame = np.zeros((480, 640, 3), dtype=np.uint8)
        mock_cvtcolor.return_value = frame
        
        # Create mock landmarks
        mock_landmarks = [MockLandmark(0.5, 0.5, 0.0, 0.9) for _ in range(33)]
        
        # Mock MediaPipe results
        mock_results = Mock()
        mock_results.pose_landmarks = Mock()
        mock_results.pose_landmarks.landmark = mock_landmarks
        
        # Mock the pose detector process method
        self.detector._pose_detector.process = Mock(return_value=mock_results)
        
        # Test detection
        result = self.detector.detect_pose(frame)
        
        assert result is not None
        assert isinstance(result, PoseLandmarks)
        assert len(result.landmarks) == 33
        assert self.detector.is_pose_detected() is True
        mock_cvtcolor.assert_called_once()
    
    @patch('cv2.cvtColor')
    def test_detect_pose_no_landmarks(self, mock_cvtcolor):
        """Test pose detection when no landmarks are found."""
        frame = np.zeros((480, 640, 3), dtype=np.uint8)
        mock_cvtcolor.return_value = frame
        
        # Mock MediaPipe results with no landmarks
        mock_results = Mock()
        mock_results.pose_landmarks = None
        
        self.detector._pose_detector.process = Mock(return_value=mock_results)
        
        result = self.detector.detect_pose(frame)
        
        assert result is None
        assert self.detector.is_pose_detected() is False
    
    def test_detect_pose_invalid_frame_type(self):
        """Test pose detection with invalid frame type."""
        with pytest.raises(ValueError, match="frame must be a numpy array"):
            self.detector.detect_pose("not_an_array")
    
    def test_detect_pose_invalid_frame_shape(self):
        """Test pose detection with invalid frame shape."""
        # 2D array instead of 3D
        frame = np.zeros((480, 640), dtype=np.uint8)
        with pytest.raises(ValueError, match="frame must be a 3-channel BGR image"):
            self.detector.detect_pose(frame)
        
        # Wrong number of channels
        frame = np.zeros((480, 640, 4), dtype=np.uint8)
        with pytest.raises(ValueError, match="frame must be a 3-channel BGR image"):
            self.detector.detect_pose(frame)
    
    @patch('cv2.cvtColor')
    def test_detect_pose_exception_handling(self, mock_cvtcolor):
        """Test pose detection exception handling."""
        frame = np.zeros((480, 640, 3), dtype=np.uint8)
        mock_cvtcolor.side_effect = Exception("OpenCV error")
        
        result = self.detector.detect_pose(frame)
        
        assert result is None
        assert self.detector.is_pose_detected() is False
    
    def test_get_arm_keypoints_left_arm_success(self):
        """Test successful left arm keypoint extraction."""
        # Create mock landmarks with high confidence left arm
        landmarks_list = [MockLandmark(0.0, 0.0, 0.0, 0.1) for _ in range(33)]
        
        # Set left arm landmarks with high confidence
        landmarks_list[11] = MockLandmark(0.3, 0.2, 0.0, 0.9)  # LEFT_SHOULDER
        landmarks_list[13] = MockLandmark(0.4, 0.4, 0.0, 0.9)  # LEFT_ELBOW
        landmarks_list[15] = MockLandmark(0.5, 0.6, 0.0, 0.9)  # LEFT_WRIST
        
        landmarks = PoseLandmarks(landmarks=landmarks_list)
        
        result = self.detector.get_arm_keypoints(landmarks)
        
        assert result is not None
        assert isinstance(result, ArmKeypoints)
        assert result.shoulder.x == 0.3
        assert result.shoulder.y == 0.2
        assert result.elbow.x == 0.4
        assert result.elbow.y == 0.4
        assert result.wrist.x == 0.5
        assert result.wrist.y == 0.6
        assert result.confidence == 0.9
    
    def test_get_arm_keypoints_right_arm_fallback(self):
        """Test right arm keypoint extraction when left arm confidence is low."""
        # Create mock landmarks
        landmarks_list = [MockLandmark(0.0, 0.0, 0.0, 0.1) for _ in range(33)]
        
        # Set left arm landmarks with low confidence
        landmarks_list[11] = MockLandmark(0.3, 0.2, 0.0, 0.5)  # LEFT_SHOULDER
        landmarks_list[13] = MockLandmark(0.4, 0.4, 0.0, 0.5)  # LEFT_ELBOW
        landmarks_list[15] = MockLandmark(0.5, 0.6, 0.0, 0.5)  # LEFT_WRIST
        
        # Set right arm landmarks with high confidence
        landmarks_list[12] = MockLandmark(0.7, 0.2, 0.0, 0.9)  # RIGHT_SHOULDER
        landmarks_list[14] = MockLandmark(0.6, 0.4, 0.0, 0.9)  # RIGHT_ELBOW
        landmarks_list[16] = MockLandmark(0.5, 0.6, 0.0, 0.9)  # RIGHT_WRIST
        
        landmarks = PoseLandmarks(landmarks=landmarks_list)
        
        result = self.detector.get_arm_keypoints(landmarks)
        
        assert result is not None
        assert isinstance(result, ArmKeypoints)
        assert result.shoulder.x == 0.7  # Right shoulder
        assert result.confidence == 0.9
    
    def test_get_arm_keypoints_both_arms_low_confidence(self):
        """Test keypoint extraction when both arms have low confidence."""
        # Create mock landmarks with low confidence for both arms
        landmarks_list = [MockLandmark(0.0, 0.0, 0.0, 0.1) for _ in range(33)]
        
        # Set both arms with low confidence
        for idx in [11, 12, 13, 14, 15, 16]:
            landmarks_list[idx] = MockLandmark(0.5, 0.5, 0.0, 0.5)
        
        landmarks = PoseLandmarks(landmarks=landmarks_list)
        
        result = self.detector.get_arm_keypoints(landmarks)
        
        assert result is None
    
    def test_get_arm_keypoints_invalid_landmarks_type(self):
        """Test keypoint extraction with invalid landmarks type."""
        with pytest.raises(ValueError, match="landmarks must be a PoseLandmarks object"):
            self.detector.get_arm_keypoints("not_landmarks")
    
    def test_get_arm_keypoints_empty_landmarks(self):
        """Test keypoint extraction with empty landmarks."""
        landmarks = PoseLandmarks(landmarks=[])
        with pytest.raises(ValueError, match="landmarks.landmarks cannot be empty"):
            self.detector.get_arm_keypoints(landmarks)
    
    def test_get_arm_keypoints_insufficient_landmarks(self):
        """Test keypoint extraction with insufficient landmarks."""
        # Only 10 landmarks, but we need at least 17 for right wrist (index 16)
        landmarks_list = [MockLandmark(0.5, 0.5, 0.0, 0.9) for _ in range(10)]
        landmarks = PoseLandmarks(landmarks=landmarks_list)
        
        result = self.detector.get_arm_keypoints(landmarks)
        
        assert result is None
    
    def test_extract_arm_keypoints_success(self):
        """Test successful arm keypoint extraction for specific arm."""
        landmarks_list = [MockLandmark(0.0, 0.0, 0.0, 0.1) for _ in range(33)]
        
        # Set specific arm landmarks
        landmarks_list[11] = MockLandmark(0.3, 0.2, 0.1, 0.9)  # shoulder
        landmarks_list[13] = MockLandmark(0.4, 0.4, 0.2, 0.8)  # elbow
        landmarks_list[15] = MockLandmark(0.5, 0.6, 0.3, 0.85) # wrist
        
        landmarks = PoseLandmarks(landmarks=landmarks_list)
        
        result = self.detector._extract_arm_keypoints(landmarks, 11, 13, 15)
        
        assert result is not None
        assert result.shoulder.x == 0.3
        assert result.shoulder.z == 0.1
        assert result.elbow.y == 0.4
        assert result.wrist.z == 0.3
        assert result.confidence == 0.8  # minimum of the three
    
    def test_extract_arm_keypoints_low_confidence(self):
        """Test arm keypoint extraction with low confidence landmarks."""
        landmarks_list = [MockLandmark(0.0, 0.0, 0.0, 0.1) for _ in range(33)]
        
        # Set landmarks with one low confidence point
        landmarks_list[11] = MockLandmark(0.3, 0.2, 0.0, 0.9)  # shoulder
        landmarks_list[13] = MockLandmark(0.4, 0.4, 0.0, 0.5)  # elbow - low confidence
        landmarks_list[15] = MockLandmark(0.5, 0.6, 0.0, 0.9)  # wrist
        
        landmarks = PoseLandmarks(landmarks=landmarks_list)
        
        result = self.detector._extract_arm_keypoints(landmarks, 11, 13, 15)
        
        assert result is None
    
    def test_extract_arm_keypoints_invalid_indices(self):
        """Test arm keypoint extraction with invalid landmark indices."""
        landmarks_list = [MockLandmark(0.5, 0.5, 0.0, 0.9) for _ in range(10)]
        landmarks = PoseLandmarks(landmarks=landmarks_list)
        
        # Try to access index 15 when only 10 landmarks exist
        result = self.detector._extract_arm_keypoints(landmarks, 11, 13, 15)
        
        assert result is None
    
    def test_is_pose_detected_initial_state(self):
        """Test initial state of pose detection flag."""
        detector = PoseDetector()
        assert detector.is_pose_detected() is False
    
    def test_is_pose_detected_after_success(self):
        """Test pose detection flag after successful detection."""
        # Manually set the flag to simulate successful detection
        self.detector._last_detection_successful = True
        assert self.detector.is_pose_detected() is True
    
    def test_is_pose_detected_after_failure(self):
        """Test pose detection flag after failed detection."""
        # First set to True, then False to test state change
        self.detector._last_detection_successful = True
        self.detector._last_detection_successful = False
        assert self.detector.is_pose_detected() is False
    
    def test_destructor_cleanup(self):
        """Test that destructor properly cleans up MediaPipe resources."""
        detector = PoseDetector()
        detector._pose_detector = Mock()
        detector._pose_detector.close = Mock()
        
        # Call destructor
        detector.__del__()
        
        detector._pose_detector.close.assert_called_once()
    
    def test_destructor_no_detector(self):
        """Test destructor when pose detector doesn't exist."""
        detector = PoseDetector()
        # Remove the pose detector to simulate initialization failure
        delattr(detector, '_pose_detector')
        
        # Should not raise an exception
        detector.__del__()


class TestPoseLandmarks:
    """Test cases for PoseLandmarks NamedTuple."""
    
    def test_pose_landmarks_creation(self):
        """Test PoseLandmarks creation and access."""
        landmarks_list = [MockLandmark(0.5, 0.5, 0.0, 0.9) for _ in range(5)]
        landmarks = PoseLandmarks(landmarks=landmarks_list)
        
        assert landmarks.landmarks == landmarks_list
        assert len(landmarks.landmarks) == 5
        assert landmarks.landmarks[0].x == 0.5
    
    def test_pose_landmarks_empty(self):
        """Test PoseLandmarks with empty landmarks list."""
        landmarks = PoseLandmarks(landmarks=[])
        assert landmarks.landmarks == []
        assert len(landmarks.landmarks) == 0