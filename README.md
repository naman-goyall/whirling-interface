# Hand Gesture Recognition for TV Control

A real-time computer vision system that detects hand gestures to control TV interfaces.

## Two Recognition Systems

### 1. **Orbit-Based Gestures** (NEW - Whirling Style) ⭐
Position-independent circular motion recognition inspired by the Whirling Interface research.

**All gestures are circles with different speeds/directions:**
- **Slow Clockwise**: Channel Up (3s per rotation)
- **Slow Counter-Clockwise**: Channel Down (3s per rotation)
- **Fast Clockwise**: Volume Up (1.5s per rotation)
- **Fast Counter-Clockwise**: Volume Down (1.5s per rotation)
- **Medium Clockwise**: Play (2s per rotation)
- **Medium Counter-Clockwise**: Pause (2s per rotation)

**Key Features:**
- ✅ No cursor needed - perform gestures anywhere on screen
- ✅ Uses Pearson correlation for robust matching
- ✅ Real-time visual feedback with correlation scores
- ✅ Simpler to learn - only circular motions at different speeds

**Run the orbit-based controller:**
```bash
python tv_orbit_controller.py
```

See [ORBIT_GESTURES.md](ORBIT_GESTURES.md) for detailed documentation.

### 2. **Shape-Based Gestures** (Original)
Traditional shape tracing with cursor following.

**Gestures:**
- Circular Clockwise / Counter-Clockwise
- Triangle, Square, Diamond
- Swipe gestures (up/down/left/right)

**Run the shape-based controller:**
```bash
python tv_gesture_controller.py
```

## Installation

**Important**: MediaPipe currently supports Python 3.8-3.12. If you're using Python 3.13+, you'll need to use Python 3.11 or 3.12.

### Option 1: Using Python 3.11/3.12 (Recommended)

```bash
# Install Python 3.11 or 3.12 if needed (using Homebrew on macOS)
brew install python@3.11

# Create virtual environment with Python 3.11
python3.11 -m venv venv

# Activate virtual environment
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### Option 2: Using existing Python environment

```bash
# Create virtual environment
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

## Usage

### Quick Start (Orbit-Based - Recommended)
```bash
python tv_orbit_controller.py
```

### Original System (Shape-Based)
```bash
python tv_gesture_controller.py
```

### Basic Hand Detection Only
```bash
python hand_gesture_detector.py
```

### Controls
- Press `q` to quit
- Press `r` to reset gesture detection

## How It Works

### Orbit-Based System (NEW)
1. **Hand Detection**: MediaPipe tracks hand landmarks (palm center)
2. **Orbit Matching**: 6 reference circles continuously rotate at different speeds
3. **Correlation Calculation**: Pearson correlation compares hand trajectory with each orbit
4. **State Machine**: Tracks progression from IDLE → PERFORMING → PENDING → SELECTED
5. **Command Execution**: When correlation held above 0.85 for 1.5s, command triggers

### Shape-Based System (Original)
1. **Hand Detection**: Uses MediaPipe Hands to detect and track 21 hand landmarks
2. **Template Matching**: Compares hand movement with animated shape templates
3. **Sync Scoring**: Measures how well hand follows the template animation
4. **Visual Feedback**: Displays detected gestures and hand landmarks

## Documentation

- **[ORBIT_GESTURES.md](ORBIT_GESTURES.md)**: Complete guide to orbit-based recognition
- **[ARCHITECTURE.md](ARCHITECTURE.md)**: System architecture overview
- **[PROJECT_STATUS.md](PROJECT_STATUS.md)**: Development status and roadmap

## Research Background

The orbit-based system is inspired by:
**"Whirling Interface: Hand-based Motion Matching Selection for Small Target on XR Displays"**
- Juyoung Lee et al., IEEE ISMAR 2024
- [Project Page](https://juyounglee.net/projects/whirling)
