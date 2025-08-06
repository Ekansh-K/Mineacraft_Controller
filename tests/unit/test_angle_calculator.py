"""
Unit tests for the AngleCalculator class.

Tests angle calculation functionality, control state mapping, and edge cases
using known coordinate values and expected results.
"""

import pytest
import numpy as np
from src.utils.angle_calculator import AngleCalculator
from src.models import Point, ControlState


class TestAngleCalculator:
    """Test cases for AngleCalculator functionality."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.calculator = AngleCalculator()
    
    def test_calculate_elbow_angle_straight_arm(self):
        """Test angle calculation for a straight arm (180 degrees)."""
        # Straight line: shoulder -> elbow -> wrist
        shoulder = Point(0.0, 0.0, 0.0)
        elbow = Point(1.0, 0.0, 0.0)
        wrist = Point(2.0, 0.0, 0.0)
        
        angle = AngleCalculator.calculate_elbow_angle(shoulder, elbow, wrist)
        assert abs(angle - 180.0) < 0.001, f"Expected ~180°, got {angle}°"
    
    def test_calculate_elbow_angle_right_angle(self):
        """Test angle calculation for a 90-degree bend."""
        # Right angle: shoulder at origin, elbow at (1,0), wrist at (1,1)
        shoulder = Point(0.0, 0.0, 0.0)
        elbow = Point(1.0, 0.0, 0.0)
        wrist = Point(1.0, 1.0, 0.0)
        
        angle = AngleCalculator.calculate_elbow_angle(shoulder, elbow, wrist)
        assert abs(angle - 90.0) < 0.001, f"Expected ~90°, got {angle}°"
    
    def test_calculate_elbow_angle_acute_angle(self):
        """Test angle calculation for an acute angle (60 degrees)."""
        # 60-degree angle using equilateral triangle properties
        shoulder = Point(0.0, 0.0, 0.0)
        elbow = Point(1.0, 0.0, 0.0)
        wrist = Point(0.5, np.sqrt(3)/2, 0.0)  # 60° from horizontal
        
        angle = AngleCalculator.calculate_elbow_angle(shoulder, elbow, wrist)
        assert abs(angle - 60.0) < 0.001, f"Expected ~60°, got {angle}°"
    
    def test_calculate_elbow_angle_obtuse_angle(self):
        """Test angle calculation for an obtuse angle (120 degrees)."""
        # 120-degree angle - corrected calculation
        shoulder = Point(0.0, 0.0, 0.0)
        elbow = Point(1.0, 0.0, 0.0)
        wrist = Point(1.5, np.sqrt(3)/2, 0.0)  # 120° angle at elbow
        
        angle = AngleCalculator.calculate_elbow_angle(shoulder, elbow, wrist)
        assert abs(angle - 120.0) < 0.001, f"Expected ~120°, got {angle}°"
    
    def test_calculate_elbow_angle_3d_coordinates(self):
        """Test angle calculation with 3D coordinates."""
        # 90-degree angle in 3D space
        shoulder = Point(0.0, 0.0, 0.0)
        elbow = Point(1.0, 1.0, 0.0)
        wrist = Point(1.0, 1.0, 1.0)
        
        angle = AngleCalculator.calculate_elbow_angle(shoulder, elbow, wrist)
        assert abs(angle - 90.0) < 0.001, f"Expected ~90°, got {angle}°"
    
    def test_calculate_elbow_angle_zero_length_vector_shoulder_elbow(self):
        """Test error handling for zero-length shoulder-elbow vector."""
        # Same point for shoulder and elbow
        shoulder = Point(1.0, 1.0, 1.0)
        elbow = Point(1.0, 1.0, 1.0)
        wrist = Point(2.0, 2.0, 2.0)
        
        with pytest.raises(ValueError, match="Invalid keypoints: vectors have zero length"):
            AngleCalculator.calculate_elbow_angle(shoulder, elbow, wrist)
    
    def test_calculate_elbow_angle_zero_length_vector_elbow_wrist(self):
        """Test error handling for zero-length elbow-wrist vector."""
        # Same point for elbow and wrist
        shoulder = Point(0.0, 0.0, 0.0)
        elbow = Point(1.0, 1.0, 1.0)
        wrist = Point(1.0, 1.0, 1.0)
        
        with pytest.raises(ValueError, match="Invalid keypoints: vectors have zero length"):
            AngleCalculator.calculate_elbow_angle(shoulder, elbow, wrist)
    
    def test_get_control_state_right_click(self):
        """Test control state mapping for right-click angle."""
        # Angle below 60 degrees should trigger right-click
        state = self.calculator.get_control_state(45.0)
        assert state == ControlState.RIGHT_CLICK
    
    def test_get_control_state_left_click(self):
        """Test control state mapping for left-click angle."""
        # Angle above 90 degrees should trigger left-click
        state = self.calculator.get_control_state(120.0)
        assert state == ControlState.LEFT_CLICK
    
    def test_get_control_state_neutral(self):
        """Test control state mapping for neutral angle."""
        # Angle between 60-90 degrees should be neutral
        state = self.calculator.get_control_state(75.0)
        assert state == ControlState.NEUTRAL
    
    def test_get_control_state_boundary_conditions(self):
        """Test control state mapping at boundary angles."""
        # Test exact threshold values
        state_60 = self.calculator.get_control_state(60.0)
        state_90 = self.calculator.get_control_state(90.0)
        
        # At exactly 60°, should be neutral (not right-click)
        assert state_60 == ControlState.NEUTRAL
        # At exactly 90°, should be neutral (not left-click)  
        assert state_90 == ControlState.NEUTRAL
    
    def test_get_control_state_hysteresis_right_click(self):
        """Test hysteresis behavior when transitioning from right-click."""
        # Start in right-click state
        self.calculator.get_control_state(50.0)  # Right-click
        
        # Angle just above normal threshold should still be right-click due to hysteresis
        state = self.calculator.get_control_state(61.0)  # 60 + 2 (hysteresis) = 62, so 61 should still be right-click
        assert state == ControlState.RIGHT_CLICK
        
        # Angle above hysteresis threshold should transition to neutral
        state = self.calculator.get_control_state(63.0)
        assert state == ControlState.NEUTRAL
    
    def test_get_control_state_hysteresis_left_click(self):
        """Test hysteresis behavior when transitioning from left-click."""
        # Start in left-click state
        self.calculator.get_control_state(120.0)  # Left-click
        
        # Angle just below normal threshold should still be left-click due to hysteresis
        state = self.calculator.get_control_state(89.0)  # 90 - 2 (hysteresis) = 88, so 89 should still be left-click
        assert state == ControlState.LEFT_CLICK
        
        # Angle below hysteresis threshold should transition to neutral
        state = self.calculator.get_control_state(87.0)
        assert state == ControlState.NEUTRAL
    
    def test_is_angle_valid_valid_angles(self):
        """Test angle validation for valid angles."""
        assert self.calculator.is_angle_valid(0.0) is True
        assert self.calculator.is_angle_valid(90.0) is True
        assert self.calculator.is_angle_valid(180.0) is True
        assert self.calculator.is_angle_valid(45.5) is True
    
    def test_is_angle_valid_invalid_angles(self):
        """Test angle validation for invalid angles."""
        assert self.calculator.is_angle_valid(-1.0) is False
        assert self.calculator.is_angle_valid(181.0) is False
        assert self.calculator.is_angle_valid(-45.0) is False
        assert self.calculator.is_angle_valid(270.0) is False
    
    def test_reset_state(self):
        """Test state reset functionality."""
        # Set a state
        self.calculator.get_control_state(50.0)  # Right-click
        
        # Reset state
        self.calculator.reset_state()
        
        # Verify hysteresis no longer applies
        state = self.calculator.get_control_state(61.0)
        assert state == ControlState.NEUTRAL  # Should be neutral without hysteresis
    
    def test_state_transitions_sequence(self):
        """Test a sequence of state transitions."""
        # Start neutral
        state1 = self.calculator.get_control_state(75.0)
        assert state1 == ControlState.NEUTRAL
        
        # Move to right-click
        state2 = self.calculator.get_control_state(45.0)
        assert state2 == ControlState.RIGHT_CLICK
        
        # Move to left-click
        state3 = self.calculator.get_control_state(120.0)
        assert state3 == ControlState.LEFT_CLICK
        
        # Back to neutral
        state4 = self.calculator.get_control_state(75.0)
        assert state4 == ControlState.NEUTRAL


class TestAngleCalculatorEdgeCases:
    """Test edge cases and error conditions."""
    
    def test_very_small_angles(self):
        """Test calculation with very small angles."""
        # Nearly straight arm (179 degrees)
        shoulder = Point(0.0, 0.0, 0.0)
        elbow = Point(1.0, 0.0, 0.0)
        wrist = Point(2.0, 0.01, 0.0)  # Very slight bend
        
        angle = AngleCalculator.calculate_elbow_angle(shoulder, elbow, wrist)
        assert 179.0 < angle < 180.0
    
    def test_floating_point_precision(self):
        """Test handling of floating-point precision issues."""
        # Use coordinates that might cause floating-point errors
        shoulder = Point(0.1, 0.1, 0.1)
        elbow = Point(0.7, 0.7, 0.7)
        wrist = Point(1.3, 1.3, 1.3)
        
        angle = AngleCalculator.calculate_elbow_angle(shoulder, elbow, wrist)
        assert abs(angle - 180.0) < 0.001
    
    def test_negative_coordinates(self):
        """Test calculation with negative coordinates."""
        shoulder = Point(-1.0, 0.0, 0.0)
        elbow = Point(0.0, 0.0, 0.0)
        wrist = Point(0.0, 1.0, 0.0)
        
        angle = AngleCalculator.calculate_elbow_angle(shoulder, elbow, wrist)
        assert abs(angle - 90.0) < 0.001