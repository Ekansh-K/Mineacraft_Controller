"""
Main Application Controller for the OpenCV Minecraft Controller.

This module provides the ApplicationController class that coordinates all system
components including camera management, pose detection, angle calculation,
mouse control, and visual feedback.
"""

import logging
import time
from typing import Optional

from .camera_manager import CameraManager
from .pose_detector import PoseDetector
from .mouse_controller import MouseController, MouseControlError
from .display_manager import DisplayManager
from ..utils.angle_calculator import AngleCalculator
from ..models.data_models import SystemState
from ..models.enums import ControlState


logger = logging.getLogger(__name__)


class ApplicationController:
    """Main application controller that coordinates all system components.
    
    Manages the complete pipeline from camera input through pose detection
    to mouse control, with visual feedback and error handling.
    """
    
    def __init__(self, camera_id: int = 0, confidence_threshold: float = 0.5, model_complexity: int = 1):
        """Initialize the application controller.
        
        Args:
            camera_id: Camera device ID for video capture
            confidence_threshold: Minimum confidence for pose detection
            model_complexity: MediaPipe model complexity (0=Lite, 1=Full, 2=Heavy)
        """
        self.camera_id = camera_id
        self.confidence_threshold = confidence_threshold
        self.model_complexity = model_complexity
        
        # Initialize system state
        self.system_state = SystemState()
        
        # Component instances (initialized in initialize())
        self.camera_manager: Optional[CameraManager] = None
        self.pose_detector: Optional[PoseDetector] = None
        self.mouse_controller: Optional[MouseController] = None
        self.display_manager: Optional[DisplayManager] = None
        self.angle_calculator: Optional[AngleCalculator] = None
        
        # Runtime state
        self._running = False
        self._frame_count = 0
        
        # FPS tracking
        self._fps_start_time = 0.0
        self._fps_frame_count = 0
        self._current_fps = 0.0
        self._fps_update_interval = 30  # Update FPS every 30 frames
        
        logger.info("ApplicationController initialized")
    
    def initialize(self) -> bool:
        """Initialize all system components.
        
        Returns:
            bool: True if initialization successful, False otherwise
        """
        try:
            logger.info("Initializing application components...")
            
            # Initialize camera manager
            self.camera_manager = CameraManager(camera_id=self.camera_id)
            if not self.camera_manager.start_capture():
                logger.error("Failed to initialize camera")
                return False
            
            # Initialize pose detector
            self.pose_detector = PoseDetector(
                confidence_threshold=self.confidence_threshold,
                model_complexity=self.model_complexity
            )
            
            # Initialize mouse controller
            try:
                self.mouse_controller = MouseController()
            except MouseControlError as e:
                logger.error(f"Failed to initialize mouse controller: {e}")
                return False
            
            # Initialize display manager
            self.display_manager = DisplayManager()
            
            # Initialize angle calculator
            self.angle_calculator = AngleCalculator()
            
            logger.info("All components initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"Error during initialization: {e}")
            self.cleanup()
            return False
    
    def run(self) -> None:
        """Run the main application loop.
        
        Processes video frames in real-time, detects poses, calculates angles,
        and controls mouse based on arm positions.
        """
        if not self._validate_components():
            logger.error("Cannot run: components not properly initialized")
            return
        
        logger.info("Starting main application loop...")
        logger.info(f"Using MediaPipe model complexity: {self.model_complexity} ({'Lite' if self.model_complexity == 0 else 'Full' if self.model_complexity == 1 else 'Heavy'})")
        self._running = True
        self._fps_start_time = time.time()
        
        try:
            while self._running:
                # Process single frame
                frame_processed = self._process_frame()
                
                # Handle keyboard input (non-blocking)
                self._handle_keyboard_input()
                
                # If frame processing failed, handle error
                if not frame_processed:
                    if not self._handle_frame_error():
                        break
                
                # Update frame count and FPS
                self._frame_count += 1
                self._update_fps_tracking()
                
        except KeyboardInterrupt:
            logger.info("Application interrupted by user")
        except Exception as e:
            logger.error(f"Unexpected error in main loop: {e}")
        finally:
            self._running = False
            logger.info("Main application loop ended")
    
    def stop(self) -> None:
        """Stop the application gracefully."""
        logger.info("Stopping application...")
        self._running = False
    
    def cleanup(self) -> None:
        """Clean up all system resources."""
        logger.info("Cleaning up application resources...")
        
        # Release mouse buttons first
        if self.mouse_controller:
            try:
                self.mouse_controller.release_all()
            except Exception as e:
                logger.error(f"Error releasing mouse buttons: {e}")
        
        # Clean up display
        if self.display_manager:
            try:
                self.display_manager.cleanup()
            except Exception as e:
                logger.error(f"Error cleaning up display: {e}")
        
        # Release camera
        if self.camera_manager:
            try:
                self.camera_manager.release()
            except Exception as e:
                logger.error(f"Error releasing camera: {e}")
        
        # Reset system state
        self.system_state = SystemState()
        
        logger.info("Cleanup completed")
    
    def toggle_pose_control(self) -> None:
        """Toggle pose control on/off."""
        self.system_state.pose_control_enabled = not self.system_state.pose_control_enabled
        
        if not self.system_state.pose_control_enabled:
            # Release all mouse buttons when disabling
            if self.mouse_controller:
                self.mouse_controller.release_all()
            self.system_state.current_control_state = ControlState.NEUTRAL
        
        status = "enabled" if self.system_state.pose_control_enabled else "disabled"
        logger.info(f"Pose control {status}")
    
    def _process_frame(self) -> bool:
        """Process a single video frame.
        
        Returns:
            bool: True if frame processed successfully, False otherwise
        """
        try:
            # Capture frame
            frame = self.camera_manager.get_frame()
            if frame is None:
                return False
            
            # Initialize display frame
            display_frame = frame.copy()
            
            # Process pose detection if enabled
            if self.system_state.pose_control_enabled:
                display_frame = self._process_pose_detection(frame, display_frame)
            else:
                # Draw disabled indicator
                display_frame = self._draw_disabled_indicator(display_frame)
                # Ensure mouse is in neutral state
                self._set_neutral_state()
            
            # Draw control state indicator
            display_frame = self.display_manager.draw_control_state_indicator(
                display_frame, self.system_state.current_control_state
            )
            
            # Display frame
            self.display_manager.show_frame(display_frame)
            
            return True
            
        except Exception as e:
            logger.error(f"Error processing frame: {e}")
            return False
    
    def _process_pose_detection(self, original_frame, display_frame):
        """Process pose detection and update mouse control.
        
        Args:
            original_frame: Original camera frame
            display_frame: Frame to draw overlays on
            
        Returns:
            Updated display frame with overlays
        """
        # Detect pose
        landmarks = self.pose_detector.detect_pose(original_frame)
        
        if landmarks:
            # Extract arm keypoints
            arm_keypoints = self.pose_detector.get_arm_keypoints(landmarks)
            
            if arm_keypoints:
                try:
                    # Calculate elbow angle
                    angle = self.angle_calculator.calculate_elbow_angle(
                        arm_keypoints.shoulder,
                        arm_keypoints.elbow,
                        arm_keypoints.wrist
                    )
                    
                    if self.angle_calculator.is_angle_valid(angle):
                        # Update system state
                        self.system_state.last_valid_angle = angle
                        
                        # Get control state and update mouse
                        control_state = self.angle_calculator.get_control_state(angle)
                        self._update_mouse_control(control_state)
                        
                        # Draw pose overlay
                        display_frame = self.display_manager.draw_pose_overlay(display_frame, arm_keypoints)
                        
                        # Draw angle and state info
                        display_frame = self.display_manager.draw_angle_info(display_frame, angle, control_state)
                        
                except ValueError as e:
                    logger.warning(f"Invalid angle calculation: {e}")
                    self._set_neutral_state()
            else:
                # No valid arm keypoints detected
                self._set_neutral_state()
        else:
            # No pose detected
            self._set_neutral_state()
        
        return display_frame
    
    def _update_mouse_control(self, control_state: ControlState) -> None:
        """Update mouse control based on the detected control state.
        
        Args:
            control_state: The detected control state
        """
        try:
            self.mouse_controller.set_state(control_state)
            self.system_state.current_control_state = control_state
            self.system_state.error_count = 0  # Reset error count on success
            
        except Exception as e:
            self.system_state.error_count += 1
            logger.error(f"Mouse control error: {e}")
            
            # If too many errors, disable pose control temporarily
            if self.system_state.error_count > 5:
                logger.warning("Too many mouse control errors, temporarily disabling pose control")
                self.system_state.pose_control_enabled = False
    
    def _set_neutral_state(self) -> None:
        """Set mouse to neutral state when no pose is detected."""
        if self.system_state.current_control_state != ControlState.NEUTRAL:
            try:
                self.mouse_controller.set_state(ControlState.NEUTRAL)
                self.system_state.current_control_state = ControlState.NEUTRAL
            except Exception as e:
                logger.error(f"Error setting neutral state: {e}")
    
    def _handle_keyboard_input(self) -> None:
        """Handle keyboard input for system control."""
        try:
            key = self.display_manager.handle_key_input()
            
            if key == 'esc' or key == 'q':
                # Exit application
                self.stop()
            elif key == 'space':
                # Toggle pose control
                self.toggle_pose_control()
            elif key == 'r':
                # Reset error counts and re-enable pose control
                self.system_state.error_count = 0
                self.system_state.pose_control_enabled = True
                if self.mouse_controller:
                    self.mouse_controller.reset_error_count()
                logger.info("System reset - pose control re-enabled")
        except Exception as e:
            logger.error(f"Error handling keyboard input: {e}")
    
    def _handle_frame_error(self) -> bool:
        """Handle frame processing errors.
        
        Returns:
            bool: True to continue processing, False to stop
        """
        try:
            # Check if camera is still available
            if not self.camera_manager.is_available():
                logger.warning("Camera unavailable, attempting reconnection...")
                
                # Try to reconnect
                if self.camera_manager.reconnect():
                    logger.info("Camera reconnected successfully")
                    return True
                else:
                    logger.error("Failed to reconnect camera")
                    return False
            
            # Camera is available but frame capture failed
            # Continue processing - might be temporary issue
            return True
            
        except Exception as e:
            logger.error(f"Error handling frame error: {e}")
            return False
    
    def _draw_disabled_indicator(self, frame):
        """Draw indicator when pose control is disabled.
        
        Args:
            frame: Input video frame
            
        Returns:
            Frame with disabled indicator
        """
        try:
            import cv2
            
            # Draw "DISABLED" text overlay
            text = "POSE CONTROL DISABLED - Press SPACE to enable"
            font = cv2.FONT_HERSHEY_SIMPLEX
            font_scale = 0.8
            color = (0, 0, 255)  # Red
            thickness = 2
            
            # Get text size for centering
            text_size = cv2.getTextSize(text, font, font_scale, thickness)[0]
            height, width = frame.shape[:2]
            
            # Center text
            text_x = (width - text_size[0]) // 2
            text_y = height // 2
            
            # Draw background rectangle
            cv2.rectangle(frame, 
                         (text_x - 10, text_y - 30),
                         (text_x + text_size[0] + 10, text_y + 10),
                         (0, 0, 0), -1)
            
            # Draw text
            cv2.putText(frame, text, (text_x, text_y), font, font_scale, color, thickness)
            
        except Exception as e:
            logger.error(f"Error drawing disabled indicator: {e}")
        
        return frame
    
    def _update_fps_tracking(self) -> None:
        """Update FPS tracking and logging."""
        self._fps_frame_count += 1
        
        if self._fps_frame_count >= self._fps_update_interval:
            current_time = time.time()
            elapsed = current_time - self._fps_start_time
            
            if elapsed > 0:
                self._current_fps = self._fps_frame_count / elapsed
                model_name = {0: 'Lite', 1: 'Full', 2: 'Heavy'}[self.model_complexity]
                logger.info(f"Current FPS: {self._current_fps:.1f} | Model: {model_name}")
            
            # Reset counters
            self._fps_start_time = current_time
            self._fps_frame_count = 0
    
    def _validate_components(self) -> bool:
        """Validate that all required components are initialized.
        
        Returns:
            bool: True if all components are ready, False otherwise
        """
        components = [
            ('camera_manager', self.camera_manager),
            ('pose_detector', self.pose_detector),
            ('mouse_controller', self.mouse_controller),
            ('display_manager', self.display_manager),
            ('angle_calculator', self.angle_calculator)
        ]
        
        for name, component in components:
            if component is None:
                logger.error(f"Component not initialized: {name}")
                return False
        
        return True
    
    def get_system_status(self) -> dict:
        """Get current system status information.
        
        Returns:
            dict: System status information
        """
        return {
            'running': self._running,
            'pose_control_enabled': self.system_state.pose_control_enabled,
            'current_control_state': str(self.system_state.current_control_state),
            'last_valid_angle': self.system_state.last_valid_angle,
            'error_count': self.system_state.error_count,
            'camera_available': self.camera_manager.is_available() if self.camera_manager else False,
            'mouse_controller_healthy': self.mouse_controller.is_healthy() if self.mouse_controller else False,
            'frame_count': self._frame_count,
            'current_fps': self._current_fps,
            'model_complexity': self.model_complexity,
            'model_name': {0: 'Lite', 1: 'Full', 2: 'Heavy'}[self.model_complexity]
        }