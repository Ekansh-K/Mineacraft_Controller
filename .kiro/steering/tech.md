# Technology Stack

## Build System & Package Management

- **Package Manager**: Uses `uv` for Python and dependency management
- **Configuration**: Uses `pyproject.toml` for dependency specification
- **Python Version**: 3.12 (specified in `.python-version`)
- **Project Structure**: Standard Python package layout
- **Environment**: Managed by uv virtual environments

## Core Dependencies

- **opencv-python**: Camera capture and image processing (not pose detection)
- **mediapipe**: Pose detection and keypoint extraction (primary pose detection engine)
- **pyautogui**: Mouse control automation
- **numpy**: Mathematical calculations and array operations

## Development Dependencies

- **pytest**: Unit testing framework
- **pytest-mock**: Mocking for isolated testing
- **black**: Code formatting
- **mypy**: Type checking

## Common Commands

```bash
# Sync project dependencies
uv sync

# Install the project in development mode
uv pip install -e .

# Run the application
uv run python main.py

# Run tests
uv run pytest

# Format code
uv run black .

# Type checking
uv run mypy .

# Add a new dependency
uv add <package-name>

# Remove a dependency
uv remove <package-name>

# Run a script with dependencies
uv run <script.py>
```

## Architecture Patterns

- **Pipeline Architecture**: Camera (OpenCV) → Pose Detection (MediaPipe) → Angle Calculation → Mouse Control
- **Modular Design**: Separate components for each major functionality
- **Dataclass Models**: Use `@dataclass` for structured data (Point, ArmKeypoints, SystemState)
- **Enum States**: Use `Enum` for control states and system states
- **Error Handling**: Graceful degradation with fallback behaviors

## Technology Roles

- **OpenCV**: Handles camera input, frame capture, and visual display/overlay
- **MediaPipe**: Performs the actual pose detection and keypoint extraction
- **PyAutoGUI**: Executes mouse button press/release commands
- **NumPy**: Supports mathematical calculations for angle computation

## Performance Requirements

- **Target Frame Rate**: 30 FPS
- **Latency**: <100ms from gesture to mouse action
- **CPU Usage**: <50% on mid-range hardware
- **Memory Usage**: <200MB total