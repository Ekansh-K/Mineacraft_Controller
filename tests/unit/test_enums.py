"""
Unit tests for enums.

Tests the ControlState enum for proper values and behavior.
"""

import pytest
from src.models import ControlState


class TestControlState:
    """Test cases for the ControlState enum."""
    
    def test_control_state_values(self):
        """Test ControlState enum has correct values."""
        assert ControlState.NEUTRAL.value == "neutral"
        assert ControlState.LEFT_CLICK.value == "left_click"
        assert ControlState.RIGHT_CLICK.value == "right_click"
    
    def test_control_state_string_representation(self):
        """Test ControlState string representation is human-readable."""
        assert str(ControlState.NEUTRAL) == "Neutral"
        assert str(ControlState.LEFT_CLICK) == "Left Click"
        assert str(ControlState.RIGHT_CLICK) == "Right Click"
    
    def test_control_state_enum_members(self):
        """Test ControlState has exactly three members."""
        members = list(ControlState)
        assert len(members) == 3
        assert ControlState.NEUTRAL in members
        assert ControlState.LEFT_CLICK in members
        assert ControlState.RIGHT_CLICK in members
    
    def test_control_state_equality(self):
        """Test ControlState enum equality comparisons."""
        assert ControlState.NEUTRAL == ControlState.NEUTRAL
        assert ControlState.LEFT_CLICK == ControlState.LEFT_CLICK
        assert ControlState.RIGHT_CLICK == ControlState.RIGHT_CLICK
        
        assert ControlState.NEUTRAL != ControlState.LEFT_CLICK
        assert ControlState.LEFT_CLICK != ControlState.RIGHT_CLICK
        assert ControlState.RIGHT_CLICK != ControlState.NEUTRAL