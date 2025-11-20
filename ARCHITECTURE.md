# Architecture Overview

## System Components

### 1. Hand Detection (`hand_gesture_detector.py`)
Main application that handles:
- **Camera Management**: Captures video from webcam
- **Hand Tracking**: Uses MediaPipe Hands to detect 21 hand landmarks in real-time
- **Visualization**: Displays hand skeleton, movement trails, and gesture information
- **UI Overlay**: Shows detection status, current gesture, and gesture guide

Key Features:
- Real-time processing at camera frame rate
- Mirror mode for intuitive interaction
- Visual feedback with colored trails and overlays
- Keyboard controls (q=quit, r=reset)

### 2. Gesture Recognition (`gesture_recognizer.py`)
Core gesture detection algorithms:

#### Gesture Types:
1. **Circular Motions**
   - Tracks hand position history
   - Calculates center point and radius variance
   - Analyzes angle changes to determine direction
   - Detects clockwise vs counter-clockwise rotation

2. **Swipe Gestures**
   - Measures displacement from start to end position
   - Calculates path efficiency (straight vs curved)
   - Determines direction based on angle
   - Supports 4 directions: left, right, up, down

#### Detection Algorithm:
```
1. Maintain position history (30 frames)
2. Extract palm center from hand landmarks
3. For each frame:
   - Add position to history
   - Analyze pattern for circular motion
   - If not circular, check for swipe
   - Apply cooldown after detection
4. Return gesture with confidence score
```

#### Key Parameters:
- `history_size`: 30 frames (adjustable for sensitivity)
- `min_movement`: 0.05 (minimum distance threshold)
- `circular_threshold`: 0.7 (circularity confidence)
- `swipe_threshold`: 0.15 (minimum swipe distance)
- `cooldown_frames`: 15 (prevents duplicate detections)

## Data Flow

```
Camera Feed
    ↓
MediaPipe Hands Detection
    ↓
21 Hand Landmarks (x, y, z)
    ↓
Palm Center Calculation
    ↓
Position History Buffer
    ↓
Gesture Analysis
    ↓
Gesture Recognition
    ↓
Visual Feedback
```

## Hand Landmarks Used

MediaPipe provides 21 landmarks per hand:
- **Wrist (0)**: Base reference point
- **Index MCP (5)**: Metacarpophalangeal joint
- **Pinky MCP (17)**: For palm center calculation

Palm center = Average of (wrist, index_mcp, pinky_mcp)

## Coordinate System

- **X**: Horizontal (0=left, 1=right)
- **Y**: Vertical (0=top, 1=bottom)
- **Z**: Depth (relative to wrist)

All coordinates normalized to [0, 1] range.

## Performance Considerations

1. **Frame Processing**: ~30-60 FPS depending on hardware
2. **Detection Latency**: ~0.5-1 second for gesture completion
3. **Memory Usage**: Minimal (position history only)
4. **CPU Usage**: Moderate (MediaPipe is optimized)

## Future Integration Points

### TV Interface Integration
The system outputs gesture events that can be mapped to TV controls:

```python
gesture_mapping = {
    "CIRCLE_COUNTER_CLOCKWISE": "select_channel",
    "SWIPE_UP": "volume_up",
    "SWIPE_DOWN": "volume_down",
    "SWIPE_LEFT": "previous_menu",
    "SWIPE_RIGHT": "next_menu",
    "CIRCLE_CLOCKWISE": "confirm_selection"
}
```

### Extension Points
1. **Custom Gestures**: Add new patterns in `GestureRecognizer`
2. **Multi-Hand**: Increase `max_num_hands` in MediaPipe config
3. **Gesture Combos**: Detect sequential gesture patterns
4. **Sensitivity Tuning**: Adjust threshold parameters per use case

## Dependencies

- **OpenCV**: Camera capture and visualization
- **MediaPipe**: Hand landmark detection (Google's ML model)
- **NumPy**: Numerical computations for gesture analysis

## Configuration Options

### Camera Settings
- Resolution: 1280x720 (adjustable)
- FPS: System default (typically 30)
- Device: Default camera (index 0)

### Detection Settings
- Confidence threshold: 0.7 (hand detection)
- Tracking threshold: 0.5 (landmark tracking)
- Max hands: 1 (can be increased)

## Testing Gestures

### Circular Motion
1. Raise your hand in front of camera
2. Move hand in a circular pattern
3. Complete at least 3/4 of a circle
4. Keep consistent radius

### Swipe Gestures
1. Raise your hand in front of camera
2. Move hand in desired direction
3. Make the movement swift and straight
4. Minimum distance: ~15% of screen width

## Troubleshooting

### No Hand Detected
- Ensure good lighting
- Check camera permissions
- Adjust `min_detection_confidence`

### Gestures Not Recognized
- Make movements larger and more deliberate
- Check `min_movement` threshold
- Reduce `history_size` for faster detection

### False Positives
- Increase confidence thresholds
- Increase `cooldown_frames`
- Make movements more distinct
