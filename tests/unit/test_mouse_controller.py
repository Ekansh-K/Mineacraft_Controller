"""
Unit tests for MouseController class.

Tests the mouse control functionality with mocked PyAutoGUI calls
to ensure proper state management and error handling.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock

from src.controllers.mouse_controller import MouseController, MouseControlError
from src.models.enums import ControlState


class TestMouseController:
    """Test cases for MouseController class."""
    
    @patch('src.controllers.mouse_controller.pyautogui')
    def test_init_success(self, mock_pyautogui):
        """Test successful MouseController initialization."""
        controller = MouseController()
        
        assert controller.get_current_state() == ControlState.NEUTRAL
        assert controller.is_healthy()
        assert mock_pyautogui.FAILSAFE is False
    
    @patch('src.controllers.mouse_controller.pyautogui', None)
    def test_init_pyautogui_not_available(self):
        """Test initialization failure when PyAutoGUI is not available."""
        with pytest.raises(MouseControlError, match="PyAutoGUI is not available"):
            MouseController()
    
    @patch('src.controllers.mouse_controller.pyautogui')
    def test_set_state_to_left_click(self, mock_pyautogui):
        """Test setting state to LEFT_CLICK from NEUTRAL."""
        controller = MouseController()
        
        controller.set_state(ControlState.LEFT_CLICK)
        
        mock_pyautogui.mouseDown.assert_called_once_with(button='left')
        assert controller.get_current_state() == ControlState.LEFT_CLICK
    
    @patch('src.controllers.mouse_controller.pyautogui')
    def test_set_state_to_right_click(self, mock_pyautogui):
        """Test setting state to RIGHT_CLICK from NEUTRAL."""
        controller = MouseController()
        
        controller.set_state(ControlState.RIGHT_CLICK)
        
        mock_pyautogui.mouseDown.assert_called_once_with(button='right')
        assert controller.get_current_state() == ControlState.RIGHT_CLICK
    
    @patch('src.controllers.mouse_controller.pyautogui')
    def test_set_state_to_neutral_from_left_click(self, mock_pyautogui):
        """Test setting state to NEUTRAL from LEFT_CLICK."""
        controller = MouseController()
        controller._current_state = ControlState.LEFT_CLICK
        
        controller.set_state(ControlState.NEUTRAL)
        
        mock_pyautogui.mouseUp.assert_called_once_with(button='left')
        assert controller.get_current_state() == ControlState.NEUTRAL
    
    @patch('src.controllers.mouse_controller.pyautogui')
    def test_set_state_to_neutral_from_right_click(self, mock_pyautogui):
        """Test setting state to NEUTRAL from RIGHT_CLICK."""
        controller = MouseController()
        controller._current_state = ControlState.RIGHT_CLICK
        
        controller.set_state(ControlState.NEUTRAL)
        
        mock_pyautogui.mouseUp.assert_called_once_with(button='right')
        assert controller.get_current_state() == ControlState.NEUTRAL
    
    @patch('src.controllers.mouse_controller.pyautogui')
    def test_state_transition_left_to_right(self, mock_pyautogui):
        """Test transitioning from LEFT_CLICK to RIGHT_CLICK."""
        controller = MouseController()
        controller._current_state = ControlState.LEFT_CLICK
        
        controller.set_state(ControlState.RIGHT_CLICK)
        
        # Should release left button first, then press right
        mock_pyautogui.mouseUp.assert_called_once_with(button='left')
        mock_pyautogui.mouseDown.assert_called_once_with(button='right')
        assert controller.get_current_state() == ControlState.RIGHT_CLICK
    
    @patch('src.controllers.mouse_controller.pyautogui')
    def test_state_transition_right_to_left(self, mock_pyautogui):
        """Test transitioning from RIGHT_CLICK to LEFT_CLICK."""
        controller = MouseController()
        controller._current_state = ControlState.RIGHT_CLICK
        
        controller.set_state(ControlState.LEFT_CLICK)
        
        # Should release right button first, then press left
        mock_pyautogui.mouseUp.assert_called_once_with(button='right')
        mock_pyautogui.mouseDown.assert_called_once_with(button='left')
        assert controller.get_current_state() == ControlState.LEFT_CLICK
    
    @patch('src.controllers.mouse_controller.pyautogui')
    def test_redundant_state_change_ignored(self, mock_pyautogui):
        """Test that redundant state changes are ignored."""
        controller = MouseController()
        controller.set_state(ControlState.LEFT_CLICK)
        
        # Reset mock to check second call
        mock_pyautogui.reset_mock()
        
        # Set to same state again
        controller.set_state(ControlState.LEFT_CLICK)
        
        # Should not make any mouse calls
        mock_pyautogui.mouseDown.assert_not_called()
        mock_pyautogui.mouseUp.assert_not_called()
    
    @patch('src.controllers.mouse_controller.pyautogui')
    def test_invalid_state_type_raises_error(self, mock_pyautogui):
        """Test that invalid state type raises ValueError."""
        controller = MouseController()
        
        with pytest.raises(ValueError, match="Invalid state type"):
            controller.set_state("invalid_state")
    
    @patch('src.controllers.mouse_controller.pyautogui')
    def test_release_all_from_left_click(self, mock_pyautogui):
        """Test release_all method from LEFT_CLICK state."""
        controller = MouseController()
        controller._current_state = ControlState.LEFT_CLICK
        
        controller.release_all()
        
        # Should release both buttons
        assert mock_pyautogui.mouseUp.call_count == 2
        mock_pyautogui.mouseUp.assert_any_call(button='left')
        mock_pyautogui.mouseUp.assert_any_call(button='right')
        assert controller.get_current_state() == ControlState.NEUTRAL
    
    @patch('src.controllers.mouse_controller.pyautogui')
    def test_release_all_from_right_click(self, mock_pyautogui):
        """Test release_all method from RIGHT_CLICK state."""
        controller = MouseController()
        controller._current_state = ControlState.RIGHT_CLICK
        
        controller.release_all()
        
        # Should release both buttons
        assert mock_pyautogui.mouseUp.call_count == 2
        mock_pyautogui.mouseUp.assert_any_call(button='left')
        mock_pyautogui.mouseUp.assert_any_call(button='right')
        assert controller.get_current_state() == ControlState.NEUTRAL
    
    @patch('src.controllers.mouse_controller.pyautogui')
    def test_mouse_control_error_handling(self, mock_pyautogui):
        """Test error handling when PyAutoGUI operations fail."""
        controller = MouseController()
        mock_pyautogui.mouseDown.side_effect = Exception("Mouse operation failed")
        
        with pytest.raises(MouseControlError, match="Failed to set mouse state"):
            # Try to trigger error multiple times to exceed threshold
            for _ in range(6):  # max_errors is 5
                try:
                    controller.set_state(ControlState.LEFT_CLICK)
                except MouseControlError:
                    pass
            # Final attempt should raise MouseControlError
            controller.set_state(ControlState.LEFT_CLICK)
    
    @patch('src.controllers.mouse_controller.pyautogui')
    def test_error_count_reset_on_success(self, mock_pyautogui):
        """Test that error count resets after successful operation."""
        controller = MouseController()
        
        # Simulate some errors
        mock_pyautogui.mouseDown.side_effect = Exception("Temporary error")
        try:
            controller.set_state(ControlState.LEFT_CLICK)
        except:
            pass
        
        assert controller._error_count > 0
        
        # Now simulate success
        mock_pyautogui.mouseDown.side_effect = None
        controller.set_state(ControlState.RIGHT_CLICK)
        
        assert controller._error_count == 0
        assert controller.is_healthy()
    
    @patch('src.controllers.mouse_controller.pyautogui')
    def test_is_healthy_method(self, mock_pyautogui):
        """Test is_healthy method returns correct status."""
        controller = MouseController()
        
        assert controller.is_healthy()
        
        # Simulate errors
        controller._error_count = 3
        assert controller.is_healthy()
        
        controller._error_count = 5
        assert not controller.is_healthy()
    
    @patch('src.controllers.mouse_controller.pyautogui')
    def test_reset_error_count(self, mock_pyautogui):
        """Test reset_error_count method."""
        controller = MouseController()
        controller._error_count = 5
        
        assert not controller.is_healthy()
        
        controller.reset_error_count()
        
        assert controller._error_count == 0
        assert controller.is_healthy()
    
    @patch('src.controllers.mouse_controller.pyautogui')
    def test_context_manager_usage(self, mock_pyautogui):
        """Test MouseController as context manager."""
        with MouseController() as controller:
            controller.set_state(ControlState.LEFT_CLICK)
        
        # Should call release_all on exit
        assert mock_pyautogui.mouseUp.call_count == 2
    
    @patch('src.controllers.mouse_controller.pyautogui')
    def test_release_all_handles_exceptions(self, mock_pyautogui):
        """Test that release_all handles exceptions gracefully."""
        controller = MouseController()
        mock_pyautogui.mouseUp.side_effect = Exception("Release failed")
        
        # Should not raise exception
        controller.release_all()
        
        # State should still be set to neutral
        assert controller.get_current_state() == ControlState.NEUTRAL
    
    @patch('src.controllers.mouse_controller.pyautogui')
    def test_get_current_state(self, mock_pyautogui):
        """Test get_current_state method."""
        controller = MouseController()
        
        assert controller.get_current_state() == ControlState.NEUTRAL
        
        controller.set_state(ControlState.LEFT_CLICK)
        assert controller.get_current_state() == ControlState.LEFT_CLICK
        
        controller.set_state(ControlState.RIGHT_CLICK)
        assert controller.get_current_state() == ControlState.RIGHT_CLICK
        
        controller.set_state(ControlState.NEUTRAL)
        assert controller.get_current_state() == ControlState.NEUTRAL