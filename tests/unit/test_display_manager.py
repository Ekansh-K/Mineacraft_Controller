"""
Unit tests for the DisplayManager class.

Tests all display rendering functions including pose overlay, angle display,
control state indicators, and window management.
"""

import pytest
import numpy as np
from unittest.mock import Mock, patch, call
from src.controllers.display_manager import DisplayManager
from src.models.data_models import ArmKeypoints, Point
from src.models.enums import ControlState


class TestDisplayManager:
    """Test cases for DisplayManager class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.display_manager = DisplayManager("Test Window")
        
        # Create test frame (480x640x3 BGR image)
        self.test_frame = np.zeros((480, 640, 3), dtype=np.uint8)
        
        # Create test keypoints
        self.test_keypoints = ArmKeypoints(
            shoulder=Point(0.3, 0.2, 0.0),
            elbow=Point(0.5, 0.4, 0.0),
            wrist=Point(0.7, 0.6, 0.0),
            confidence=0.8
        )
    
    def test_init(self):
        """Test DisplayManager initialization."""
        dm = DisplayManager("Custom Window")
        assert dm.window_name == "Custom Window"
        assert not dm._window_created
        assert dm.font_scale == 0.7
        assert dm.font_thickness == 2
        
        # Test default window name
        dm_default = DisplayManager()
        assert dm_default.window_name == "OpenCV Minecraft Controller"
    
    def test_colors_defined(self):
        """Test that all required colors are defined."""
        required_colors = [
            'skeleton', 'joints', 'elbow_highlight', 'text_bg', 'text_fg',
            'neutral', 'left_click', 'right_click'
        ]
        
        for color in required_colors:
            assert color in self.display_manager.colors
            assert isinstance(self.display_manager.colors[color], tuple)
            assert len(self.display_manager.colors[color]) == 3
    
    @patch('cv2.namedWindow')
    def test_ensure_window_created(self, mock_named_window):
        """Test window creation."""
        # Initially window should not be created
        assert not self.display_manager._window_created
        
        # Call private method to create window
        self.display_manager._ensure_window_created()
        
        # Verify window was created
        assert self.display_manager._window_created
        mock_named_window.assert_called_once_with("Test Window", 1)  # cv2.WINDOW_AUTOSIZE = 1
        
        # Calling again should not create window again
        mock_named_window.reset_mock()
        self.display_manager._ensure_window_created()
        mock_named_window.assert_not_called()
    
    def test_point_to_pixel(self):
        """Test conversion from normalized coordinates to pixel coordinates."""
        point = Point(0.5, 0.3, 0.0)
        width, height = 640, 480
        
        pixel_x, pixel_y = self.display_manager._point_to_pixel(point, width, height)
        
        assert pixel_x == 320  # 0.5 * 640
        assert pixel_y == 144  # 0.3 * 480
        
        # Test edge cases
        point_origin = Point(0.0, 0.0, 0.0)
        px_x, px_y = self.display_manager._point_to_pixel(point_origin, width, height)
        assert px_x == 0
        assert px_y == 0
        
        point_max = Point(1.0, 1.0, 0.0)
        px_x, px_y = self.display_manager._point_to_pixel(point_max, width, height)
        assert px_x == 640
        assert px_y == 480
    
    def test_get_state_color(self):
        """Test state color mapping."""
        neutral_color = self.display_manager._get_state_color(ControlState.NEUTRAL)
        left_color = self.display_manager._get_state_color(ControlState.LEFT_CLICK)
        right_color = self.display_manager._get_state_color(ControlState.RIGHT_CLICK)
        
        assert neutral_color == self.display_manager.colors['neutral']
        assert left_color == self.display_manager.colors['left_click']
        assert right_color == self.display_manager.colors['right_click']
    
    def test_get_state_label(self):
        """Test state label mapping."""
        assert self.display_manager._get_state_label(ControlState.NEUTRAL) == "NEUTRAL"
        assert self.display_manager._get_state_label(ControlState.LEFT_CLICK) == "LEFT"
        assert self.display_manager._get_state_label(ControlState.RIGHT_CLICK) == "RIGHT"
    
    @patch('cv2.line')
    @patch('cv2.circle')
    def test_draw_pose_overlay(self, mock_circle, mock_line):
        """Test pose skeleton overlay drawing."""
        result_frame = self.display_manager.draw_pose_overlay(self.test_frame, self.test_keypoints)
        
        # Verify frame is returned
        assert result_frame is not None
        assert result_frame.shape == self.test_frame.shape
        
        # Verify skeleton lines are drawn (shoulder-elbow, elbow-wrist)
        assert mock_line.call_count == 2
        
        # Verify joint circles are drawn (shoulder, elbow highlight, elbow border, wrist)
        assert mock_circle.call_count == 4
        
        # Test with None keypoints
        result_none = self.display_manager.draw_pose_overlay(self.test_frame, None)
        assert result_none is not None
    
    def test_draw_pose_overlay_invalid_frame(self):
        """Test pose overlay with invalid frame."""
        with pytest.raises(ValueError, match="Frame cannot be None"):
            self.display_manager.draw_pose_overlay(None, self.test_keypoints)
    
    @patch('cv2.putText')
    @patch('cv2.rectangle')
    @patch('cv2.getTextSize')
    def test_draw_angle_info(self, mock_get_text_size, mock_rectangle, mock_put_text):
        """Test angle and control state information display."""
        # Mock text size calculation
        mock_get_text_size.return_value = ((100, 20), 5)
        
        angle = 75.5
        state = ControlState.NEUTRAL
        
        result_frame = self.display_manager.draw_angle_info(self.test_frame, angle, state)
        
        # Verify frame is returned
        assert result_frame is not None
        assert result_frame.shape == self.test_frame.shape
        
        # Verify text size was calculated
        assert mock_get_text_size.call_count == 2
        
        # Verify background rectangles are drawn
        assert mock_rectangle.call_count == 2
        
        # Verify text is drawn (angle and state)
        assert mock_put_text.call_count == 2
        
        # Check that angle text contains the angle value
        angle_call = mock_put_text.call_args_list[0]
        assert "75.5" in angle_call[0][1]  # Second argument is the text
    
    def test_draw_angle_info_invalid_frame(self):
        """Test angle info with invalid frame."""
        with pytest.raises(ValueError, match="Frame cannot be None"):
            self.display_manager.draw_angle_info(None, 45.0, ControlState.NEUTRAL)
    
    @patch('cv2.putText')
    @patch('cv2.rectangle')
    @patch('cv2.circle')
    @patch('cv2.getTextSize')
    def test_draw_control_state_indicator(self, mock_get_text_size, mock_circle, mock_rectangle, mock_put_text):
        """Test control state visual indicator."""
        # Mock text size calculation
        mock_get_text_size.return_value = ((50, 15), 3)
        
        state = ControlState.LEFT_CLICK
        
        result_frame = self.display_manager.draw_control_state_indicator(self.test_frame, state)
        
        # Verify frame is returned
        assert result_frame is not None
        assert result_frame.shape == self.test_frame.shape
        
        # Verify indicator circle is drawn (filled + border)
        assert mock_circle.call_count == 2
        
        # Verify label background rectangle is drawn
        assert mock_rectangle.call_count == 1
        
        # Verify label text is drawn
        assert mock_put_text.call_count == 1
        
        # Check that label text is correct
        label_call = mock_put_text.call_args_list[0]
        assert "LEFT" in label_call[0][1]
    
    def test_draw_control_state_indicator_invalid_frame(self):
        """Test control state indicator with invalid frame."""
        with pytest.raises(ValueError, match="Frame cannot be None"):
            self.display_manager.draw_control_state_indicator(None, ControlState.NEUTRAL)
    
    @patch('cv2.imshow')
    @patch('cv2.namedWindow')
    def test_show_frame(self, mock_named_window, mock_imshow):
        """Test frame display."""
        self.display_manager.show_frame(self.test_frame)
        
        # Verify window was created
        mock_named_window.assert_called_once()
        
        # Verify frame was displayed
        mock_imshow.assert_called_once_with("Test Window", self.test_frame)
    
    def test_show_frame_invalid_frame(self):
        """Test show frame with invalid frame."""
        with pytest.raises(ValueError, match="Frame cannot be None"):
            self.display_manager.show_frame(None)
    
    @patch('cv2.waitKey')
    def test_handle_key_input(self, mock_wait_key):
        """Test keyboard input handling."""
        # Test no key pressed
        mock_wait_key.return_value = 255
        assert self.display_manager.handle_key_input() is None
        
        # Test ESC key
        mock_wait_key.return_value = 27
        assert self.display_manager.handle_key_input() == 'esc'
        
        # Test space key
        mock_wait_key.return_value = ord(' ')
        assert self.display_manager.handle_key_input() == 'space'
        
        # Test Q key
        mock_wait_key.return_value = ord('q')
        assert self.display_manager.handle_key_input() == 'q'
        
        # Test regular character
        mock_wait_key.return_value = ord('a')
        assert self.display_manager.handle_key_input() == 'a'
        
        # Test non-printable character
        mock_wait_key.return_value = 1  # Non-printable
        assert self.display_manager.handle_key_input() is None
    
    @patch('cv2.destroyWindow')
    def test_cleanup(self, mock_destroy_window):
        """Test cleanup of OpenCV resources."""
        # Set window as created
        self.display_manager._window_created = True
        
        self.display_manager.cleanup()
        
        # Verify window was destroyed
        mock_destroy_window.assert_called_once_with("Test Window")
        assert not self.display_manager._window_created
        
        # Test cleanup when window not created
        mock_destroy_window.reset_mock()
        self.display_manager.cleanup()
        mock_destroy_window.assert_not_called()


class TestDisplayManagerIntegration:
    """Integration tests for DisplayManager with real OpenCV operations."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.display_manager = DisplayManager("Integration Test")
        self.test_frame = np.ones((480, 640, 3), dtype=np.uint8) * 128  # Gray frame
        
        self.test_keypoints = ArmKeypoints(
            shoulder=Point(0.2, 0.3, 0.0),
            elbow=Point(0.5, 0.5, 0.0),
            wrist=Point(0.8, 0.7, 0.0),
            confidence=0.9
        )
    
    def test_full_overlay_pipeline(self):
        """Test complete overlay rendering pipeline."""
        # Start with base frame
        result_frame = self.test_frame.copy()
        
        # Apply pose overlay
        result_frame = self.display_manager.draw_pose_overlay(result_frame, self.test_keypoints)
        
        # Apply angle info
        result_frame = self.display_manager.draw_angle_info(result_frame, 67.5, ControlState.NEUTRAL)
        
        # Apply control state indicator
        result_frame = self.display_manager.draw_control_state_indicator(result_frame, ControlState.NEUTRAL)
        
        # Verify frame dimensions are preserved
        assert result_frame.shape == self.test_frame.shape
        
        # Verify frame was modified (not identical to original)
        assert not np.array_equal(result_frame, self.test_frame)
    
    def test_different_control_states(self):
        """Test rendering with different control states."""
        states_to_test = [ControlState.NEUTRAL, ControlState.LEFT_CLICK, ControlState.RIGHT_CLICK]
        
        for state in states_to_test:
            result_frame = self.display_manager.draw_angle_info(self.test_frame, 45.0, state)
            result_frame = self.display_manager.draw_control_state_indicator(result_frame, state)
            
            # Verify frame is valid
            assert result_frame.shape == self.test_frame.shape
            assert result_frame.dtype == np.uint8
    
    def test_edge_case_coordinates(self):
        """Test with edge case keypoint coordinates."""
        # Test with coordinates at frame edges
        edge_keypoints = ArmKeypoints(
            shoulder=Point(0.0, 0.0, 0.0),
            elbow=Point(0.5, 0.5, 0.0),
            wrist=Point(1.0, 1.0, 0.0),
            confidence=0.7
        )
        
        result_frame = self.display_manager.draw_pose_overlay(self.test_frame, edge_keypoints)
        
        # Should not raise exceptions and should return valid frame
        assert result_frame.shape == self.test_frame.shape
        assert result_frame.dtype == np.uint8