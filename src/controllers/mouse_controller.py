"""
Mouse Controller for OpenCV Minecraft Controller.

This module provides the MouseController class that manages mouse button states
based on pose detection results. It uses PyAutoGUI to execute mouse commands
and includes state tracking to avoid redundant operations.
"""

import logging
from typing import Optional

try:
    import pyautogui
except ImportError:
    pyautogui = None

from ..models.enums import ControlState


logger = logging.getLogger(__name__)


class MouseControlError(Exception):
    """Exception raised when mouse control operations fail."""
    pass


class MouseController:
    """Manages mouse button states based on control commands.
    
    This class handles mouse button press/hold/release operations using PyAutoGUI,
    maintains current state to avoid redundant commands, and provides error
    handling for mouse control failures.
    """
    
    def __init__(self):
        """Initialize the MouseController.
        
        Raises:
            MouseControlError: If PyAutoGUI is not available or fails to initialize.
        """
        if pyautogui is None:
            raise MouseControlError("PyAutoGUI is not available. Please install it with: pip install pyautogui")
        
        # Disable PyAutoGUI fail-safe (moving mouse to corner stops program)
        # This is important for gaming applications
        pyautogui.FAILSAFE = False
        
        self._current_state = ControlState.NEUTRAL
        self._error_count = 0
        self._max_errors = 5
        
        logger.info("MouseController initialized successfully")
    
    def set_state(self, state: ControlState) -> None:
        """Set the mouse control state.
        
        Updates the mouse button state based on the provided control state.
        Avoids redundant commands by checking current state first.
        
        Args:
            state: The desired control state (NEUTRAL, LEFT_CLICK, RIGHT_CLICK)
            
        Raises:
            MouseControlError: If mouse control operations fail repeatedly
        """
        if not isinstance(state, ControlState):
            raise ValueError(f"Invalid state type: {type(state)}. Expected ControlState.")
        
        # Avoid redundant commands
        if state == self._current_state:
            return
        
        try:
            self._transition_to_state(state)
            self._current_state = state
            self._error_count = 0  # Reset error count on successful operation
            
            logger.debug(f"Mouse state changed to: {state}")
            
        except Exception as e:
            self._error_count += 1
            error_msg = f"Failed to set mouse state to {state}: {e}"
            logger.error(error_msg)
            
            if self._error_count >= self._max_errors:
                raise MouseControlError(f"Too many mouse control errors ({self._error_count}). Last error: {error_msg}")
    
    def _transition_to_state(self, new_state: ControlState) -> None:
        """Perform the actual mouse state transition.
        
        Args:
            new_state: The target control state
            
        Raises:
            Exception: If PyAutoGUI operations fail
        """
        # First, release any currently pressed buttons
        if self._current_state == ControlState.LEFT_CLICK:
            pyautogui.mouseUp(button='left')
        elif self._current_state == ControlState.RIGHT_CLICK:
            pyautogui.mouseUp(button='right')
        
        # Then, press the new button if needed
        if new_state == ControlState.LEFT_CLICK:
            pyautogui.mouseDown(button='left')
        elif new_state == ControlState.RIGHT_CLICK:
            pyautogui.mouseDown(button='right')
        # NEUTRAL state requires no additional action after releasing buttons
    
    def release_all(self) -> None:
        """Release all mouse buttons and set state to neutral.
        
        This method ensures all mouse buttons are released, useful for
        cleanup or emergency stop situations.
        """
        try:
            pyautogui.mouseUp(button='left')
            pyautogui.mouseUp(button='right')
            self._current_state = ControlState.NEUTRAL
            self._error_count = 0
            
            logger.info("All mouse buttons released")
            
        except Exception as e:
            logger.error(f"Failed to release mouse buttons: {e}")
            # Don't raise exception here as this is often called during cleanup
    
    def get_current_state(self) -> ControlState:
        """Get the current mouse control state.
        
        Returns:
            The current control state
        """
        return self._current_state
    
    def is_healthy(self) -> bool:
        """Check if the mouse controller is in a healthy state.
        
        Returns:
            True if error count is below threshold, False otherwise
        """
        return self._error_count < self._max_errors
    
    def reset_error_count(self) -> None:
        """Reset the error counter.
        
        Useful for recovery scenarios where errors were temporary.
        """
        self._error_count = 0
        logger.info("Mouse controller error count reset")
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit - ensure all buttons are released."""
        self.release_all()