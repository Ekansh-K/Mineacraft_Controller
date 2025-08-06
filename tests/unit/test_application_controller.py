"""
Unit tests for the ApplicationController class.

Tests the main application controller's initialization, coordination of components,
and basic functionality without running the main loop.
"""

import pytest
from unittest.mock import Mock, patch
import numpy as np

from src.controllers.application_controller import ApplicationController
from src.models.enums import ControlState
from src.models.data_models import SystemState


class TestApplicationController:
    """Test cases for ApplicationController class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.app_controller = ApplicationController(camera_id=0, confidence_threshold=0.5)
    
    def test_init(self):
        """Test ApplicationController initialization."""
        assert self.app_controller.camera_id == 0
        assert self.app_controller.confidence_threshold == 0.5
        assert isinstance(self.app_controller.system_state, SystemState)
        assert self.app_controller.system_state.pose_control_enabled is True
        assert self.app_controller.system_state.current_control_state == ControlState.NEUTRAL
        assert not self.app_controller._running
        assert self.app_controller._frame_count == 0
    
    @patch('src.controllers.application_controller.CameraManager')
    @patch('src.controllers.application_controller.PoseDetector')
    @patch('src.controllers.application_controller.MouseController')
    @patch('src.controllers.application_controller.DisplayManager')
    @patch('src.controllers.application_controller.AngleCalculator')
    def test_initialize_success(self, mock_angle_calc, mock_display, mock_mouse, mock_pose, mock_camera):
        """Test successful initialization of all components."""
        # Setup mocks
        mock_camera_instance = Mock()
        mock_camera_instance.start_capture.return_value = True
        mock_camera.return_value = mock_camera_instance
        
        mock_mouse_instance = Mock()
        mock_mouse.return_value = mock_mouse_instance
        
        # Test initialization
        result = self.app_controller.initialize()
        
        assert result is True
        assert self.app_controller.camera_manager is not None
        assert self.app_controller.pose_detector is not None
        assert self.app_controller.mouse_controller is not None
        assert self.app_controller.display_manager is not None
        assert self.app_controller.angle_calculator is not None
        
        # Verify camera was started
        mock_camera_instance.start_capture.assert_called_once()
    
    @patch('src.controllers.application_controller.CameraManager')
    def test_initialize_camera_failure(self, mock_camera):
        """Test initialization failure when camera fails to start."""
        # Setup mock to fail camera initialization
        mock_camera_instance = Mock()
        mock_camera_instance.start_capture.return_value = False
        mock_camera.return_value = mock_camera_instance
        
        # Test initialization
        result = self.app_controller.initialize()
        
        assert result is False
        assert self.app_controller.camera_manager is not None
        mock_camera_instance.start_capture.assert_called_once()
    
    @patch('src.controllers.application_controller.MouseController')
    def test_initialize_mouse_failure(self, mock_mouse):
        """Test initialization failure when mouse controller fails."""
        from src.controllers.mouse_controller import MouseControlError
        
        # Setup mock to raise exception
        mock_mouse.side_effect = MouseControlError("PyAutoGUI not available")
        
        # Test initialization
        result = self.app_controller.initialize()
        
        assert result is False
    
    def test_toggle_pose_control(self):
        """Test toggling pose control on and off."""
        # Setup mock mouse controller
        mock_mouse = Mock()
        self.app_controller.mouse_controller = mock_mouse
        
        # Initially enabled
        assert self.app_controller.system_state.pose_control_enabled is True
        
        # Toggle to disabled
        self.app_controller.toggle_pose_control()
        assert self.app_controller.system_state.pose_control_enabled is False
        assert self.app_controller.system_state.current_control_state == ControlState.NEUTRAL
        mock_mouse.release_all.assert_called_once()
        
        # Toggle back to enabled
        mock_mouse.reset_mock()
        self.app_controller.toggle_pose_control()
        assert self.app_controller.system_state.pose_control_enabled is True
        mock_mouse.release_all.assert_not_called()
    
    def test_stop(self):
        """Test stopping the application."""
        self.app_controller._running = True
        self.app_controller.stop()
        assert self.app_controller._running is False
    
    def test_cleanup(self):
        """Test cleanup of all resources."""
        # Setup mock components
        mock_mouse = Mock()
        mock_display = Mock()
        mock_camera = Mock()
        
        self.app_controller.mouse_controller = mock_mouse
        self.app_controller.display_manager = mock_display
        self.app_controller.camera_manager = mock_camera
        
        # Test cleanup
        self.app_controller.cleanup()
        
        # Verify all cleanup methods were called
        mock_mouse.release_all.assert_called_once()
        mock_display.cleanup.assert_called_once()
        mock_camera.release.assert_called_once()
        
        # Verify system state was reset
        assert self.app_controller.system_state.pose_control_enabled is True
        assert self.app_controller.system_state.current_control_state == ControlState.NEUTRAL
        assert self.app_controller.system_state.error_count == 0
    
    def test_cleanup_with_exceptions(self):
        """Test cleanup handles exceptions gracefully."""
        # Setup mock components that raise exceptions
        mock_mouse = Mock()
        mock_mouse.release_all.side_effect = Exception("Mouse error")
        
        mock_display = Mock()
        mock_display.cleanup.side_effect = Exception("Display error")
        
        mock_camera = Mock()
        mock_camera.release.side_effect = Exception("Camera error")
        
        self.app_controller.mouse_controller = mock_mouse
        self.app_controller.display_manager = mock_display
        self.app_controller.camera_manager = mock_camera
        
        # Test cleanup - should not raise exceptions
        self.app_controller.cleanup()
        
        # Verify all cleanup methods were attempted
        mock_mouse.release_all.assert_called_once()
        mock_display.cleanup.assert_called_once()
        mock_camera.release.assert_called_once()
    
    def test_validate_components_success(self):
        """Test component validation when all components are initialized."""
        # Setup all components
        self.app_controller.camera_manager = Mock()
        self.app_controller.pose_detector = Mock()
        self.app_controller.mouse_controller = Mock()
        self.app_controller.display_manager = Mock()
        self.app_controller.angle_calculator = Mock()
        
        result = self.app_controller._validate_components()
        assert result is True
    
    def test_validate_components_missing(self):
        """Test component validation when components are missing."""
        # Leave some components uninitialized
        self.app_controller.camera_manager = Mock()
        # pose_detector is None
        self.app_controller.mouse_controller = Mock()
        # display_manager is None
        self.app_controller.angle_calculator = Mock()
        
        result = self.app_controller._validate_components()
        assert result is False
    
    def test_update_mouse_control_success(self):
        """Test successful mouse control update."""
        mock_mouse = Mock()
        self.app_controller.mouse_controller = mock_mouse
        
        # Test updating to left click
        self.app_controller._update_mouse_control(ControlState.LEFT_CLICK)
        
        mock_mouse.set_state.assert_called_once_with(ControlState.LEFT_CLICK)
        assert self.app_controller.system_state.current_control_state == ControlState.LEFT_CLICK
        assert self.app_controller.system_state.error_count == 0
    
    def test_update_mouse_control_error(self):
        """Test mouse control update with error."""
        mock_mouse = Mock()
        mock_mouse.set_state.side_effect = Exception("Mouse error")
        self.app_controller.mouse_controller = mock_mouse
        
        # Test updating with error
        self.app_controller._update_mouse_control(ControlState.LEFT_CLICK)
        
        mock_mouse.set_state.assert_called_once_with(ControlState.LEFT_CLICK)
        assert self.app_controller.system_state.error_count == 1
    
    def test_update_mouse_control_too_many_errors(self):
        """Test mouse control disables pose control after too many errors."""
        mock_mouse = Mock()
        mock_mouse.set_state.side_effect = Exception("Mouse error")
        self.app_controller.mouse_controller = mock_mouse
        
        # Set error count high
        self.app_controller.system_state.error_count = 5
        
        # Test updating with error
        self.app_controller._update_mouse_control(ControlState.LEFT_CLICK)
        
        assert self.app_controller.system_state.error_count == 6
        assert self.app_controller.system_state.pose_control_enabled is False
    
    def test_set_neutral_state(self):
        """Test setting neutral state."""
        mock_mouse = Mock()
        self.app_controller.mouse_controller = mock_mouse
        self.app_controller.system_state.current_control_state = ControlState.LEFT_CLICK
        
        # Test setting neutral state
        self.app_controller._set_neutral_state()
        
        mock_mouse.set_state.assert_called_once_with(ControlState.NEUTRAL)
        assert self.app_controller.system_state.current_control_state == ControlState.NEUTRAL
    
    def test_set_neutral_state_already_neutral(self):
        """Test setting neutral state when already neutral."""
        mock_mouse = Mock()
        self.app_controller.mouse_controller = mock_mouse
        self.app_controller.system_state.current_control_state = ControlState.NEUTRAL
        
        # Test setting neutral state
        self.app_controller._set_neutral_state()
        
        # Should not call set_state since already neutral
        mock_mouse.set_state.assert_not_called()
    
    def test_handle_keyboard_input_esc(self):
        """Test keyboard input handling for ESC key."""
        mock_display = Mock()
        mock_display.handle_key_input.return_value = 'esc'
        self.app_controller.display_manager = mock_display
        self.app_controller._running = True
        
        # Test ESC key handling
        self.app_controller._handle_keyboard_input()
        
        assert self.app_controller._running is False
    
    def test_handle_keyboard_input_space(self):
        """Test keyboard input handling for SPACE key."""
        mock_display = Mock()
        mock_display.handle_key_input.return_value = 'space'
        self.app_controller.display_manager = mock_display
        
        initial_state = self.app_controller.system_state.pose_control_enabled
        
        # Test SPACE key handling
        self.app_controller._handle_keyboard_input()
        
        assert self.app_controller.system_state.pose_control_enabled != initial_state
    
    def test_handle_keyboard_input_reset(self):
        """Test keyboard input handling for R key (reset)."""
        mock_display = Mock()
        mock_display.handle_key_input.return_value = 'r'
        self.app_controller.display_manager = mock_display
        
        mock_mouse = Mock()
        self.app_controller.mouse_controller = mock_mouse
        
        # Set some error state
        self.app_controller.system_state.error_count = 3
        self.app_controller.system_state.pose_control_enabled = False
        
        # Test R key handling
        self.app_controller._handle_keyboard_input()
        
        assert self.app_controller.system_state.error_count == 0
        assert self.app_controller.system_state.pose_control_enabled is True
        mock_mouse.reset_error_count.assert_called_once()
    
    def test_get_system_status(self):
        """Test getting system status information."""
        # Setup some state
        self.app_controller._running = True
        self.app_controller._frame_count = 100
        self.app_controller.system_state.last_valid_angle = 75.5
        self.app_controller.system_state.error_count = 2
        
        # Setup mock components
        mock_camera = Mock()
        mock_camera.is_available.return_value = True
        self.app_controller.camera_manager = mock_camera
        
        mock_mouse = Mock()
        mock_mouse.is_healthy.return_value = True
        self.app_controller.mouse_controller = mock_mouse
        
        # Test getting status
        status = self.app_controller.get_system_status()
        
        assert status['running'] is True
        assert status['pose_control_enabled'] is True
        assert status['current_control_state'] == 'Neutral'
        assert status['last_valid_angle'] == 75.5
        assert status['error_count'] == 2
        assert status['camera_available'] is True
        assert status['mouse_controller_healthy'] is True
        assert status['frame_count'] == 100
    
    def test_handle_frame_error_camera_unavailable(self):
        """Test handling frame error when camera is unavailable."""
        mock_camera = Mock()
        mock_camera.is_available.return_value = False
        mock_camera.reconnect.return_value = True
        self.app_controller.camera_manager = mock_camera
        
        # Test frame error handling
        result = self.app_controller._handle_frame_error()
        
        assert result is True
        mock_camera.is_available.assert_called_once()
        mock_camera.reconnect.assert_called_once()
    
    def test_handle_frame_error_reconnect_fails(self):
        """Test handling frame error when camera reconnection fails."""
        mock_camera = Mock()
        mock_camera.is_available.return_value = False
        mock_camera.reconnect.return_value = False
        self.app_controller.camera_manager = mock_camera
        
        # Test frame error handling
        result = self.app_controller._handle_frame_error()
        
        assert result is False
        mock_camera.is_available.assert_called_once()
        mock_camera.reconnect.assert_called_once()
    
    def test_handle_frame_error_camera_available(self):
        """Test handling frame error when camera is available."""
        mock_camera = Mock()
        mock_camera.is_available.return_value = True
        self.app_controller.camera_manager = mock_camera
        
        # Test frame error handling
        result = self.app_controller._handle_frame_error()
        
        assert result is True
        mock_camera.is_available.assert_called_once()
        mock_camera.reconnect.assert_not_called()
    
    def test_process_frame_no_camera_frame(self):
        """Test frame processing when camera returns no frame."""
        mock_camera = Mock()
        mock_camera.get_frame.return_value = None
        self.app_controller.camera_manager = mock_camera
        
        result = self.app_controller._process_frame()
        
        assert result is False
        mock_camera.get_frame.assert_called_once()
    
    def test_draw_disabled_indicator(self):
        """Test drawing disabled indicator on frame."""
        # Create a mock frame
        frame = np.zeros((480, 640, 3), dtype=np.uint8)
        
        # Test drawing disabled indicator
        result_frame = self.app_controller._draw_disabled_indicator(frame)
        
        # Should return a frame (even if drawing fails)
        assert result_frame is not None
        assert result_frame.shape == frame.shape