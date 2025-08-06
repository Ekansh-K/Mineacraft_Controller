"""Unit tests for CameraManager class."""

import pytest
from unittest.mock import Mock, patch, MagicMock
import numpy as np
import cv2

from src.controllers.camera_manager import CameraManager


class TestCameraManager:
    """Test cases for CameraManager functionality."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.camera_manager = CameraManager(camera_id=0)
    
    def test_init_default_values(self):
        """Test CameraManager initialization with default values."""
        cm = CameraManager()
        assert cm.camera_id == 0
        assert cm.width == 640
        assert cm.height == 480
        assert cm.cap is None
        assert cm._is_initialized is False
    
    def test_init_custom_values(self):
        """Test CameraManager initialization with custom values."""
        cm = CameraManager(camera_id=1, width=1280, height=720)
        assert cm.camera_id == 1
        assert cm.width == 1280
        assert cm.height == 720
    
    @patch('cv2.VideoCapture')
    def test_start_capture_success(self, mock_video_capture):
        """Test successful camera initialization."""
        # Mock successful camera capture
        mock_cap = Mock()
        mock_cap.isOpened.return_value = True
        mock_cap.read.return_value = (True, np.zeros((480, 640, 3), dtype=np.uint8))
        mock_video_capture.return_value = mock_cap
        
        result = self.camera_manager.start_capture()
        
        assert result is True
        assert self.camera_manager._is_initialized is True
        assert self.camera_manager.cap is mock_cap
        
        # Verify camera properties were set
        mock_cap.set.assert_any_call(cv2.CAP_PROP_FRAME_WIDTH, 640)
        mock_cap.set.assert_any_call(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        mock_cap.set.assert_any_call(cv2.CAP_PROP_FPS, 30)
    
    @patch('cv2.VideoCapture')
    def test_start_capture_camera_not_opened(self, mock_video_capture):
        """Test camera initialization failure when camera won't open."""
        mock_cap = Mock()
        mock_cap.isOpened.return_value = False
        mock_video_capture.return_value = mock_cap
        
        result = self.camera_manager.start_capture()
        
        assert result is False
        assert self.camera_manager._is_initialized is False
    
    @patch('cv2.VideoCapture')
    def test_start_capture_frame_read_failure(self, mock_video_capture):
        """Test camera initialization failure when test frame capture fails."""
        mock_cap = Mock()
        mock_cap.isOpened.return_value = True
        mock_cap.read.return_value = (False, None)
        mock_video_capture.return_value = mock_cap
        
        result = self.camera_manager.start_capture()
        
        assert result is False
        assert self.camera_manager._is_initialized is False
    
    @patch('cv2.VideoCapture')
    def test_start_capture_exception_handling(self, mock_video_capture):
        """Test camera initialization with exception handling."""
        mock_video_capture.side_effect = Exception("Camera error")
        
        result = self.camera_manager.start_capture()
        
        assert result is False
        assert self.camera_manager._is_initialized is False
    
    def test_get_frame_not_initialized(self):
        """Test get_frame when camera is not initialized."""
        result = self.camera_manager.get_frame()
        assert result is None
    
    @patch('cv2.VideoCapture')
    def test_get_frame_success(self, mock_video_capture):
        """Test successful frame capture."""
        # Setup initialized camera
        mock_cap = Mock()
        mock_cap.isOpened.return_value = True
        test_frame = np.zeros((480, 640, 3), dtype=np.uint8)
        mock_cap.read.return_value = (True, test_frame)
        mock_video_capture.return_value = mock_cap
        
        self.camera_manager.start_capture()
        
        # Test frame capture
        result = self.camera_manager.get_frame()
        
        assert result is not None
        assert isinstance(result, np.ndarray)
        np.testing.assert_array_equal(result, test_frame)
    
    @patch('cv2.VideoCapture')
    def test_get_frame_read_failure(self, mock_video_capture):
        """Test frame capture when read fails."""
        # Setup initialized camera
        mock_cap = Mock()
        mock_cap.isOpened.return_value = True
        mock_cap.read.side_effect = [(True, np.zeros((480, 640, 3))), (False, None)]
        mock_video_capture.return_value = mock_cap
        
        self.camera_manager.start_capture()
        
        # Test failed frame capture
        result = self.camera_manager.get_frame()
        
        assert result is None
    
    @patch('cv2.VideoCapture')
    def test_get_frame_exception_handling(self, mock_video_capture):
        """Test frame capture with exception handling."""
        # Setup initialized camera
        mock_cap = Mock()
        mock_cap.isOpened.return_value = True
        mock_cap.read.side_effect = [(True, np.zeros((480, 640, 3))), Exception("Read error")]
        mock_video_capture.return_value = mock_cap
        
        self.camera_manager.start_capture()
        
        # Test exception during frame capture
        result = self.camera_manager.get_frame()
        
        assert result is None
    
    def test_is_available_not_initialized(self):
        """Test is_available when camera is not initialized."""
        result = self.camera_manager.is_available()
        assert result is False
    
    @patch('cv2.VideoCapture')
    def test_is_available_success(self, mock_video_capture):
        """Test is_available with working camera."""
        mock_cap = Mock()
        mock_cap.isOpened.return_value = True
        mock_cap.read.return_value = (True, np.zeros((480, 640, 3)))
        mock_video_capture.return_value = mock_cap
        
        self.camera_manager.start_capture()
        
        result = self.camera_manager.is_available()
        assert result is True
    
    @patch('cv2.VideoCapture')
    def test_is_available_camera_closed(self, mock_video_capture):
        """Test is_available when camera is closed."""
        mock_cap = Mock()
        mock_cap.isOpened.side_effect = [True, True, False]  # Opens, test frame, then closed
        mock_cap.read.return_value = (True, np.zeros((480, 640, 3)))
        mock_video_capture.return_value = mock_cap
        
        self.camera_manager.start_capture()
        
        # Reset the side_effect to return False for the is_available check
        mock_cap.isOpened.side_effect = None
        mock_cap.isOpened.return_value = False
        
        result = self.camera_manager.is_available()
        assert result is False
    
    @patch('cv2.VideoCapture')
    def test_is_available_exception_handling(self, mock_video_capture):
        """Test is_available with exception handling."""
        mock_cap = Mock()
        mock_cap.isOpened.side_effect = [True, True]  # For start_capture calls
        mock_cap.read.return_value = (True, np.zeros((480, 640, 3)))
        mock_video_capture.return_value = mock_cap
        
        self.camera_manager.start_capture()
        
        # Set exception for the is_available check
        mock_cap.isOpened.side_effect = Exception("Check error")
        
        result = self.camera_manager.is_available()
        assert result is False
    
    def test_release_not_initialized(self):
        """Test release when camera is not initialized."""
        # Should not raise exception
        self.camera_manager.release()
        assert self.camera_manager.cap is None
        assert self.camera_manager._is_initialized is False
    
    @patch('cv2.VideoCapture')
    def test_release_success(self, mock_video_capture):
        """Test successful camera resource release."""
        mock_cap = Mock()
        mock_cap.isOpened.return_value = True
        mock_cap.read.return_value = (True, np.zeros((480, 640, 3)))
        mock_video_capture.return_value = mock_cap
        
        self.camera_manager.start_capture()
        self.camera_manager.release()
        
        mock_cap.release.assert_called_once()
        assert self.camera_manager.cap is None
        assert self.camera_manager._is_initialized is False
    
    @patch('cv2.VideoCapture')
    def test_release_exception_handling(self, mock_video_capture):
        """Test release with exception handling."""
        mock_cap = Mock()
        mock_cap.isOpened.return_value = True
        mock_cap.read.return_value = (True, np.zeros((480, 640, 3)))
        mock_cap.release.side_effect = Exception("Release error")
        mock_video_capture.return_value = mock_cap
        
        self.camera_manager.start_capture()
        
        # Should not raise exception
        self.camera_manager.release()
        assert self.camera_manager.cap is None
        assert self.camera_manager._is_initialized is False
    
    @patch('cv2.VideoCapture')
    def test_reconnect_success(self, mock_video_capture):
        """Test successful camera reconnection."""
        mock_cap = Mock()
        mock_cap.isOpened.return_value = True
        mock_cap.read.return_value = (True, np.zeros((480, 640, 3)))
        mock_video_capture.return_value = mock_cap
        
        # Initial connection
        self.camera_manager.start_capture()
        
        # Reconnect
        result = self.camera_manager.reconnect()
        
        assert result is True
        assert self.camera_manager._is_initialized is True
    
    @patch('cv2.VideoCapture')
    def test_reconnect_failure(self, mock_video_capture):
        """Test failed camera reconnection."""
        # First call succeeds, second fails
        mock_cap_success = Mock()
        mock_cap_success.isOpened.return_value = True
        mock_cap_success.read.return_value = (True, np.zeros((480, 640, 3)))
        
        mock_cap_fail = Mock()
        mock_cap_fail.isOpened.return_value = False
        
        mock_video_capture.side_effect = [mock_cap_success, mock_cap_fail]
        
        # Initial connection
        self.camera_manager.start_capture()
        
        # Failed reconnect
        result = self.camera_manager.reconnect()
        
        assert result is False
        assert self.camera_manager._is_initialized is False
    
    def test_get_camera_info_not_available(self):
        """Test get_camera_info when camera is not available."""
        result = self.camera_manager.get_camera_info()
        assert result == {}
    
    @patch('cv2.VideoCapture')
    def test_get_camera_info_success(self, mock_video_capture):
        """Test successful camera info retrieval."""
        mock_cap = Mock()
        mock_cap.isOpened.return_value = True
        mock_cap.read.return_value = (True, np.zeros((480, 640, 3)))
        mock_cap.get.side_effect = lambda prop: {
            cv2.CAP_PROP_FRAME_WIDTH: 640,
            cv2.CAP_PROP_FRAME_HEIGHT: 480,
            cv2.CAP_PROP_FPS: 30.0
        }[prop]
        mock_video_capture.return_value = mock_cap
        
        self.camera_manager.start_capture()
        
        result = self.camera_manager.get_camera_info()
        
        expected = {
            'width': 640,
            'height': 480,
            'fps': 30.0,
            'camera_id': 0,
            'is_available': True
        }
        assert result == expected
    
    @patch('cv2.VideoCapture')
    def test_get_camera_info_exception_handling(self, mock_video_capture):
        """Test get_camera_info with exception handling."""
        mock_cap = Mock()
        mock_cap.isOpened.return_value = True
        mock_cap.read.return_value = (True, np.zeros((480, 640, 3)))
        mock_cap.get.side_effect = Exception("Get property error")
        mock_video_capture.return_value = mock_cap
        
        self.camera_manager.start_capture()
        
        result = self.camera_manager.get_camera_info()
        
        assert result == {'is_available': False}