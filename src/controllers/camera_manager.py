"""Camera management system for video capture and frame processing."""

import cv2
import numpy as np
from typing import Optional
import logging


class CameraManager:
    """Manages camera connection, frame capture, and resource cleanup."""
    
    def __init__(self, camera_id: int = 0, width: int = 640, height: int = 480):
        """
        Initialize camera manager.
        
        Args:
            camera_id: Camera device ID (default: 0 for primary camera)
            width: Frame width for capture (default: 640)
            height: Frame height for capture (default: 480)
        """
        self.camera_id = camera_id
        self.width = width
        self.height = height
        self.cap: Optional[cv2.VideoCapture] = None
        self._is_initialized = False
        self.logger = logging.getLogger(__name__)
    
    def start_capture(self) -> bool:
        """
        Initialize camera and start video capture.
        
        Returns:
            bool: True if camera initialization successful, False otherwise
        """
        try:
            self.cap = cv2.VideoCapture(self.camera_id)
            
            if not self.cap.isOpened():
                self.logger.error(f"Failed to open camera {self.camera_id}")
                return False
            
            # Set camera properties for optimal performance
            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.width)
            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.height)
            self.cap.set(cv2.CAP_PROP_FPS, 30)
            
            # Verify camera is working by capturing a test frame
            ret, _ = self.cap.read()
            if not ret:
                self.logger.error("Camera opened but failed to capture frame")
                self.release()
                return False
            
            self._is_initialized = True
            self.logger.info(f"Camera {self.camera_id} initialized successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Error initializing camera: {e}")
            self.release()
            return False
    
    def get_frame(self) -> Optional[np.ndarray]:
        """
        Capture a single frame from the camera.
        
        Returns:
            Optional[np.ndarray]: Captured frame if successful, None otherwise
        """
        if not self._is_initialized or self.cap is None:
            self.logger.warning("Camera not initialized")
            return None
        
        try:
            ret, frame = self.cap.read()
            if not ret:
                self.logger.warning("Failed to capture frame")
                return None
            
            return frame
            
        except Exception as e:
            self.logger.error(f"Error capturing frame: {e}")
            return None
    
    def is_available(self) -> bool:
        """
        Check if camera is available and working.
        
        Returns:
            bool: True if camera is available, False otherwise
        """
        if not self._is_initialized or self.cap is None:
            return False
        
        try:
            return self.cap.isOpened()
        except Exception:
            return False
    
    def release(self) -> None:
        """Release camera resources and cleanup."""
        try:
            if self.cap is not None:
                self.cap.release()
                self.logger.info("Camera resources released")
            
        except Exception as e:
            self.logger.error(f"Error releasing camera: {e}")
        finally:
            # Always cleanup regardless of exceptions
            self.cap = None
            self._is_initialized = False
    
    def reconnect(self) -> bool:
        """
        Attempt to reconnect to the camera.
        
        Returns:
            bool: True if reconnection successful, False otherwise
        """
        self.logger.info("Attempting camera reconnection...")
        self.release()
        return self.start_capture()
    
    def get_camera_info(self) -> dict:
        """
        Get current camera properties and settings.
        
        Returns:
            dict: Camera properties including width, height, fps
        """
        if not self.is_available():
            return {}
        
        try:
            return {
                'width': int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH)),
                'height': int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT)),
                'fps': self.cap.get(cv2.CAP_PROP_FPS),
                'camera_id': self.camera_id,
                'is_available': True
            }
        except Exception as e:
            self.logger.error(f"Error getting camera info: {e}")
            return {'is_available': False}