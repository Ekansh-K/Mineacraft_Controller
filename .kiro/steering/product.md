# Product Overview

## Kalakriti OpenCV Project

This is a computer vision-based controller for Minecraft that enables hands-free gameplay through arm pose detection. The system uses OpenCV and MediaPipe to track the player's elbow joint angle in real-time, translating specific arm positions into mouse controls:

- **Right-click**: Elbow angle below 60 degrees
- **Left-click**: Elbow angle above 90 degrees  
- **Neutral**: Elbow angle between 60-90 degrees (no clicks)

## Key Features

- Real-time pose detection using MediaPipe
- Visual feedback with pose overlay and angle display
- Graceful error handling and camera management
- Toggle control system for enabling/disabling pose control
- Performance optimization for smooth 30 FPS operation

## Target Use Case

Designed for Minecraft players who want an alternative, hands-free control method using natural arm movements detected through a standard webcam.