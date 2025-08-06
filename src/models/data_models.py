"""
Core data models for the OpenCV Minecraft Controller.

This module defines the fundamental data structures used throughout the application
for representing 3D coordinates, arm keypoints, and system state.
"""

from dataclasses import dataclass
from typing import Optional
from .enums import ControlState


@dataclass
class Point:
    """Represents a 3D coordinate point.
    
    Used for storing pose keypoint coordinates with optional z-depth.
    """
    x: float
    y: float
    z: float = 0.0
    
    def __post_init__(self):
        """Validate coordinate values."""
        if not isinstance(self.x, (int, float)):
            raise TypeError("x coordinate must be a number")
        if not isinstance(self.y, (int, float)):
            raise TypeError("y coordinate must be a number")
        if not isinstance(self.z, (int, float)):
            raise TypeError("z coordinate must be a number")


@dataclass
class ArmKeypoints:
    """Represents the key points of an arm for pose detection.
    
    Contains shoulder, elbow, and wrist coordinates along with confidence score.
    """
    shoulder: Point
    elbow: Point
    wrist: Point
    confidence: float
    
    def __post_init__(self):
        """Validate keypoint data."""
        if not isinstance(self.shoulder, Point):
            raise TypeError("shoulder must be a Point instance")
        if not isinstance(self.elbow, Point):
            raise TypeError("elbow must be a Point instance")
        if not isinstance(self.wrist, Point):
            raise TypeError("wrist must be a Point instance")
        if not isinstance(self.confidence, (int, float)):
            raise TypeError("confidence must be a number")
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError("confidence must be between 0.0 and 1.0")


@dataclass
class SystemState:
    """Represents the current state of the application system.
    
    Tracks pose control status, current control state, and error information.
    """
    pose_control_enabled: bool = True
    current_control_state: ControlState = ControlState.NEUTRAL
    last_valid_angle: Optional[float] = None
    error_count: int = 0
    
    def __post_init__(self):
        """Validate system state data."""
        if not isinstance(self.pose_control_enabled, bool):
            raise TypeError("pose_control_enabled must be a boolean")
        if not isinstance(self.current_control_state, ControlState):
            raise TypeError("current_control_state must be a ControlState enum")
        if self.last_valid_angle is not None and not isinstance(self.last_valid_angle, (int, float)):
            raise TypeError("last_valid_angle must be a number or None")
        if not isinstance(self.error_count, int):
            raise TypeError("error_count must be an integer")
        if self.error_count < 0:
            raise ValueError("error_count must be non-negative")