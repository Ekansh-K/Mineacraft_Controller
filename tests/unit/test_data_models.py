"""
Unit tests for data models.

Tests the Point, ArmKeypoints, and SystemState dataclasses for proper
validation and behavior.
"""

import pytest
from src.models import Point, ArmKeypoints, SystemState, ControlState


class TestPoint:
    """Test cases for the Point dataclass."""
    
    def test_point_creation_with_defaults(self):
        """Test creating a Point with default z coordinate."""
        point = Point(x=10.5, y=20.3)
        assert point.x == 10.5
        assert point.y == 20.3
        assert point.z == 0.0
    
    def test_point_creation_with_z(self):
        """Test creating a Point with explicit z coordinate."""
        point = Point(x=1.0, y=2.0, z=3.0)
        assert point.x == 1.0
        assert point.y == 2.0
        assert point.z == 3.0
    
    def test_point_with_integers(self):
        """Test Point accepts integer coordinates."""
        point = Point(x=1, y=2, z=3)
        assert point.x == 1
        assert point.y == 2
        assert point.z == 3
    
    def test_point_invalid_x_type(self):
        """Test Point raises TypeError for invalid x coordinate type."""
        with pytest.raises(TypeError, match="x coordinate must be a number"):
            Point(x="invalid", y=1.0)
    
    def test_point_invalid_y_type(self):
        """Test Point raises TypeError for invalid y coordinate type."""
        with pytest.raises(TypeError, match="y coordinate must be a number"):
            Point(x=1.0, y="invalid")
    
    def test_point_invalid_z_type(self):
        """Test Point raises TypeError for invalid z coordinate type."""
        with pytest.raises(TypeError, match="z coordinate must be a number"):
            Point(x=1.0, y=2.0, z="invalid")


class TestArmKeypoints:
    """Test cases for the ArmKeypoints dataclass."""
    
    def test_arm_keypoints_creation(self):
        """Test creating ArmKeypoints with valid data."""
        shoulder = Point(1.0, 2.0, 3.0)
        elbow = Point(4.0, 5.0, 6.0)
        wrist = Point(7.0, 8.0, 9.0)
        confidence = 0.85
        
        keypoints = ArmKeypoints(
            shoulder=shoulder,
            elbow=elbow,
            wrist=wrist,
            confidence=confidence
        )
        
        assert keypoints.shoulder == shoulder
        assert keypoints.elbow == elbow
        assert keypoints.wrist == wrist
        assert keypoints.confidence == confidence
    
    def test_arm_keypoints_confidence_bounds(self):
        """Test ArmKeypoints accepts confidence values within valid range."""
        shoulder = Point(1.0, 2.0)
        elbow = Point(4.0, 5.0)
        wrist = Point(7.0, 8.0)
        
        # Test minimum confidence
        keypoints_min = ArmKeypoints(shoulder, elbow, wrist, 0.0)
        assert keypoints_min.confidence == 0.0
        
        # Test maximum confidence
        keypoints_max = ArmKeypoints(shoulder, elbow, wrist, 1.0)
        assert keypoints_max.confidence == 1.0
    
    def test_arm_keypoints_invalid_shoulder_type(self):
        """Test ArmKeypoints raises TypeError for invalid shoulder type."""
        with pytest.raises(TypeError, match="shoulder must be a Point instance"):
            ArmKeypoints(
                shoulder="invalid",
                elbow=Point(1.0, 2.0),
                wrist=Point(3.0, 4.0),
                confidence=0.5
            )
    
    def test_arm_keypoints_invalid_elbow_type(self):
        """Test ArmKeypoints raises TypeError for invalid elbow type."""
        with pytest.raises(TypeError, match="elbow must be a Point instance"):
            ArmKeypoints(
                shoulder=Point(1.0, 2.0),
                elbow="invalid",
                wrist=Point(3.0, 4.0),
                confidence=0.5
            )
    
    def test_arm_keypoints_invalid_wrist_type(self):
        """Test ArmKeypoints raises TypeError for invalid wrist type."""
        with pytest.raises(TypeError, match="wrist must be a Point instance"):
            ArmKeypoints(
                shoulder=Point(1.0, 2.0),
                elbow=Point(3.0, 4.0),
                wrist="invalid",
                confidence=0.5
            )
    
    def test_arm_keypoints_invalid_confidence_type(self):
        """Test ArmKeypoints raises TypeError for invalid confidence type."""
        with pytest.raises(TypeError, match="confidence must be a number"):
            ArmKeypoints(
                shoulder=Point(1.0, 2.0),
                elbow=Point(3.0, 4.0),
                wrist=Point(5.0, 6.0),
                confidence="invalid"
            )
    
    def test_arm_keypoints_confidence_below_range(self):
        """Test ArmKeypoints raises ValueError for confidence below 0.0."""
        with pytest.raises(ValueError, match="confidence must be between 0.0 and 1.0"):
            ArmKeypoints(
                shoulder=Point(1.0, 2.0),
                elbow=Point(3.0, 4.0),
                wrist=Point(5.0, 6.0),
                confidence=-0.1
            )
    
    def test_arm_keypoints_confidence_above_range(self):
        """Test ArmKeypoints raises ValueError for confidence above 1.0."""
        with pytest.raises(ValueError, match="confidence must be between 0.0 and 1.0"):
            ArmKeypoints(
                shoulder=Point(1.0, 2.0),
                elbow=Point(3.0, 4.0),
                wrist=Point(5.0, 6.0),
                confidence=1.1
            )


