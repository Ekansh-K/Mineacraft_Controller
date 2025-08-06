"""
Angle calculation utilities for the OpenCV Minecraft Controller.

This module provides functionality to calculate elbow joint angles from arm keypoints
and map those angles to appropriate control states for mouse control.
"""

import numpy as np
from typing import Optional
from ..models import Point, ControlState


class AngleCalculator:
    """Calculates elbow joint angles and maps them to control states.
    
    Uses vector-based calculations to determine the angle between the upper arm
    (shoulder to elbow) and forearm (elbow to wrist) segments.
    """
    
    # Angle thresholds for control state mapping
    RIGHT_CLICK_THRESHOLD = 60.0  # Below this angle triggers right-click
    LEFT_CLICK_THRESHOLD = 90.0   # Above this angle triggers left-click
    HYSTERESIS_MARGIN = 2.0       # Prevents rapid state changes
    
    def __init__(self):
        """Initialize the angle calculator."""
        self._last_state: Optional[ControlState] = None
    
    @staticmethod
    def calculate_elbow_angle(shoulder: Point, elbow: Point, wrist: Point) -> float:
        """Calculate the elbow joint angle using vector mathematics.
        
        Args:
            shoulder: Shoulder keypoint coordinates
            elbow: Elbow keypoint coordinates  
            wrist: Wrist keypoint coordinates
            
        Returns:
            The elbow angle in degrees (0-180)
            
        Raises:
            ValueError: If keypoints form invalid vectors (zero length)
        """
        # Create vectors from elbow to shoulder and elbow to wrist
        upper_arm = np.array([shoulder.x - elbow.x, shoulder.y - elbow.y, shoulder.z - elbow.z])
        forearm = np.array([wrist.x - elbow.x, wrist.y - elbow.y, wrist.z - elbow.z])
        
        # Calculate vector magnitudes
        upper_arm_length = np.linalg.norm(upper_arm)
        forearm_length = np.linalg.norm(forearm)
        
        # Check for zero-length vectors
        if upper_arm_length == 0 or forearm_length == 0:
            raise ValueError("Invalid keypoints: vectors have zero length")
        
        # Normalize vectors
        upper_arm_normalized = upper_arm / upper_arm_length
        forearm_normalized = forearm / forearm_length
        
        # Calculate dot product
        dot_product = np.dot(upper_arm_normalized, forearm_normalized)
        
        # Clamp dot product to valid range for arccos (handle floating point errors)
        dot_product = np.clip(dot_product, -1.0, 1.0)
        
        # Calculate angle in radians and convert to degrees
        angle_radians = np.arccos(dot_product)
        angle_degrees = np.degrees(angle_radians)
        
        return float(angle_degrees)
    
    def get_control_state(self, angle: float) -> ControlState:
        """Map elbow angle to appropriate control state with hysteresis.
        
        Args:
            angle: Elbow angle in degrees
            
        Returns:
            The corresponding control state
        """
        # Apply hysteresis to prevent rapid state changes
        if self._last_state == ControlState.RIGHT_CLICK:
            # When in right-click state, need higher threshold to exit
            right_threshold = self.RIGHT_CLICK_THRESHOLD + self.HYSTERESIS_MARGIN
        else:
            right_threshold = self.RIGHT_CLICK_THRESHOLD
            
        if self._last_state == ControlState.LEFT_CLICK:
            # When in left-click state, need lower threshold to exit
            left_threshold = self.LEFT_CLICK_THRESHOLD - self.HYSTERESIS_MARGIN
        else:
            left_threshold = self.LEFT_CLICK_THRESHOLD
        
        # Determine new state based on angle
        if angle < right_threshold:
            new_state = ControlState.RIGHT_CLICK
        elif angle > left_threshold:
            new_state = ControlState.LEFT_CLICK
        else:
            new_state = ControlState.NEUTRAL
        
        # Update last state and return
        self._last_state = new_state
        return new_state
    
    def is_angle_valid(self, angle: float) -> bool:
        """Check if the calculated angle is within valid range.
        
        Args:
            angle: Angle in degrees to validate
            
        Returns:
            True if angle is valid (0-180 degrees), False otherwise
        """
        return 0.0 <= angle <= 180.0
    
    def reset_state(self) -> None:
        """Reset the internal state tracking for hysteresis."""
        self._last_state = None