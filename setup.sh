#!/bin/bash

# Setup script for Hand Gesture Detection
echo "====================================="
echo "Hand Gesture Detection - Setup"
echo "====================================="

# Check Python version
PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}')
echo "Detected Python version: $PYTHON_VERSION"

# Extract major and minor version
MAJOR=$(echo $PYTHON_VERSION | cut -d. -f1)
MINOR=$(echo $PYTHON_VERSION | cut -d. -f2)

if [ "$MAJOR" -eq 3 ] && [ "$MINOR" -ge 13 ]; then
    echo ""
    echo "⚠️  Warning: Python 3.13+ detected. MediaPipe requires Python 3.8-3.12."
    echo ""
    echo "Please install Python 3.11 or 3.12:"
    echo "  brew install python@3.11"
    echo ""
    echo "Then run:"
    echo "  python3.11 -m venv venv"
    echo "  source venv/bin/activate"
    echo "  pip install -r requirements.txt"
    exit 1
fi

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
    if [ $? -ne 0 ]; then
        echo "Failed to create virtual environment"
        exit 1
    fi
fi

echo "Activating virtual environment..."
source venv/bin/activate

echo "Installing dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

if [ $? -eq 0 ]; then
    echo ""
    echo "✅ Setup complete!"
    echo ""
    echo "To run the hand gesture detector:"
    echo "  source venv/bin/activate"
    echo "  python hand_gesture_detector.py"
else
    echo ""
    echo "❌ Installation failed. Please check the error messages above."
fi
