# Design Document

## Overview

The OpenCV Minecraft Controller is a real-time pose detection system that translates arm movements into mouse controls for Minecraft. The system uses MediaPipe Pose for accurate keypoint detection, calculates elbow joint angles, and maps specific angle ranges to mouse button states. The architecture follows a modular design with separate components for pose detection, angle calculation, mouse control, and visual feedback.

## Architecture

The system follows a pipeline architecture with these main components:

```
Camera Input → Pose Detection → Angle Calculation → Mouse Control
                     ↓
               Visual Feedback ← State Management
```

### Core Components:
1. **Camera Manager**: Handles video capture and frame processing
2. **Pose Detector**: Uses MediaPipe to detect arm keypoints
3. **Angle Calculator**: Computes elbow joint angles from keypoints
4. **Mouse Controller**: Manages mouse button states based on angles
5. **Display Manager**: Provides visual feedback and UI overlay
6. **State Manager**: Coordinates system state and error handling

## Components and Interfaces

### Camera Manager
```python
class CameraManager:
    def __init__(self, camera_id: int = 0)
    def start_capture(self) -> bool
    def get_frame(self) -> Optional[np.ndarray]
    def release(self) -> None
    def is_available(self) -> bool
```

**Responsibilities:**
- Initialize and manage camera connection
- Capture video frames at optimal resolution (640x480 for performance)
- Handle camera disconnection/reconnection
- Provide frame rate control

### Pose Detector
```python
class PoseDetector:
    def __init__(self, confidence_threshold: float = 0.5)
    def detect_pose(self, frame: np.ndarray) -> Optional[PoseLandmarks]
    def get_arm_keypoints(self, landmarks: PoseLandmarks) -> Optional[ArmKeypoints]
    def is_pose_detected(self) -> bool
```

**Responsibilities:**
- Initialize MediaPipe Pose model
- Process frames to detect human pose
- Extract arm-specific keypoints (shoulder, elbow, wrist)
- Filter results based on confidence thresholds

### Angle Calculator
```python
class AngleCalculator:
    @staticmethod
    def calculate_elbow_angle(shoulder: Point, elbow: Point, wrist: Point) -> float
    def get_control_state(self, angle: float) -> ControlState
    def is_angle_valid(self, angle: float) -> bool
```

**Responsibilities:**
- Calculate elbow joint angle using vector mathematics
- Map angles to control states (LEFT_CLICK, RIGHT_CLICK, NEUTRAL)
- Validate angle calculations for accuracy

### Mouse Controller
```python
class MouseController:
    def __init__(self)
    def set_state(self, state: ControlState) -> None
    def release_all(self) -> None
    def get_current_state(self) -> ControlState
```

**Responsibilities:**
- Execute mouse button press/release commands
- Maintain current mouse state to avoid redundant commands
- Handle mouse control errors gracefully

### Display Manager
```python
class DisplayManager:
    def __init__(self, window_name: str)
    def draw_pose_overlay(self, frame: np.ndarray, keypoints: ArmKeypoints) -> np.ndarray
    def draw_angle_info(self, frame: np.ndarray, angle: float, state: ControlState) -> np.ndarray
    def show_frame(self, frame: np.ndarray) -> None
    def handle_key_input(self) -> Optional[str]
```

**Responsibilities:**
- Render pose skeleton overlay on video feed
- Display current angle and control state information
- Handle keyboard input for system control
- Manage OpenCV window display

## Data Models

### Core Data Structures
```python
@dataclass
class Point:
    x: float
    y: float
    z: float = 0.0

@dataclass
class ArmKeypoints:
    shoulder: Point
    elbow: Point
    wrist: Point
    confidence: float

class ControlState(Enum):
    NEUTRAL = "neutral"
    LEFT_CLICK = "left_click"
    RIGHT_CLICK = "right_click"

@dataclass
class SystemState:
    pose_control_enabled: bool = True
    current_control_state: ControlState = ControlState.NEUTRAL
    last_valid_angle: Optional[float] = None
    error_count: int = 0
```

### Angle Thresholds
```python
class AngleThresholds:
    RIGHT_CLICK_THRESHOLD = 60.0  # Below this angle
    LEFT_CLICK_THRESHOLD = 90.0   # Above this angle
    HYSTERESIS_MARGIN = 2.0       # Prevent rapid state changes
```

## Error Handling

### Camera Errors
- **Connection Loss**: Attempt reconnection every 2 seconds, display warning overlay
- **Frame Capture Failure**: Skip frame and continue with next capture
- **Initialization Failure**: Display error message and exit gracefully

### Pose Detection Errors
- **No Person Detected**: Maintain neutral state, continue processing
- **Low Confidence**: Use previous valid state with timeout (2 seconds)
- **Keypoint Missing**: Skip angle calculation for that frame

### Mouse Control Errors
- **Command Failure**: Log error, attempt retry once, continue operation
- **System Permission**: Display permission error and guidance

### Performance Optimization
- **High CPU Usage**: Reduce frame processing rate dynamically
- **Memory Issues**: Implement frame buffer management
- **Latency**: Optimize pose detection model settings

## Testing Strategy

### Unit Testing
- **Angle Calculation**: Test with known keypoint coordinates
- **State Transitions**: Verify correct state changes for angle ranges
- **Mouse Control**: Mock mouse commands and verify state management
- **Error Handling**: Test error scenarios with mocked failures

### Integration Testing
- **Camera Integration**: Test with various camera devices and resolutions
- **Pose Detection Pipeline**: End-to-end testing with recorded video samples
- **Real-time Performance**: Measure frame rate and latency under load

### Manual Testing
- **Gesture Recognition**: Test with different arm positions and movements
- **Edge Cases**: Test with multiple people, poor lighting, partial occlusion
- **User Experience**: Validate visual feedback and control responsiveness

### Performance Benchmarks
- Target: 30 FPS processing rate
- Latency: <100ms from gesture to mouse action
- CPU Usage: <50% on mid-range hardware
- Memory: <200MB total usage

## Dependencies

### Core Libraries
- **opencv-python**: Camera capture and image processing
- **mediapipe**: Pose detection and keypoint extraction
- **pyautogui**: Mouse control automation
- **numpy**: Mathematical calculations and array operations

### Development Dependencies
- **pytest**: Unit testing framework
- **pytest-mock**: Mocking for isolated testing
- **black**: Code formatting
- **mypy**: Type checking