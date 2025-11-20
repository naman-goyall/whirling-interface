import numpy as np
from collections import deque
from typing import List, Tuple, Optional, Dict
import math
import time


class OrbitGesture:
    """Represents a circular gesture with specific speed and direction."""
    
    def __init__(self, name: str, period: float, clockwise: bool, radius: float = 0.15):
        """
        Args:
            name: Name/command for this gesture
            period: Time in seconds to complete one full circle
            clockwise: True for clockwise, False for counter-clockwise
            radius: Normalized radius of the circle (0-1 scale)
        """
        self.name = name
        self.period = period
        self.clockwise = clockwise
        self.radius = radius
        self.theta = 0.0
        self.theta_history = deque(maxlen=60)
        self.correlation = 0.0
        
    def update(self, delta_time: float):
        """Update the orbit position based on time."""
        angular_velocity = (2 * math.pi / self.period)
        if self.clockwise:
            self.theta += angular_velocity * delta_time
        else:
            self.theta -= angular_velocity * delta_time
        
        # Normalize theta to [0, 2*pi]
        self.theta = self.theta % (2 * math.pi)
        
    def get_position(self, center_x: float = 0.5, center_y: float = 0.5) -> Tuple[float, float]:
        """Get current position on the orbit."""
        x = center_x + self.radius * math.cos(self.theta)
        y = center_y + self.radius * math.sin(self.theta)
        return x, y
    
    def add_theta_history(self, timestamp: float):
        """Store current orbit position in history."""
        x, y = self.get_position()
        self.theta_history.append({
            'timestamp': timestamp,
            'theta': self.theta,
            'x': x,
            'y': y
        })


def pearson_correlation(x: List[float], y: List[float]) -> float:
    """Calculate Pearson correlation coefficient between two sequences."""
    n = len(x)
    if n < 2:
        return 0.0
    
    sum_x = sum(x)
    sum_y = sum(y)
    sum_xy = sum(xi * yi for xi, yi in zip(x, y))
    sum_x2 = sum(xi * xi for xi in x)
    sum_y2 = sum(yi * yi for yi in y)
    
    numerator = n * sum_xy - sum_x * sum_y
    denominator = math.sqrt((n * sum_x2 - sum_x * sum_x) * (n * sum_y2 - sum_y * sum_y))
    
    if denominator == 0:
        return 0.0
    
    return numerator / denominator


