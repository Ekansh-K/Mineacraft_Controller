"""
Display Manager for the OpenCV Minecraft Controller.

This module handles all visual feedback including pose overlay, angle display,
and control state indicators using OpenCV for window management and rendering.
"""

import cv2
import numpy as np
from typing import Optional, Tuple
from ..models.data_models import ArmKeypoints, Point
from ..models.enums import ControlState


class DisplayManager:
    """Manages visual feedback and display for the pose detection system.
    
    Handles OpenCV window management, pose skeleton overlay drawing,
    angle and control state information display.
    """
    
    def __init__(self, window_name: str = "OpenCV Minecraft Controller"):
        """Initialize the display manager.
        
        Args:
            window_name: Name of the OpenCV window
        """
        self.window_name = window_name
        self._window_created = False
        
        # Display colors (BGR format for OpenCV)
        self.colors = {
            'skeleton': (0, 255, 0),      # Green for pose skeleton
            'joints': (0, 0, 255),        # Red for joint points
            'elbow_highlight': (255, 0, 255),  # Magenta for elbow
            'text_bg': (0, 0, 0),         # Black background for text
            'text_fg': (255, 255, 255),   # White text
            'neutral': (255, 255, 0),     # Cyan for neutral state
            'left_click': (0, 255, 0),    # Green for left click
            'right_click': (0, 0, 255),   # Red for right click
        }
        
        # Text settings
        self.font = cv2.FONT_HERSHEY_SIMPLEX
        self.font_scale = 0.7
        self.font_thickness = 2
        self.text_padding = 10
    
    def _ensure_window_created(self) -> None:
        """Ensure the OpenCV window is created."""
        if not self._window_created:
            cv2.namedWindow(self.window_name, cv2.WINDOW_AUTOSIZE)
            self._window_created = True
    
    def draw_pose_overlay(self, frame: np.ndarray, keypoints: ArmKeypoints) -> np.ndarray:
        """Draw pose skeleton overlay on the video frame.
        
        Args:
            frame: Input video frame
            keypoints: Detected arm keypoints
            
        Returns:
            Frame with pose overlay drawn
        """
        if frame is None:
            raise ValueError("Frame cannot be None")
        if keypoints is None:
            return frame.copy()
        
        overlay_frame = frame.copy()
        
        # Convert normalized coordinates to pixel coordinates
        height, width = frame.shape[:2]
        
        shoulder_px = self._point_to_pixel(keypoints.shoulder, width, height)
        elbow_px = self._point_to_pixel(keypoints.elbow, width, height)
        wrist_px = self._point_to_pixel(keypoints.wrist, width, height)
        
        # Draw skeleton lines
        cv2.line(overlay_frame, shoulder_px, elbow_px, self.colors['skeleton'], 3)
        cv2.line(overlay_frame, elbow_px, wrist_px, self.colors['skeleton'], 3)
        
        # Draw joint points
        cv2.circle(overlay_frame, shoulder_px, 8, self.colors['joints'], -1)
        cv2.circle(overlay_frame, wrist_px, 8, self.colors['joints'], -1)
        
        # Highlight elbow joint (being tracked)
        cv2.circle(overlay_frame, elbow_px, 12, self.colors['elbow_highlight'], -1)
        cv2.circle(overlay_frame, elbow_px, 12, self.colors['joints'], 2)
        
        return overlay_frame
    
    def draw_angle_info(self, frame: np.ndarray, angle: float, state: ControlState) -> np.ndarray:
        """Draw angle and control state information on the frame.
        
        Args:
            frame: Input video frame
            angle: Current elbow angle in degrees
            state: Current control state
            
        Returns:
            Frame with angle and state information drawn
        """
        if frame is None:
            raise ValueError("Frame cannot be None")
        
        info_frame = frame.copy()
        
        # Prepare text information
        angle_text = f"Elbow Angle: {angle:.1f}°"
        state_text = f"Control State: {str(state)}"
        
        # Get text sizes for background rectangles
        angle_size = cv2.getTextSize(angle_text, self.font, self.font_scale, self.font_thickness)[0]
        state_size = cv2.getTextSize(state_text, self.font, self.font_scale, self.font_thickness)[0]
        
        # Position text in top-left corner
        angle_pos = (self.text_padding, 30)
        state_pos = (self.text_padding, 70)
        
        # Draw background rectangles for better readability
        cv2.rectangle(info_frame, 
                     (angle_pos[0] - 5, angle_pos[1] - 25),
                     (angle_pos[0] + angle_size[0] + 5, angle_pos[1] + 5),
                     self.colors['text_bg'], -1)
        
        cv2.rectangle(info_frame,
                     (state_pos[0] - 5, state_pos[1] - 25),
                     (state_pos[0] + state_size[0] + 5, state_pos[1] + 5),
                     self.colors['text_bg'], -1)
        
        # Draw text
        cv2.putText(info_frame, angle_text, angle_pos, self.font, 
                   self.font_scale, self.colors['text_fg'], self.font_thickness)
        
        # Use state-specific color for control state text
        state_color = self._get_state_color(state)
        cv2.putText(info_frame, state_text, state_pos, self.font,
                   self.font_scale, state_color, self.font_thickness)
        
        return info_frame
    
    def draw_control_state_indicator(self, frame: np.ndarray, state: ControlState) -> np.ndarray:
        """Draw visual indicator for current mouse control state.
        
        Args:
            frame: Input video frame
            state: Current control state
            
        Returns:
            Frame with control state indicator drawn
        """
        if frame is None:
            raise ValueError("Frame cannot be None")
        
        indicator_frame = frame.copy()
        height, width = frame.shape[:2]
        
        # Position indicator in top-right corner
        indicator_size = 20
        indicator_pos = (width - indicator_size - self.text_padding, self.text_padding)
        
        # Draw indicator circle with state-specific color
        state_color = self._get_state_color(state)
        cv2.circle(indicator_frame, 
                  (indicator_pos[0] + indicator_size // 2, indicator_pos[1] + indicator_size // 2),
                  indicator_size // 2, state_color, -1)
        
        # Add border
        cv2.circle(indicator_frame,
                  (indicator_pos[0] + indicator_size // 2, indicator_pos[1] + indicator_size // 2),
                  indicator_size // 2, self.colors['text_fg'], 2)
        
        # Add state label
        label_text = self._get_state_label(state)
        label_size = cv2.getTextSize(label_text, self.font, 0.5, 1)[0]
        label_pos = (width - label_size[0] - self.text_padding, indicator_pos[1] + indicator_size + 20)
        
        # Draw label background
        cv2.rectangle(indicator_frame,
                     (label_pos[0] - 3, label_pos[1] - 15),
                     (label_pos[0] + label_size[0] + 3, label_pos[1] + 3),
                     self.colors['text_bg'], -1)
        
        # Draw label text
        cv2.putText(indicator_frame, label_text, label_pos, self.font,
                   0.5, self.colors['text_fg'], 1)
        
        return indicator_frame
    
    def show_frame(self, frame: np.ndarray) -> None:
        """Display the frame in the OpenCV window.
        
        Args:
            frame: Frame to display
        """
        if frame is None:
            raise ValueError("Frame cannot be None")
        
        self._ensure_window_created()
        cv2.imshow(self.window_name, frame)
    
    def handle_key_input(self) -> Optional[str]:
        """Handle keyboard input from the OpenCV window.
        
        Returns:
            Key pressed as string, or None if no key pressed
        """
        key = cv2.waitKey(1) & 0xFF
        if key == 255:  # No key pressed
            return None
        elif key == 27:  # ESC key
            return 'esc'
        elif key == ord(' '):  # Space key
            return 'space'
        elif key == ord('q'):  # Q key
            return 'q'
        else:
            return chr(key) if 32 <= key <= 126 else None
    
    def cleanup(self) -> None:
        """Clean up OpenCV windows and resources."""
        if self._window_created:
            cv2.destroyWindow(self.window_name)
            self._window_created = False
    
    def _point_to_pixel(self, point: Point, width: int, height: int) -> Tuple[int, int]:
        """Convert normalized point coordinates to pixel coordinates.
        
        Args:
            point: Point with normalized coordinates (0-1)
            width: Frame width in pixels
            height: Frame height in pixels
            
        Returns:
            Pixel coordinates as (x, y) tuple
        """
        pixel_x = int(point.x * width)
        pixel_y = int(point.y * height)
        return (pixel_x, pixel_y)
    
    def _get_state_color(self, state: ControlState) -> Tuple[int, int, int]:
        """Get color for the given control state.
        
        Args:
            state: Control state
            
        Returns:
            BGR color tuple
        """
        color_map = {
            ControlState.NEUTRAL: self.colors['neutral'],
            ControlState.LEFT_CLICK: self.colors['left_click'],
            ControlState.RIGHT_CLICK: self.colors['right_click']
        }
        return color_map.get(state, self.colors['text_fg'])
    
    def _get_state_label(self, state: ControlState) -> str:
        """Get short label for the given control state.
        
        Args:
            state: Control state
            
        Returns:
            Short label string
        """
        label_map = {
            ControlState.NEUTRAL: "NEUTRAL",
            ControlState.LEFT_CLICK: "LEFT",
            ControlState.RIGHT_CLICK: "RIGHT"
        }
        return label_map.get(state, "UNKNOWN")