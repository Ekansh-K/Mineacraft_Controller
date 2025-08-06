# Project Structure

## Current Layout

```
kalakriti-opencv-project/
├── .kiro/                    # Kiro configuration and specs
│   ├── specs/               # Feature specifications
│   └── steering/            # AI assistant guidance rules
├── main.py                  # Application entry point
├── pyproject.toml          # Project configuration and dependencies
├── .python-version         # Python version specification (3.12)
└── README.md               # Project documentation
```

## Planned Structure (Based on Design Spec)

```
kalakriti-opencv-project/
├── src/
│   ├── models/             # Data models and enums
│   │   ├── __init__.py
│   │   ├── data_models.py  # Point, ArmKeypoints, SystemState
│   │   └── enums.py        # ControlState, system enums
│   ├── controllers/        # Main logic components
│   │   ├── __init__.py
│   │   ├── camera_manager.py
│   │   ├── pose_detector.py
│   │   ├── mouse_controller.py
│   │   └── display_manager.py
│   ├── utils/              # Utility functions
│   │   ├── __init__.py
│   │   ├── angle_calculator.py
│   │   └── config.py
│   └── __init__.py
├── tests/                  # Test files
│   ├── unit/
│   ├── integration/
│   └── __init__.py
├── main.py                 # Application entry point
└── [existing files...]
```

## File Organization Conventions

- **Entry Point**: `main.py` contains the main application controller
- **Source Code**: All implementation code goes in `src/` directory
- **Models**: Data structures and enums in `src/models/`
- **Controllers**: Main component classes in `src/controllers/`
- **Utilities**: Helper functions and calculations in `src/utils/`
- **Tests**: Mirror source structure in `tests/` directory

## Naming Conventions

- **Files**: Snake_case for Python files (`camera_manager.py`)
- **Classes**: PascalCase (`CameraManager`, `PoseDetector`)
- **Functions/Variables**: Snake_case (`calculate_elbow_angle`, `current_state`)
- **Constants**: UPPER_SNAKE_CASE (`RIGHT_CLICK_THRESHOLD`)
- **Private Methods**: Leading underscore (`_validate_keypoints`)

## Import Organization

1. Standard library imports
2. Third-party library imports (opencv, mediapipe, etc.)
3. Local application imports
4. Separate groups with blank lines