class OrbitGestureRecognizer:
    """
    Recognizes gestures based on circular motion matching using Pearson correlation.
    Based on the Whirling Interface approach.
    """
    
    # Detection thresholds
    LOW_THRESHOLD = 0.75
    HIGH_THRESHOLD = 0.85
    PENDING_TIME_THRESHOLD = 1.5  # seconds
    
    # Frame limits
    MINIMUM_FRAME = 30
    MAXIMUM_FRAME = 60
    
    def __init__(self):
        """Initialize the orbit gesture recognizer."""
        # Hand position history
        self.hand_history = deque(maxlen=self.MAXIMUM_FRAME)
        
        # Current hand position
        self.current_hand_pos = None
        
        # Define orbit gestures for TV control
        self.orbits = [
            OrbitGesture("CHANNEL_UP", period=3.0, clockwise=True, radius=0.25),      # Slow CW
            OrbitGesture("CHANNEL_DOWN", period=3.0, clockwise=False, radius=0.25),   # Slow CCW
            OrbitGesture("VOLUME_UP", period=1.5, clockwise=True, radius=0.25),       # Fast CW
            OrbitGesture("VOLUME_DOWN", period=1.5, clockwise=False, radius=0.25),    # Fast CCW
            OrbitGesture("PLAY", period=2.0, clockwise=True, radius=0.25),            # Medium CW
            OrbitGesture("PAUSE", period=2.0, clockwise=False, radius=0.25),          # Medium CCW
        ]
        
        # State tracking
        self.state = "INACTIVE"  # INACTIVE, IDLE, PERFORMING, PENDING, SELECTED
        self.max_orbit = None
        self.pending_start = None
        self.last_state_time = 0.0
        
        # Last detected gesture
        self.current_gesture = None
        self.gesture_confidence = 0.0
        
        # Timing
        self.last_update_time = None
        
        # For visualization
        self.center_x = 0.5
        self.center_y = 0.5
        
    def add_hand_position(self, landmarks):
        """
        Add current hand landmarks to history.
        
        Args:
            landmarks: MediaPipe hand landmarks
        """
        if landmarks:
            # Use palm center (average of key palm points)
            wrist = landmarks[0]
            index_mcp = landmarks[5]
            pinky_mcp = landmarks[17]
            
            palm_center_x = (wrist.x + index_mcp.x + pinky_mcp.x) / 3
            palm_center_y = (wrist.y + index_mcp.y + pinky_mcp.y) / 3
            
            timestamp = time.time()
            
            self.hand_history.append({
                'timestamp': timestamp,
                'position': {'x': palm_center_x, 'y': palm_center_y}
            })
            
            self.current_hand_pos = (palm_center_x, palm_center_y)
            
            # Update center based on current hand position (for visualization)
            if len(self.hand_history) >= self.MINIMUM_FRAME:
                # Calculate center as mean of recent positions
                recent_x = [h['position']['x'] for h in list(self.hand_history)[-self.MINIMUM_FRAME:]]
                recent_y = [h['position']['y'] for h in list(self.hand_history)[-self.MINIMUM_FRAME:]]
                self.center_x = sum(recent_x) / len(recent_x)
                self.center_y = sum(recent_y) / len(recent_y)
    
    def update(self, delta_time: float = None):
        """
        Update orbit positions and detect gestures.
        
        Args:
            delta_time: Time since last update in seconds. If None, calculated automatically.
        """
        current_time = time.time()
        
        if self.last_update_time is None:
            self.last_update_time = current_time
            return
        
        if delta_time is None:
            delta_time = current_time - self.last_update_time
        
        self.last_update_time = current_time
        
        # Update all orbits
        for orbit in self.orbits:
            orbit.update(delta_time)
            orbit.add_theta_history(current_time)
        
        # Calculate correlations and detect gestures
        if len(self.hand_history) >= self.MINIMUM_FRAME:
            self._calculate_correlations()
            self._update_state(current_time)
    
    def _calculate_correlations(self):
        """Calculate Pearson correlation for each orbit gesture."""
        for orbit in self.orbits:
            if len(orbit.theta_history) < self.MINIMUM_FRAME:
                orbit.correlation = 0.0
                continue
            
            # Get recent positions (matching the frame count)
            frame_count = min(len(self.hand_history), self.MAXIMUM_FRAME)
            
            orbit_history = list(orbit.theta_history)[-frame_count:]
            hand_history = list(self.hand_history)[-frame_count:]
            
            # Extract X and Y coordinates
            orbit_xs = [h['x'] for h in orbit_history]
            orbit_ys = [h['y'] for h in orbit_history]
            hand_xs = [h['position']['x'] for h in hand_history]
            hand_ys = [h['position']['y'] for h in hand_history]
            
            # Calculate correlation for both X and Y
            corr_x = pearson_correlation(orbit_xs, hand_xs)
            corr_y = pearson_correlation(orbit_ys, hand_ys)
            
            # Average correlation
            orbit.correlation = (corr_x + corr_y) / 2
    
    def _update_state(self, current_time: float):
        """Update state machine based on correlations."""
        # Find orbit with maximum correlation
        max_orbit = max(self.orbits, key=lambda o: o.correlation)
        max_corr = max_orbit.correlation
        
        # State transitions with cooldown
        if current_time - self.last_state_time < 0.5:
            return
        
        if self.state == "IDLE":
            if max_corr >= self.LOW_THRESHOLD:
                self.state = "PERFORMING"
                self.max_orbit = max_orbit
                self.last_state_time = current_time
                
        elif self.state == "PERFORMING":
            if max_corr < self.LOW_THRESHOLD:
                self.state = "IDLE"
                self.max_orbit = None
                self.last_state_time = current_time
            elif max_corr >= self.HIGH_THRESHOLD:
                self.state = "PENDING"
                self.max_orbit = max_orbit
                self.pending_start = current_time
                self.last_state_time = current_time
                
        elif self.state == "PENDING":
            # Check if we maintained high correlation
            if max_orbit == self.max_orbit and (current_time - self.pending_start) > self.PENDING_TIME_THRESHOLD:
                self.state = "SELECTED"
                self.current_gesture = max_orbit.name
                self.gesture_confidence = max_corr
                self.last_state_time = current_time
            elif max_orbit != self.max_orbit or max_corr < self.HIGH_THRESHOLD:
                # Lost sync, go back to performing or idle
                if max_corr >= self.LOW_THRESHOLD:
                    self.state = "PERFORMING"
                else:
                    self.state = "IDLE"
                self.max_orbit = None
                self.pending_start = None
                self.last_state_time = current_time
    
    def detect_gesture(self) -> Tuple[Optional[str], float]:
        """
        Detect current gesture.
        
        Returns:
            Tuple of (gesture_name, confidence)
        """
        if self.state == "SELECTED":
            gesture = self.current_gesture
            confidence = self.gesture_confidence
            
            # Reset after detection
            self.state = "IDLE"
            self.current_gesture = None
            self.gesture_confidence = 0.0
            self.max_orbit = None
            self.pending_start = None
            
            return gesture, confidence
        
        return None, 0.0
    
    def set_inactive(self, inactive: bool):
        """Set inactive state (when no hand detected)."""
        if inactive:
            self.state = "INACTIVE"
            self.hand_history.clear()
            for orbit in self.orbits:
                orbit.theta_history.clear()
                orbit.correlation = 0.0
            self.current_hand_pos = None
            self.max_orbit = None
            self.pending_start = None
        else:
            if self.state == "INACTIVE":
                self.state = "IDLE"
    
    def reset(self):
        """Reset the recognizer state."""
        self.hand_history.clear()
        self.current_hand_pos = None
        self.state = "IDLE"
        self.current_gesture = None
        self.gesture_confidence = 0.0
        self.max_orbit = None
        self.pending_start = None
        
        for orbit in self.orbits:
            orbit.theta_history.clear()
            orbit.correlation = 0.0
    
    def get_orbits(self) -> List[OrbitGesture]:
        """Get all orbit gestures for visualization."""
        return self.orbits
    
    def get_state(self) -> str:
        """Get current state."""
        return self.state
    
    def get_max_orbit(self) -> Optional[OrbitGesture]:
        """Get the orbit with highest correlation (for visualization)."""
        if self.state in ["PERFORMING", "PENDING"]:
            return self.max_orbit
        return None
    
    def get_hand_position(self) -> Optional[Tuple[float, float]]:
        """Get current hand position."""
        return self.current_hand_pos
    
    def get_orbit_center(self) -> Tuple[float, float]:
        """Get the center point for orbit visualization."""
        return self.center_x, self.center_y