class TestSystemState:
    """Test cases for the SystemState dataclass."""
    
    def test_system_state_creation_with_defaults(self):
        """Test creating SystemState with default values."""
        state = SystemState()
        assert state.pose_control_enabled is True
        assert state.current_control_state == ControlState.NEUTRAL
        assert state.last_valid_angle is None
        assert state.error_count == 0
    
    def test_system_state_creation_with_values(self):
        """Test creating SystemState with explicit values."""
        state = SystemState(
            pose_control_enabled=False,
            current_control_state=ControlState.LEFT_CLICK,
            last_valid_angle=75.5,
            error_count=3
        )
        assert state.pose_control_enabled is False
        assert state.current_control_state == ControlState.LEFT_CLICK
        assert state.last_valid_angle == 75.5
        assert state.error_count == 3
    
    def test_system_state_invalid_pose_control_type(self):
        """Test SystemState raises TypeError for invalid pose_control_enabled type."""
        with pytest.raises(TypeError, match="pose_control_enabled must be a boolean"):
            SystemState(pose_control_enabled="invalid")
    
    def test_system_state_invalid_control_state_type(self):
        """Test SystemState raises TypeError for invalid current_control_state type."""
        with pytest.raises(TypeError, match="current_control_state must be a ControlState enum"):
            SystemState(current_control_state="invalid")
    
    def test_system_state_invalid_angle_type(self):
        """Test SystemState raises TypeError for invalid last_valid_angle type."""
        with pytest.raises(TypeError, match="last_valid_angle must be a number or None"):
            SystemState(last_valid_angle="invalid")
    
    def test_system_state_valid_angle_none(self):
        """Test SystemState accepts None for last_valid_angle."""
        state = SystemState(last_valid_angle=None)
        assert state.last_valid_angle is None
    
    def test_system_state_valid_angle_number(self):
        """Test SystemState accepts numeric values for last_valid_angle."""
        state = SystemState(last_valid_angle=45.0)
        assert state.last_valid_angle == 45.0
        
        state_int = SystemState(last_valid_angle=90)
        assert state_int.last_valid_angle == 90
    
    def test_system_state_invalid_error_count_type(self):
        """Test SystemState raises TypeError for invalid error_count type."""
        with pytest.raises(TypeError, match="error_count must be an integer"):
            SystemState(error_count="invalid")
    
    def test_system_state_negative_error_count(self):
        """Test SystemState raises ValueError for negative error_count."""
        with pytest.raises(ValueError, match="error_count must be non-negative"):
            SystemState(error_count=-1)