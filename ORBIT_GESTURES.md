# Orbit-Based Gesture Recognition (Whirling Style)

## Overview

This system uses **orbit-based gesture recognition** inspired by the Whirling Interface research. Instead of tracing different shapes (circles, triangles, squares), all gestures are **circular motions** with different **speeds and directions**.

## Key Concepts

### 1. All Gestures Are Circles
- **No shape tracing required** - everything is a circular motion
- Different commands = Different circle parameters:
  - **Speed**: Slow (3s), Medium (2s), Fast (1.5s) per rotation
  - **Direction**: Clockwise (CW) vs Counter-Clockwise (CCW)

### 2. Position-Independent Detection
- **No cursor needed** - user can perform gestures anywhere on screen
- System matches the **motion pattern**, not the position
- Uses Pearson correlation to compare hand movement with reference orbits

### 3. Correlation-Based Matching
- Tracks hand position over 30-60 frames
- Compares X and Y trajectories with each orbit pattern
- Correlation score: -1 (opposite) to +1 (perfect match)
- Thresholds:
  - **0.75**: PERFORMING (starting to match)
  - **0.85**: PENDING (strong match)
  - **Hold for 1.5s**: SELECTED (command triggered)

## TV Control Gestures

| Gesture | Speed | Direction | Command |
|---------|-------|-----------|---------|
| Slow Circle | 3.0s | Clockwise | **Channel Up** |
| Slow Circle | 3.0s | Counter-CW | **Channel Down** |
| Fast Circle | 1.5s | Clockwise | **Volume Up** |
| Fast Circle | 1.5s | Counter-CW | **Volume Down** |
| Medium Circle | 2.0s | Clockwise | **Play** |
| Medium Circle | 2.0s | Counter-CW | **Pause** |

## How It Works

### State Machine
```
INACTIVE → IDLE → PERFORMING → PENDING → SELECTED
     ↑                              ↓
     └──────────────────────────────┘
```

**States:**
- **INACTIVE**: No hand detected
- **IDLE**: Hand detected, waiting for motion
- **PERFORMING**: Correlation ≥ 0.75, matching an orbit
- **PENDING**: Correlation ≥ 0.85, strong match
- **SELECTED**: Held for 1.5s, command executed

### Detection Algorithm

1. **Capture Hand Position**
   - Uses MediaPipe to detect hand landmarks
   - Extracts palm center (average of wrist, index MCP, pinky MCP)
   - Stores in position history buffer

2. **Update Reference Orbits**
   - 6 orbit patterns continuously animate
   - Each orbit rotates at its designated speed/direction
   - Position stored in orbit history buffer

3. **Calculate Correlations**
   - For each orbit, compare:
     - Hand X positions vs Orbit X positions
     - Hand Y positions vs Orbit Y positions
   - Use Pearson correlation coefficient
   - Average the X and Y correlations

4. **State Transitions**
   - Find orbit with highest correlation
   - Check thresholds and update state
   - Execute command when SELECTED state reached

## Pearson Correlation

The system uses Pearson correlation to measure similarity:

```
r = (n·Σxy - Σx·Σy) / sqrt[(n·Σx² - (Σx)²) · (n·Σy² - (Σy)²)]
```

Where:
- `n` = number of frames (30-60)
- `x` = hand positions
- `y` = orbit positions

**Interpretation:**
- `r = 1.0`: Perfect positive correlation (exact match)
- `r = 0.0`: No correlation (random)
- `r = -1.0`: Perfect negative correlation (opposite motion)

## Visual Feedback

### Orbit Display (3×2 Grid)
- Shows 6 orbiting circles on right side of screen
- Each displays:
  - **Gray circle**: Orbit path
  - **Yellow ball**: Current orbit position
  - **White arrow**: Direction indicator
  - **Label**: Command name and speed/direction
  - **Correlation score**: When > 0.3

### Color Coding
- **Dark Gray (40,40,40)**: Low correlation (< 0.5)
- **Dark Cyan (100,100,0)**: Medium correlation (0.5-0.7)
- **Light Yellow (0,200,200)**: High correlation (> 0.7)
- **Yellow (0,255,255)**: PERFORMING state
- **Green (0,255,0)**: PENDING state (almost there!)
- **Red (0,0,255)**: SELECTED state (command executed!)

