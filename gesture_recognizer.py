import numpy as np
from collections import deque
from typing import List, Tuple, Optional, Dict
import math


class GestureRecognizer:
    """
    Recognizes hand gestures from hand landmark positions over time.
    Supports circular motions and directional swipes.
    """
    
    def __init__(self, history_size=50, min_movement=0.05):
        """
        Args:
            history_size: Number of frames to keep in history
            min_movement: Minimum movement threshold to detect gestures
        """
        self.history_size = history_size
        self.min_movement = min_movement
        
        # Store hand position history (using wrist or palm center)
        self.position_history = deque(maxlen=history_size)
        
        # Debug mode
        self.debug = False
        
        # Current detected gesture
        self.current_gesture = None
        self.gesture_confidence = 0.0
        self.gesture_cooldown = 0
        self.cooldown_frames = 20  # Frames to wait before detecting new gesture
        
        # Generate gesture templates
        self.templates = self._generate_templates()
        
        # Minimum points needed for matching
        self.min_points_for_match = 20
        
        # Current hand position for cursor
        self.current_hand_pos = None
        
        # Sync tracking for each gesture
        self.sync_scores = {
            'CIRCLE_CLOCKWISE': [], 
            'CIRCLE_COUNTER_CLOCKWISE': [], 
            'TRIANGLE': [],
            'SQUARE': [],
            'SQUARE_REVERSE': [],
            'DIAMOND': [],
            'SWIPE_UP': [],
            'SWIPE_DOWN': [],
            'SWIPE_LEFT': [],
            'SWIPE_RIGHT': []
        }
        self.sync_window = 50  # Frames to track sync (increased for stricter detection)
        
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
            
            palm_center = (
                (wrist.x + index_mcp.x + pinky_mcp.x) / 3,
                (wrist.y + index_mcp.y + pinky_mcp.y) / 3,
                (wrist.z + index_mcp.z + pinky_mcp.z) / 3
            )
            
            self.position_history.append(palm_center)
            self.current_hand_pos = (palm_center[0], palm_center[1])  # Store for cursor
    
    def _generate_templates(self) -> Dict[str, np.ndarray]:
        """Generate normalized templates for each gesture."""
        templates = {}
        
        # Clockwise circle (50 points)
        angles_cw = np.linspace(0, 2 * np.pi, 50)
        templates['CIRCLE_CLOCKWISE'] = np.column_stack([
            0.5 + 0.3 * np.cos(angles_cw),
            0.5 + 0.3 * np.sin(angles_cw)
        ])
        
        # Counter-clockwise circle (50 points)
        angles_ccw = np.linspace(0, -2 * np.pi, 50)
        templates['CIRCLE_COUNTER_CLOCKWISE'] = np.column_stack([
            0.5 + 0.3 * np.cos(angles_ccw),
            0.5 + 0.3 * np.sin(angles_ccw)
        ])
        
        # Triangle (60 points - 20 per side)
        triangle = []
        # Bottom side (left to right)
        for i in range(20):
            triangle.append([0.2 + 0.6 * i / 20, 0.7])
        # Right side (bottom to top)
        for i in range(20):
            t = i / 20
            triangle.append([0.8 - 0.3 * t, 0.7 - 0.5 * t])
        # Left side (top to bottom)
        for i in range(20):
            t = i / 20
            triangle.append([0.5 - 0.3 * t, 0.2 + 0.5 * t])
        templates['TRIANGLE'] = np.array(triangle)
        
        # Swipe Up (20 points)
        swipe_up = []
        for i in range(20):
            t = i / 19
            swipe_up.append([0.5, 0.8 - 0.6 * t])
        templates['SWIPE_UP'] = np.array(swipe_up)
        
        # Swipe Down (20 points)
        swipe_down = []
        for i in range(20):
            t = i / 19
            swipe_down.append([0.5, 0.2 + 0.6 * t])
        templates['SWIPE_DOWN'] = np.array(swipe_down)
        
        # Swipe Left (20 points)
        swipe_left = []
        for i in range(20):
            t = i / 19
            swipe_left.append([0.8 - 0.6 * t, 0.5])
        templates['SWIPE_LEFT'] = np.array(swipe_left)
        
        # Swipe Right (20 points)
        swipe_right = []
        for i in range(20):
            t = i / 19
            swipe_right.append([0.2 + 0.6 * t, 0.5])
        templates['SWIPE_RIGHT'] = np.array(swipe_right)
        
        # Square (60 points - 15 per side, clockwise from bottom-left)
        square = []
        # Bottom side (left to right)
        for i in range(15):
            square.append([0.2 + 0.6 * i / 14, 0.7])
        # Right side (bottom to top)
        for i in range(15):
            square.append([0.8, 0.7 - 0.5 * i / 14])
        # Top side (right to left)
        for i in range(15):
            square.append([0.8 - 0.6 * i / 14, 0.2])
        # Left side (top to bottom)
        for i in range(15):
            square.append([0.2, 0.2 + 0.5 * i / 14])
        templates['SQUARE'] = np.array(square)
        
        # Square Reverse (60 points - counter-clockwise from top-left)
        square_reverse = []
        # Top side (left to right)
        for i in range(15):
            square_reverse.append([0.2 + 0.6 * i / 14, 0.2])
        # Right side (top to bottom)
        for i in range(15):
            square_reverse.append([0.8, 0.2 + 0.5 * i / 14])
        # Bottom side (right to left)
        for i in range(15):
            square_reverse.append([0.8 - 0.6 * i / 14, 0.7])
        # Left side (bottom to top)
        for i in range(15):
            square_reverse.append([0.2, 0.7 - 0.5 * i / 14])
        templates['SQUARE_REVERSE'] = np.array(square_reverse)
        
        # Diamond (60 points - 15 per side)
        diamond = []
        # Right side (center to right-center)
        for i in range(15):
            t = i / 14
            diamond.append([0.5 + 0.3 * t, 0.5 - 0.3 * t])
        # Bottom side (right-center to bottom-center)
        for i in range(15):
            t = i / 14
            diamond.append([0.8 - 0.3 * t, 0.2 + 0.3 * t])
        # Left side (bottom-center to left-center)
        for i in range(15):
            t = i / 14
            diamond.append([0.5 - 0.3 * t, 0.5 + 0.3 * t])
        # Top side (left-center to top-center)
        for i in range(15):
            t = i / 14
            diamond.append([0.2 + 0.3 * t, 0.8 - 0.3 * t])
        templates['DIAMOND'] = np.array(diamond)
        
        return templates
    
    def get_template(self, gesture_name: str) -> Optional[np.ndarray]:
        """Get the template for a specific gesture."""
        return self.templates.get(gesture_name)
    
    def check_sync_with_template(self, gesture_name: str, template_idx: int, box_x: int, box_y: int, box_size: int) -> float:
        """
        Check how well the current hand position matches the template animation.
        
        Args:
            gesture_name: Name of the gesture template
            template_idx: Current animation index in the template
            box_x, box_y: Top-left corner of template box on screen
            box_size: Size of template box
            
        Returns:
            Sync score (0-1, where 1 is perfect sync)
        """
        if self.current_hand_pos is None:
            return 0.0
        
        template = self.templates.get(gesture_name)
        if template is None or template_idx >= len(template):
            return 0.0
        
        # Get expected position from template
        expected_pos = template[template_idx]
        expected_x = box_x + expected_pos[0] * box_size
        expected_y = box_y + expected_pos[1] * box_size
        
        # Get actual hand position (normalized screen coordinates)
        hand_x = self.current_hand_pos[0]
        hand_y = self.current_hand_pos[1]
        
        # Calculate distance
        dx = hand_x - (expected_x / 1280)  # Assuming 1280 width
        dy = hand_y - (expected_y / 720)    # Assuming 720 height
        distance = np.sqrt(dx**2 + dy**2)
        
        # Convert to sync score (closer = higher score)
        # Distance threshold of 0.1 (normalized coordinates) - tighter for better accuracy
        sync_score = max(0.0, 1.0 - (distance / 0.1))
        
        return sync_score
    
    def _normalize_path(self, positions: np.ndarray) -> np.ndarray:
        """Normalize a path to [0, 1] range."""
        if len(positions) == 0:
            return positions
        
        min_vals = positions.min(axis=0)
        max_vals = positions.max(axis=0)
        
        # Avoid division by zero
        range_vals = max_vals - min_vals
        range_vals[range_vals < 1e-6] = 1.0
        
        normalized = (positions - min_vals) / range_vals
        return normalized
    
    def _resample_path(self, positions: np.ndarray, n_points: int) -> np.ndarray:
        """Resample path to have exactly n_points."""
        if len(positions) < 2:
            return positions
        
        # Calculate cumulative distances
        distances = np.sqrt(np.sum(np.diff(positions, axis=0)**2, axis=1))
        cumsum = np.concatenate([[0], np.cumsum(distances)])
        total_length = cumsum[-1]
        
        if total_length < 1e-6:
            return positions
        
        # Sample evenly along the path
        target_distances = np.linspace(0, total_length, n_points)
        resampled = []
        
        for target_dist in target_distances:
            idx = np.searchsorted(cumsum, target_dist)
            if idx == 0:
                resampled.append(positions[0])
            elif idx >= len(positions):
                resampled.append(positions[-1])
            else:
                # Interpolate between two points
                t = (target_dist - cumsum[idx - 1]) / (cumsum[idx] - cumsum[idx - 1])
                point = positions[idx - 1] + t * (positions[idx] - positions[idx - 1])
                resampled.append(point)
        
        return np.array(resampled)
    
    def _compute_similarity(self, path1: np.ndarray, path2: np.ndarray) -> float:
        """Compute similarity between two paths (0 = different, 1 = identical)."""
        if len(path1) != len(path2):
            return 0.0
        
        # Compute average distance between corresponding points
        distances = np.sqrt(np.sum((path1 - path2)**2, axis=1))
        avg_distance = np.mean(distances)
        
        # Convert distance to similarity (closer to 0 = more similar)
        # Use exponential decay
        similarity = np.exp(-avg_distance * 10)
        
        return similarity
    
    def update_sync_scores(self, sync_data: dict):
        """
        Update sync scores for each gesture based on current animation frame.
        
        Args:
            sync_data: Dict mapping gesture_name to sync_score for current frame
        """
        for gesture_name, sync_score in sync_data.items():
            if gesture_name in self.sync_scores:
                self.sync_scores[gesture_name].append(sync_score)
                # Keep only recent sync_window frames
                if len(self.sync_scores[gesture_name]) > self.sync_window:
                    self.sync_scores[gesture_name].pop(0)
    
    def detect_gesture(self) -> Tuple[Optional[str], float]:
        """
        Detect gesture based on sustained synchronization with templates.
        
        Returns:
            Tuple of (gesture_name, confidence)
        """
        # Manage cooldown
        if self.gesture_cooldown > 0:
            self.gesture_cooldown -= 1
            return self.current_gesture, self.gesture_confidence
        
        # Check sync scores for each gesture
        best_gesture = None
        best_score = 0.0
        
        for gesture_name, scores in self.sync_scores.items():
            if len(scores) >= self.sync_window * 0.8:  # Need at least 80% of window filled
                # Calculate average sync score
                avg_score = np.mean(scores)
                
                if avg_score > best_score:
                    best_score = avg_score
                    best_gesture = gesture_name
        
        # Need at least 70% average sync to detect (stricter)
        if best_score > 0.7 and best_gesture:
            self.current_gesture = best_gesture
            self.gesture_confidence = best_score
            self.gesture_cooldown = self.cooldown_frames
            
            # Clear sync scores after detection
            for gesture_name in self.sync_scores:
                self.sync_scores[gesture_name].clear()
            
            return best_gesture, best_score
        
        # Decay current gesture if no strong detection
        if self.gesture_cooldown == 0:
            self.current_gesture = None
            self.gesture_confidence = 0.0
        
        return self.current_gesture, self.gesture_confidence
    
    def reset(self):
        """Reset gesture history and current detection."""
        self.position_history.clear()
        self.current_gesture = None
        self.gesture_confidence = 0.0
        self.gesture_cooldown = 0
        # Clear sync scores
        for gesture_name in self.sync_scores:
            self.sync_scores[gesture_name].clear()
    
    def get_gesture_description(self, gesture: str) -> str:
        """Get human-readable description of gesture."""
        descriptions = {
            "CIRCLE_CLOCKWISE": "Clockwise Circle",
            "CIRCLE_COUNTER_CLOCKWISE": "Counter-Clockwise Circle",
            "TRIANGLE": "Triangle",
            "SQUARE": "Square",
            "SQUARE_REVERSE": "Square Reverse",
            "DIAMOND": "Diamond",
            "SWIPE_UP": "Swipe Up",
            "SWIPE_DOWN": "Swipe Down",
            "SWIPE_LEFT": "Swipe Left",
            "SWIPE_RIGHT": "Swipe Right"
        }
        return descriptions.get(gesture, "Unknown")
