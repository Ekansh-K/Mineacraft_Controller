"""
Main entry point for the Kalakriti OpenCV Minecraft Controller.

This application provides hands-free Minecraft control through arm pose detection.
The system uses OpenCV and MediaPipe to track elbow joint angles and translates
specific arm positions into mouse controls.
"""

import sys
import logging
import argparse
from typing import Optional

from src.controllers.application_controller import ApplicationController


def setup_logging(debug: bool = False) -> None:
    """Configure logging for the application.
    
    Args:
        debug: Enable debug level logging if True
    """
    level = logging.DEBUG if debug else logging.INFO
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler('opencv_controller.log')
        ]
    )


def parse_arguments() -> argparse.Namespace:
    """Parse command line arguments.
    
    Returns:
        Parsed command line arguments
    """
    parser = argparse.ArgumentParser(
        description="OpenCV Minecraft Controller - Hands-free gaming through pose detection"
    )
    parser.add_argument(
        '--camera-id', 
        type=int, 
        default=0,
        help='Camera device ID (default: 0)'
    )
    parser.add_argument(
        '--confidence', 
        type=float, 
        default=0.5,
        help='Pose detection confidence threshold (0.0-1.0, default: 0.5)'
    )
    parser.add_argument(
        '--model-complexity',
        type=int,
        choices=[0, 1, 2],
        default=1,
        help='MediaPipe model complexity: 0=Lite (fastest), 1=Full (balanced), 2=Heavy (most accurate)'
    )
    parser.add_argument(
        '--debug', 
        action='store_true',
        help='Enable debug logging'
    )
    
    return parser.parse_args()


def print_usage_instructions() -> None:
    """Print usage instructions for the user."""
    print("\n" + "="*60)
    print("OpenCV Minecraft Controller - Usage Instructions")
    print("="*60)
    print("Controls:")
    print("  SPACE    - Toggle pose control on/off")
    print("  R        - Reset system and re-enable pose control")
    print("  ESC/Q    - Exit application")
    print("\nArm Position Controls:")
    print("  Elbow angle < 60°   - Right mouse button")
    print("  Elbow angle > 90°   - Left mouse button")
    print("  Elbow angle 60-90°  - Neutral (no clicks)")
    print("\nModel Complexity Options:")
    print("  --model-complexity 0  - Lite (fastest, ~60+ FPS)")
    print("  --model-complexity 1  - Full (balanced, ~30+ FPS) [DEFAULT]")
    print("  --model-complexity 2  - Heavy (most accurate, ~15+ FPS)")
    print("\nMake sure you're positioned clearly in front of the camera.")
    print("The system will display your pose overlay and current angle.")
    print("FPS will be logged every 30 frames to monitor performance.")
    print("="*60 + "\n")


def main() -> int:
    """
    Main application entry point.
    
    Returns:
        int: Exit code (0 for success, non-zero for error)
    """
    # Parse command line arguments
    args = parse_arguments()
    
    # Setup logging
    setup_logging(debug=args.debug)
    logger = logging.getLogger(__name__)
    
    # Validate arguments
    if not 0.0 <= args.confidence <= 1.0:
        logger.error("Confidence threshold must be between 0.0 and 1.0")
        return 1
    
    # Print usage instructions
    print_usage_instructions()
    
    # Initialize application controller
    app_controller = None
    
    try:
        logger.info("Starting Kalakriti OpenCV Minecraft Controller...")
        logger.info(f"Camera ID: {args.camera_id}, Confidence: {args.confidence}, Model: {['Lite', 'Full', 'Heavy'][args.model_complexity]}")
        
        # Create and initialize application controller
        app_controller = ApplicationController(
            camera_id=args.camera_id,
            confidence_threshold=args.confidence,
            model_complexity=args.model_complexity
        )
        
        if not app_controller.initialize():
            logger.error("Failed to initialize application components")
            return 1
        
        logger.info("Application initialized successfully")
        logger.info("Press SPACE to toggle pose control, ESC/Q to exit")
        
        # Run the main application loop
        app_controller.run()
        
        logger.info("Application finished successfully")
        return 0
        
    except KeyboardInterrupt:
        logger.info("Application interrupted by user")
        return 0
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        return 1
    finally:
        # Ensure cleanup is performed
        if app_controller:
            app_controller.cleanup()


if __name__ == "__main__":
    sys.exit(main())
