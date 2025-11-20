import cv2
import mediapipe as mp
import numpy as np
import os
from gesture_recognizer import GestureRecognizer


class TVGestureController:
    """
    TV controller with hand gesture detection.
    Shows TV controls as animated gestures that users must follow.
    """
    
    def __init__(self):
        # Initialize MediaPipe Hands
        self.mp_hands = mp.solutions.hands
        self.mp_drawing = mp.solutions.drawing_utils
        self.mp_drawing_styles = mp.solutions.drawing_styles
        
        # Configure hand detection
        self.hands = self.mp_hands.Hands(
            static_image_mode=False,
            max_num_hands=1,
            min_detection_confidence=0.7,
            min_tracking_confidence=0.5
        )
        
        # Initialize gesture recognizer
        self.gesture_recognizer = GestureRecognizer(history_size=50)
        
        # Video capture for hand detection
        self.cap = None
        
        # Video capture for TV content
        self.tv_cap = None
        self.current_channel = 0
        self.channels = [f"channels/channel{i}.mp4" for i in range(1, 7)]
        self.volume = 50
        self.is_paused = False
        
        # UI colors
        self.color_text = (255, 255, 255)  # White
        
        # Animation for templates
        self.frame_count = 0
        
        # Gesture to command mapping
        self.gesture_commands = {
            'TRIANGLE': 'Volume Up',
            'SQUARE': 'Volume Down',
            'CIRCLE_CLOCKWISE': 'Channel Up',
            'CIRCLE_COUNTER_CLOCKWISE': 'Channel Down',
            'DIAMOND': 'Play',
            'SQUARE_REVERSE': 'Pause'
        }
        
        # Last command feedback
        self.last_command = None
        self.command_cooldown = 0
        
    def start(self):
        """Start the TV gesture controller."""
        # Open camera for hand detection
        self.cap = cv2.VideoCapture(0)
        
        if not self.cap.isOpened():
            print("Error: Could not open camera")
            return
        
        # Set camera properties
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
        
        # Load first channel
        self.load_channel(self.current_channel)
        
        print("TV Gesture Controller Started")
        print("=" * 50)
        print("GESTURES:")
        print("  - Triangle = Volume Up")
        print("  - Square = Volume Down")
        print("  - Clockwise Circle = Next Channel")
        print("  - Counter-Clockwise Circle = Previous Channel")
        print("  - Diamond = Play")
        print("  - Square Reverse = Pause")
        print("\nHOW TO USE:")
        print("  1. See the 6 gesture animations when hand detected")
        print("  2. Follow the moving yellow ball with your hand")
        print("  3. Match timing for ~2 seconds to trigger command")
        print("\nControls:")
        print("  - Press 'q' to quit")
        print("  - Press 'r' to reset")
        print("=" * 50)
        
        while True:
            success, frame = self.cap.read()
            
            if not success:
                print("Failed to read frame")
                break
            
            # Flip frame for mirror effect
            frame = cv2.flip(frame, 1)
            
            # Increment frame counter for animation
            self.frame_count += 1
            
            # Process frame
            annotated_frame = self.process_frame(frame)
            
            # Display
            cv2.imshow('TV Gesture Controller', annotated_frame)
            
            # Handle key presses
            key = cv2.waitKey(1) & 0xFF
            if key == ord('q'):
                break
            elif key == ord('r'):
                self.gesture_recognizer.reset()
                print("Gesture detection reset")
        
        self.cleanup()
    
    def load_channel(self, channel_index):
        """Load a TV channel video."""
        if self.tv_cap is not None:
            self.tv_cap.release()
        
        try:
            self.tv_cap = cv2.VideoCapture(self.channels[channel_index])
            if not self.tv_cap.isOpened():
                print(f"Warning: Could not open {self.channels[channel_index]}")
                self.tv_cap = None
        except:
            print(f"Error loading channel {channel_index + 1}")
            self.tv_cap = None
    
    def process_frame(self, camera_frame):
        """Process a single frame."""
        h, w, _ = camera_frame.shape
        
        # Get TV channel frame as background
        tv_frame = self._get_tv_frame(w, h)
        
        # Convert camera frame to RGB for MediaPipe
        rgb_frame = cv2.cvtColor(camera_frame, cv2.COLOR_BGR2RGB)
        
        # Detect hands
        results = self.hands.process(rgb_frame)
        
        # Update hand position (but don't draw landmarks - we only want cursor)
        if results.multi_hand_landmarks:
            for hand_landmarks in results.multi_hand_landmarks:
                # Add position to gesture recognizer
                self.gesture_recognizer.add_hand_position(hand_landmarks.landmark)
        
        # Detect gesture
        gesture, confidence = self.gesture_recognizer.detect_gesture()
        
        # Execute command if gesture detected
        if gesture and self.command_cooldown == 0:
            self.execute_gesture_command(gesture)
        
        if self.command_cooldown > 0:
            self.command_cooldown -= 1
        
        # Draw hand cursor on TV frame (not camera frame)
        hand_detected = results.multi_hand_landmarks is not None
        if hand_detected:
            self._draw_hand_cursor(tv_frame)
        
        # Draw UI on TV frame (pass hand detection status)
        self._draw_ui(tv_frame, gesture, confidence, hand_detected)
        
        return tv_frame
    
    def _get_tv_frame(self, target_w, target_h):
        """Get current TV channel frame, resized to target dimensions."""
        if self.tv_cap is not None and self.tv_cap.isOpened():
            # If paused, just get current frame without advancing
            if self.is_paused:
                # Get current frame position and re-read it
                current_pos = self.tv_cap.get(cv2.CAP_PROP_POS_FRAMES)
                if current_pos > 0:
                    self.tv_cap.set(cv2.CAP_PROP_POS_FRAMES, current_pos - 1)
                ret, tv_frame = self.tv_cap.read()
                if ret:
                    tv_frame = cv2.resize(tv_frame, (target_w, target_h))
                    return tv_frame
            else:
                # Normal playback
                ret, tv_frame = self.tv_cap.read()
                
                if ret:
                    # Resize to match display size
                    tv_frame = cv2.resize(tv_frame, (target_w, target_h))
                    return tv_frame
                else:
                    # Video ended, loop back to start
                    self.tv_cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                    ret, tv_frame = self.tv_cap.read()
                    if ret:
                        tv_frame = cv2.resize(tv_frame, (target_w, target_h))
                        return tv_frame
        
        # Fallback: black frame if no video
        return np.zeros((target_h, target_w, 3), dtype=np.uint8)
    
    def execute_gesture_command(self, gesture):
        """Execute TV command based on detected gesture."""
        if gesture in self.gesture_commands:
            command = self.gesture_commands[gesture]
            
            if gesture == 'TRIANGLE':
                self.volume = min(100, self.volume + 5)
                self.last_command = f"Volume: {self.volume}%"
            elif gesture == 'SQUARE':
                self.volume = max(0, self.volume - 5)
                self.last_command = f"Volume: {self.volume}%"
            elif gesture == 'CIRCLE_CLOCKWISE':
                self.current_channel = (self.current_channel + 1) % len(self.channels)
                self.load_channel(self.current_channel)
                self.last_command = f"Channel: {self.current_channel + 1}"
            elif gesture == 'CIRCLE_COUNTER_CLOCKWISE':
                self.current_channel = (self.current_channel - 1) % len(self.channels)
                self.load_channel(self.current_channel)
                self.last_command = f"Channel: {self.current_channel + 1}"
            elif gesture == 'DIAMOND':
                self.is_paused = False
                self.last_command = "Playing"
            elif gesture == 'SQUARE_REVERSE':
                self.is_paused = True
                self.last_command = "Paused"
            
            print(f"Command: {self.last_command}")
            self.command_cooldown = 30  # Cooldown frames before next command
    
    def _draw_hand_cursor(self, frame):
        """Draw cursor at hand position."""
        if self.gesture_recognizer.current_hand_pos is None:
            return
        
        h, w, _ = frame.shape
        hand_x = int(self.gesture_recognizer.current_hand_pos[0] * w)
        hand_y = int(self.gesture_recognizer.current_hand_pos[1] * h)
        
        # Draw cursor circle
        cv2.circle(frame, (hand_x, hand_y), 15, (0, 255, 255), 3)
        cv2.circle(frame, (hand_x, hand_y), 5, (255, 255, 255), -1)
        
        # Draw crosshair
        cv2.line(frame, (hand_x - 20, hand_y), (hand_x - 10, hand_y), (0, 255, 255), 2)
        cv2.line(frame, (hand_x + 10, hand_y), (hand_x + 20, hand_y), (0, 255, 255), 2)
        cv2.line(frame, (hand_x, hand_y - 20), (hand_x, hand_y - 10), (0, 255, 255), 2)
        cv2.line(frame, (hand_x, hand_y + 10), (hand_x, hand_y + 20), (0, 255, 255), 2)
    
    def _draw_ui(self, frame, gesture, confidence, hand_detected):
        """Draw UI overlay."""
        h, w, _ = frame.shape
        
        # Top panel - only show when hand is detected
        if hand_detected:
            overlay = frame.copy()
            cv2.rectangle(overlay, (0, 0), (w, 100), (0, 0, 0), -1)
            frame_blend = cv2.addWeighted(frame, 0.6, overlay, 0.4, 0)
            frame[:100] = frame_blend[:100]
            
            # Title
            cv2.putText(frame, "TV Gesture Controller", (20, 35),
                       cv2.FONT_HERSHEY_SIMPLEX, 1.0, self.color_text, 2)
            
            # Status
            play_state = "PAUSED" if self.is_paused else "PLAYING"
            status_text = f"Channel: {self.current_channel + 1} | Volume: {self.volume}% | {play_state}"
            cv2.putText(frame, status_text, (20, 70),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)
        
        # Last command feedback (always show when command executed)
        if self.last_command and self.command_cooldown > 0:
            cmd_y = 140
            overlay = frame.copy()
            cv2.rectangle(overlay, (0, cmd_y), (w, cmd_y + 80), (0, 50, 0), -1)
            frame_blend = cv2.addWeighted(frame, 0.5, overlay, 0.5, 0)
            frame[cmd_y:cmd_y + 80] = frame_blend[cmd_y:cmd_y + 80]
            
            cv2.putText(frame, f"Command: {self.last_command}", (20, cmd_y + 50),
                       cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 255, 0), 2)
        
        # Draw gesture templates only if hand is detected
        if hand_detected:
            self._draw_gesture_templates(frame)
        
        # Controls
        controls_y = h - 40
        cv2.putText(frame, "Press 'q' to quit | 'r' to reset", (20, controls_y),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, (200, 200, 200), 1)
    
    def _draw_gesture_templates(self, frame):
        """Draw the 6 TV control gestures."""
        h, w, _ = frame.shape
        
        # Position for templates - 3x2 grid on right side
        start_x = w - 450
        start_y = 180
        template_size = 120
        spacing_x = 200
        spacing_y = 160
        
        gestures = ['TRIANGLE', 'SQUARE', 'CIRCLE_CLOCKWISE', 'CIRCLE_COUNTER_CLOCKWISE', 'DIAMOND', 'SQUARE_REVERSE']
        labels = ['Volume Up', 'Volume Down', 'Next Channel', 'Prev Channel', 'Play', 'Pause']
        
        # Arrange in 3x2 grid (3 rows, 2 columns)
        positions = [
            (0, 0),  # Top left - Triangle (Volume Up)
            (0, 1),  # Top right - Square (Volume Down)
            (1, 0),  # Middle left - Clockwise (Next Channel)
            (1, 1),  # Middle right - Counter-clockwise (Prev Channel)
            (2, 0),  # Bottom left - Diamond (Play)
            (2, 1)   # Bottom right - Square Reverse (Pause)
        ]
        
        sync_data = {}
        
        for idx, (gesture_name, label) in enumerate(zip(gestures, labels)):
            template = self.gesture_recognizer.get_template(gesture_name)
            if template is None:
                continue
            
            row, col = positions[idx]
            box_x = start_x + col * spacing_x
            box_y = start_y + row * spacing_y
            
            # Animate
            total_points = len(template)
            anim_speed = 0.5
            current_idx = int(self.frame_count * anim_speed) % total_points
            
            # Check sync
            sync_score = self.gesture_recognizer.check_sync_with_template(
                gesture_name, current_idx, box_x, box_y, template_size
            )
            sync_data[gesture_name] = sync_score
            
            # Box color based on sync
            if sync_score > 0.7:
                box_color = (0, 200, 0)
            elif sync_score > 0.5:
                box_color = (0, 200, 200)
            else:
                box_color = (40, 40, 40)
            
            # Draw background
            overlay = frame.copy()
            cv2.rectangle(overlay, (box_x - 10, box_y - 10),
                         (box_x + template_size + 10, box_y + template_size + 30),
                         box_color, -1)
            frame[:] = cv2.addWeighted(frame, 0.7, overlay, 0.3, 0)
            
            # Label without sync %
            cv2.putText(frame, label, (box_x, box_y - 15),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.4, (200, 200, 200), 1)
            
            # Draw template path
            for i in range(1, total_points):
                pt1 = template[i-1]
                pt2 = template[i]
                x1 = int(box_x + pt1[0] * template_size)
                y1 = int(box_y + pt1[1] * template_size)
                x2 = int(box_x + pt2[0] * template_size)
                y2 = int(box_y + pt2[1] * template_size)
                cv2.line(frame, (x1, y1), (x2, y2), (100, 100, 100), 2)
            
            # Draw animated ball
            ball_pos = template[current_idx]
            ball_x = int(box_x + ball_pos[0] * template_size)
            ball_y = int(box_y + ball_pos[1] * template_size)
            cv2.circle(frame, (ball_x, ball_y), 10, (0, 255, 255), -1)
            cv2.circle(frame, (ball_x, ball_y), 12, (255, 255, 255), 2)
        
        # Update sync scores
        self.gesture_recognizer.update_sync_scores(sync_data)
    
    def cleanup(self):
        """Release resources."""
        if self.cap:
            self.cap.release()
        if self.tv_cap:
            self.tv_cap.release()
        cv2.destroyAllWindows()
        self.hands.close()
        print("TV Gesture Controller Stopped")


def main():
    controller = TVGestureController()
    controller.start()


if __name__ == "__main__":
    main()
