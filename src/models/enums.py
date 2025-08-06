"""
Enums for the OpenCV Minecraft Controller.

This module defines the enumeration types used throughout the application
for representing control states and system states.
"""

from enum import Enum


class ControlState(Enum):
    """Represents the current mouse control state based on arm position.
    
    Maps to specific mouse button actions:
    - NEUTRAL: No mouse buttons pressed
    - LEFT_CLICK: Left mouse button held down
    - RIGHT_CLICK: Right mouse button held down
    """
    NEUTRAL = "neutral"
    LEFT_CLICK = "left_click"
    RIGHT_CLICK = "right_click"
    
    def __str__(self) -> str:
        """Return human-readable string representation."""
        return self.value.replace("_", " ").title()