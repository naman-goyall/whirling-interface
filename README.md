# Hand Gesture Recognition for TV Control

A real-time computer vision system that detects hand gestures to control TV interfaces.

## Supported Gestures

- **Circular Clockwise**: Rotate hand in clockwise circle
- **Circular Counter-Clockwise**: Rotate hand in counter-clockwise circle
- **Swipe Left**: Move hand from right to left
- **Swipe Right**: Move hand from left to right
- **Swipe Up**: Move hand from bottom to top
- **Swipe Down**: Move hand from top to bottom

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

Run the hand gesture detection:

```bash
python hand_gesture_detector.py
```

### Controls
- Press `q` to quit
- Press `r` to reset gesture detection

## How It Works

1. **Hand Detection**: Uses MediaPipe Hands to detect and track 21 hand landmarks in real-time
2. **Gesture Recognition**: Analyzes hand movement patterns to identify gestures:
   - Tracks hand position history over time
   - Detects directional movements for swipes
   - Analyzes circular patterns for rotation gestures
3. **Visual Feedback**: Displays detected gestures and hand landmarks on screen

## Future Integration

This system will be integrated with a TV interface where:
- Counter-clockwise circle → Channel selection
- Swipe up/down → Volume control
- Swipe left/right → Menu navigation
# whirling-interface