### Hand Indicator
- **Purple circle**: Shows current hand position on screen
- No cursor needed - just for reference

## Usage Instructions

### Running the System
```bash
python tv_orbit_controller.py
```

### Performing Gestures

1. **Show your hand** to the camera
   - Orbits will appear on the right side
   - System enters IDLE state

2. **Move hand in a circle** (anywhere on screen)
   - Match the speed and direction of desired command
   - Watch correlation scores increase

3. **Maintain the pattern**
   - When correlation reaches 0.75, box turns yellow (PERFORMING)
   - When correlation reaches 0.85, box turns green (PENDING)
   - Keep going for 1.5 more seconds

4. **Command executes**
   - Box turns red briefly (SELECTED)
   - Command feedback shown at top
   - System returns to IDLE

### Tips for Better Recognition

**Speed Matching:**
- **Slow** (~3 sec per circle): Leisurely pace, like drawing with care
- **Medium** (~2 sec per circle): Normal circular motion
- **Fast** (~1.5 sec per circle): Quick spinning motion

**Direction:**
- **Clockwise**: Natural "stirring" motion
- **Counter-Clockwise**: Reverse motion

**Best Practices:**
- Make smooth, consistent circles
- Keep similar radius throughout
- Don't need to be at specific position - motion pattern matters
- If correlation is low, try adjusting speed
- Watch the reference balls to match timing

## Implementation Details

### Files
- **`orbit_gesture_recognizer.py`**: Core recognition engine
  - `OrbitGesture` class: Defines single orbit pattern
  - `OrbitGestureRecognizer` class: Manages detection and state
  - `pearson_correlation()`: Similarity calculation

- **`tv_orbit_controller.py`**: TV control interface
  - Integrates MediaPipe hand tracking
  - Visualizes orbits and feedback
  - Maps gestures to TV commands

### Key Parameters (Tunable)

```python
# Correlation thresholds
LOW_THRESHOLD = 0.75      # Start detecting
HIGH_THRESHOLD = 0.85     # Strong match
PENDING_TIME_THRESHOLD = 1.5  # Seconds to hold

# History buffers
MINIMUM_FRAME = 30        # Min frames for correlation
MAXIMUM_FRAME = 60        # Max frames to keep

# Orbit speeds (seconds per rotation)
SLOW = 3.0
MEDIUM = 2.0
FAST = 1.5

# Orbit radius (normalized)
RADIUS = 0.15             # 15% of screen
```

## Advantages Over Shape-Based Recognition

1. **Simpler for Users**
   - Only need to learn circular motion
   - Speed/direction more intuitive than shape memory

2. **More Reliable**
   - Correlation is robust to position/scale variations
   - Natural motion is easier to maintain

3. **Position Independent**
   - Can perform gesture anywhere
   - No need to find cursor or specific zone

4. **Better Feedback**
   - Continuous correlation score
   - Visual indicators show how close you are

5. **Scalable**
   - Easy to add new commands (just vary speed/direction)
   - Can combine with other parameters (radius, etc.)

## Research Background

Based on:
**"Whirling Interface: Hand-based Motion Matching Selection for Small Target on XR Displays"**
- Juyoung Lee et al.
- IEEE ISMAR 2024

Key innovations from paper:
- Motion matching instead of static target selection
- Pearson correlation for trajectory comparison
- Orbit-based interaction paradigm
- Adaptive window sizing (30-60 frames)

## Comparison with Original System

| Feature | Original (Shape-Based) | New (Orbit-Based) |
|---------|----------------------|-------------------|
| Gesture Types | 10 shapes | 6 circles |
| Position | Requires cursor tracking | Position-independent |
| Detection | Template matching | Pearson correlation |
| Feedback | Sync percentage | Correlation score |
| User Learning | Remember 10 shapes | Learn 3 speeds × 2 directions |
| Execution | Follow animated shape | Match circle speed/direction |

## Future Enhancements

### Possible Extensions
1. **Variable Radius**: Add size as third parameter
2. **Multi-Hand**: Use both hands for combo gestures
3. **Adaptive Thresholds**: Adjust based on user performance
4. **Custom Training**: Let users define their own orbit speeds
5. **3D Orbits**: Use depth (Z) for additional commands

### Additional Applications
- Menu navigation in VR/AR
- Music/media control
- Smart home control
- Gaming input
- Accessibility interfaces
