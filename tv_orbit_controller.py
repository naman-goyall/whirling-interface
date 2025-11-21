import cv2
import mediapipe as mp
import numpy as np
import os
import math
from orbit_gesture_recognizer import OrbitGestureRecognizer


class TVOrbitController:
    """
    TV controller with orbit-based hand gesture detection.
    Based on the Whirling Interface approach - all commands are circles with different speeds.
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
        
        # Initialize orbit gesture recognizer
        self.gesture_recognizer = OrbitGestureRecognizer()
        
        # Video capture for hand detection
        self.cap = None
        
        # Video capture for TV content
        self.tv_cap = None
        self.current_channel = 0
        self.channels = [f"channels/channel{i}.mp4" for i in range(1, 7)]
        self.volume = 50
        self.is_paused = False
        self.paused_frame = None  # Cache the paused frame to avoid seeking
        
        # UI colors
        self.color_text = (255, 255, 255)  # White
        
        # Gesture to command mapping
        self.gesture_commands = {
            'CHANNEL_UP': 'Next Channel',
            'CHANNEL_DOWN': 'Previous Channel',
            'VOLUME_UP': 'Volume Up',
            'VOLUME_DOWN': 'Volume Down',
            'PLAY': 'Play',
            'PAUSE': 'Pause'
        }
        
        # Last command feedback
        self.last_command = None
        self.command_cooldown = 0
        
        # Volume ramping for sustained gestures
        self.last_volume_gesture = None
        self.volume_gesture_count = 0
        self.volume_step_sizes = [5, 10, 15, 20]  # Progressive step sizes
        self.last_volume_gesture_frame = 0
        self.volume_gesture_timeout = 90  # Reset if no gesture for 90 frames (~3 seconds)
        self.current_frame = 0
        
    def start(self):
        """Start the TV orbit controller."""
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
        
        print("TV Orbit Controller Started")
        print("=" * 60)
        print("ORBIT GESTURES (All are circles with different speeds):")
        print("  - Slow Clockwise Circle = Next Channel")
        print("  - Slow Counter-Clockwise Circle = Previous Channel")
        print("  - Fast Clockwise Circle = Volume Up")
        print("  - Fast Counter-Clockwise Circle = Volume Down")
        print("  - Medium Clockwise Circle = Play")
        print("  - Medium Counter-Clockwise Circle = Pause")
        print("\nHOW TO USE:")
        print("  1. See the 6 orbiting circles when hand is detected")
        print("  2. Move your hand in a circular motion ANYWHERE on screen")
        print("  3. Match the speed and direction of the desired command")
        print("  4. Keep matching for ~1.5 seconds to trigger")
        print("  5. NO CURSOR NEEDED - just move in circles!")
        print("\nKeyboard Controls:")
        print("  - Press 'q' to quit")
        print("  - Press 'r' to reset gestures")
        print("  - Up Arrow = Volume Up")
        print("  - Down Arrow = Volume Down")
        print("  - Right Arrow = Next Channel")
        print("  - Left Arrow = Previous Channel")
        print("  - Space = Play/Pause Toggle")
        print("=" * 60)
        
        while True:
            success, frame = self.cap.read()
            
            if not success:
                print("Failed to read frame")
                break
            
            # Flip frame for mirror effect
            frame = cv2.flip(frame, 1)
            
            # Process frame
            annotated_frame = self.process_frame(frame)
            
            # Display
            cv2.imshow('TV Orbit Controller', annotated_frame)
            
            # Handle key presses
            key = cv2.waitKey(1) & 0xFF
            if key == ord('q'):
                break
            elif key == ord('r'):
                self.gesture_recognizer.reset()
                print("Gesture detection reset")
            elif key == 0:  # Up arrow
                self.handle_keyboard_command('VOLUME_UP')
            elif key == 1:  # Down arrow
                self.handle_keyboard_command('VOLUME_DOWN')
            elif key == 2:  # Right arrow
                self.handle_keyboard_command('CHANNEL_UP')
            elif key == 3:  # Left arrow
                self.handle_keyboard_command('CHANNEL_DOWN')
            elif key == 32:  # Space
                if self.is_paused:
                    self.handle_keyboard_command('PLAY')
                else:
                    self.handle_keyboard_command('PAUSE')
        
        self.cleanup()
    
    def load_channel(self, channel_index):
        """Load a TV channel video."""
        if self.tv_cap is not None:
            self.tv_cap.release()
        
        # Clear paused frame cache when changing channels
        self.paused_frame = None
        
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
        self.current_frame += 1
        h, w, _ = camera_frame.shape
        
        # Get TV channel frame as background
        tv_frame = self._get_tv_frame(w, h)
        
        # Convert camera frame to RGB for MediaPipe
        rgb_frame = cv2.cvtColor(camera_frame, cv2.COLOR_BGR2RGB)
        
        # Detect hands
        results = self.hands.process(rgb_frame)
        
        # Update hand position and gesture recognizer
        hand_detected = results.multi_hand_landmarks is not None
        
        if hand_detected:
            for hand_landmarks in results.multi_hand_landmarks:
                # Add position to gesture recognizer
                self.gesture_recognizer.add_hand_position(hand_landmarks.landmark)
            
            # Set active state
            self.gesture_recognizer.set_inactive(False)
        else:
            # No hand detected
            self.gesture_recognizer.set_inactive(True)
        
        # Update gesture recognizer (orbit animations and correlation calculations)
        self.gesture_recognizer.update()
        
        # Detect gesture
        gesture, confidence = self.gesture_recognizer.detect_gesture()
        
        # Execute command if gesture detected
        if gesture and self.command_cooldown == 0:
            self.execute_gesture_command(gesture)
        
        if self.command_cooldown > 0:
            self.command_cooldown -= 1
        
        # Draw UI on TV frame
        self._draw_ui(tv_frame, gesture, confidence, hand_detected)
        
        return tv_frame
    
    def _get_tv_frame(self, target_w, target_h):
        """Get current TV channel frame, resized to target dimensions."""
        if self.tv_cap is not None and self.tv_cap.isOpened():
            # If paused, return cached frame (no video seeking needed)
            if self.is_paused:
                if self.paused_frame is not None:
                    return self.paused_frame
                # If no cached frame yet, read current and cache it
                ret, tv_frame = self.tv_cap.read()
                if ret:
                    tv_frame = cv2.resize(tv_frame, (target_w, target_h))
                    self.paused_frame = tv_frame.copy()
                    return tv_frame
            else:
                # Normal playback - clear cached frame and advance video
                self.paused_frame = None
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
            
            if gesture == 'VOLUME_UP':
                # Check if this is a continuous gesture (within timeout)
                frames_since_last = self.current_frame - self.last_volume_gesture_frame
                is_continuous = (self.last_volume_gesture == 'VOLUME_UP' and 
                                frames_since_last < self.volume_gesture_timeout)
                
                # Ramp up step size for continuous volume gestures
                if is_continuous:
                    self.volume_gesture_count += 1
                else:
                    self.volume_gesture_count = 0
                    self.last_volume_gesture = 'VOLUME_UP'
                
                self.last_volume_gesture_frame = self.current_frame
                
                # Get step size based on consecutive count (capped)
                step_index = min(self.volume_gesture_count, len(self.volume_step_sizes) - 1)
                step_size = self.volume_step_sizes[step_index]
                
                self.volume = min(100, self.volume + step_size)
                self.last_command = f"Volume: {self.volume}% (+{step_size})"
            elif gesture == 'VOLUME_DOWN':
                # Check if this is a continuous gesture (within timeout)
                frames_since_last = self.current_frame - self.last_volume_gesture_frame
                is_continuous = (self.last_volume_gesture == 'VOLUME_DOWN' and 
                                frames_since_last < self.volume_gesture_timeout)
                
                # Ramp up step size for continuous volume gestures
                if is_continuous:
                    self.volume_gesture_count += 1
                else:
                    self.volume_gesture_count = 0
                    self.last_volume_gesture = 'VOLUME_DOWN'
                
                self.last_volume_gesture_frame = self.current_frame
                
                # Get step size based on consecutive count (capped)
                step_index = min(self.volume_gesture_count, len(self.volume_step_sizes) - 1)
                step_size = self.volume_step_sizes[step_index]
                
                self.volume = max(0, self.volume - step_size)
                self.last_command = f"Volume: {self.volume}% (-{step_size})"
            elif gesture == 'CHANNEL_UP':
                # Reset volume ramping when switching to non-volume gesture
                self.last_volume_gesture = None
                self.volume_gesture_count = 0
                
                self.current_channel = (self.current_channel + 1) % len(self.channels)
                self.load_channel(self.current_channel)
                self.last_command = f"Channel: {self.current_channel + 1}"
            elif gesture == 'CHANNEL_DOWN':
                # Reset volume ramping when switching to non-volume gesture
                self.last_volume_gesture = None
                self.volume_gesture_count = 0
                
                self.current_channel = (self.current_channel - 1) % len(self.channels)
                self.load_channel(self.current_channel)
                self.last_command = f"Channel: {self.current_channel + 1}"
            elif gesture == 'PLAY':
                # Reset volume ramping when switching to non-volume gesture
                self.last_volume_gesture = None
                self.volume_gesture_count = 0
                
                self.is_paused = False
                self.paused_frame = None  # Clear cached frame when resuming
                self.last_command = "Playing"
            elif gesture == 'PAUSE':
                # Reset volume ramping when switching to non-volume gesture
                self.last_volume_gesture = None
                self.volume_gesture_count = 0
                
                self.is_paused = True
                # Frame will be cached on next _get_tv_frame call
                self.last_command = "Paused"
            
            print(f"Command: {self.last_command}")
            self.command_cooldown = 30  # Cooldown frames before next command
    
    def handle_keyboard_command(self, gesture):
        """Handle keyboard input as if it were a gesture command."""
        # Bypass cooldown for keyboard commands
        self.execute_gesture_command(gesture)
    
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
            cv2.putText(frame, "TV Orbit Controller (Whirling Style)", (20, 35),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.9, self.color_text, 2)
            
            # Status
            play_state = "PAUSED" if self.is_paused else "PLAYING"
            status_text = f"Channel: {self.current_channel + 1} | Volume: {self.volume}% | {play_state}"
            cv2.putText(frame, status_text, (20, 70),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)
        
        # Last command feedback (always show when command executed)
        if self.last_command and self.command_cooldown > 0:
            cmd_y = 120
            overlay = frame.copy()
            cv2.rectangle(overlay, (0, cmd_y), (w, cmd_y + 80), (0, 0, 0), -1)
            frame_blend = cv2.addWeighted(frame, 0.3, overlay, 0.7, 0)
            frame[cmd_y:cmd_y + 80] = frame_blend[cmd_y:cmd_y + 80]
            
            cv2.putText(frame, f"Command: {self.last_command}", (20, cmd_y + 50),
                       cv2.FONT_HERSHEY_SIMPLEX, 1.0, (255, 255, 255), 2)
        
        # Draw orbit visualizations only if hand is detected
        if hand_detected:
            self._draw_orbit_gestures(frame)
        else:
            # Show message when no hand detected
            msg = "Show your hand to see orbit gestures"
            text_size = cv2.getTextSize(msg, cv2.FONT_HERSHEY_SIMPLEX, 0.8, 2)[0]
            text_x = (w - text_size[0]) // 2
            text_y = h // 2
            cv2.putText(frame, msg, (text_x, text_y),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.8, (100, 100, 100), 2)
        
        # Controls
        controls_y = h - 40
        cv2.putText(frame, "Press 'q' to quit | Arrow keys: Vol/Ch | Space: Play/Pause", (20, controls_y),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, (200, 200, 200), 1)
    
    def _draw_orbit_gestures(self, frame):
        """Draw the 6 orbit gesture visualizations."""
        h, w, _ = frame.shape
        
        # Get orbits from recognizer
        orbits = self.gesture_recognizer.get_orbits()
        state = self.gesture_recognizer.get_state()
        max_orbit = self.gesture_recognizer.get_max_orbit()
        hand_pos = self.gesture_recognizer.get_hand_position()
        
        # Position for orbit displays - 3x2 grid on right side
        start_x = w - 470
        start_y = 220
        orbit_display_radius = 80
        spacing_x = 220
        spacing_y = 180
        
        # Arrange in 3x2 grid (3 rows, 2 columns)
        positions = [
            (0, 0),  # Top left - Channel Up (Slow CW)
            (0, 1),  # Top right - Channel Down (Slow CCW)
            (1, 0),  # Middle left - Volume Up (Fast CW)
            (1, 1),  # Middle right - Volume Down (Fast CCW)
            (2, 0),  # Bottom left - Play (Medium CW)
            (2, 1)   # Bottom right - Pause (Medium CCW)
        ]
        
        for idx, orbit in enumerate(orbits):
            row, col = positions[idx]
            center_x = start_x + col * spacing_x
            center_y = start_y + row * spacing_y
            
            # Get orbit position
            orbit_x, orbit_y = orbit.get_position(center_x=0.5, center_y=0.5)
            
            # Convert to screen coordinates relative to display center
            rel_x = int((orbit_x - 0.5) * orbit_display_radius * 2)
            rel_y = int((orbit_y - 0.5) * orbit_display_radius * 2)
            ball_x = center_x + rel_x
            ball_y = center_y + rel_y
            
            # Determine color based on state and correlation
            correlation = orbit.correlation
            
            # Box color based on correlation and state
            if state == "SELECTED" and max_orbit == orbit:
                box_color = (0, 0, 255)  # Red for selected
                text_color = (255, 255, 255)
            elif state == "PENDING" and max_orbit == orbit:
                box_color = (0, 255, 0)  # Green for pending
                text_color = (255, 255, 255)
            elif state == "PERFORMING" and max_orbit == orbit:
                box_color = (0, 255, 255)  # Yellow for performing
                text_color = (0, 0, 0)
            elif correlation > 0.7:
                box_color = (0, 200, 200)  # Light yellow
                text_color = (0, 0, 0)
            elif correlation > 0.5:
                box_color = (100, 100, 0)  # Dark cyan
                text_color = (200, 200, 200)
            else:
                box_color = (40, 40, 40)  # Dark gray
                text_color = (150, 150, 150)
            
            # Draw background box
            box_size = 140
            overlay = frame.copy()
            cv2.rectangle(overlay, 
                         (center_x - box_size//2, center_y - box_size//2),
                         (center_x + box_size//2, center_y + box_size//2),
                         box_color, -1)
            frame[:] = cv2.addWeighted(frame, 0.7, overlay, 0.3, 0)
            
            # Draw orbit path (circle)
            cv2.circle(frame, (center_x, center_y), orbit_display_radius, (100, 100, 100), 2)
            
            # Draw center dot
            cv2.circle(frame, (center_x, center_y), 3, (150, 150, 150), -1)
            
            # Draw orbiting ball
            cv2.circle(frame, (ball_x, ball_y), 12, (0, 255, 255), -1)
            cv2.circle(frame, (ball_x, ball_y), 14, (255, 255, 255), 2)
            
            # Draw direction arrow
            arrow_len = 15
            angle = orbit.theta + (math.pi/6 if orbit.clockwise else -math.pi/6)
            arrow_end_x = int(ball_x + arrow_len * math.cos(angle))
            arrow_end_y = int(ball_y + arrow_len * math.sin(angle))
            cv2.arrowedLine(frame, (ball_x, ball_y), (arrow_end_x, arrow_end_y), 
                           (255, 255, 255), 2, tipLength=0.5)
            
            # Label
            label = self.gesture_commands[orbit.name]
            label_y = center_y - box_size//2 - 10
            
            # Add speed indicator
            if "Slow" in str(orbit.period) or orbit.period >= 2.5:
                speed_str = "SLOW"
            elif orbit.period <= 1.7:
                speed_str = "FAST"
            else:
                speed_str = "MED"
            
            direction_str = "CW" if orbit.clockwise else "CCW"
            full_label = f"{label} ({speed_str} {direction_str})"
            
            cv2.putText(frame, full_label, (center_x - box_size//2, label_y),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.35, text_color, 1)
            
            # Show correlation if above threshold
            if correlation > 0.3:
                corr_text = f"{correlation:.2f}"
                cv2.putText(frame, corr_text, (center_x - 15, center_y + box_size//2 + 20),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.4, text_color, 1)
        
        # Draw hand trace (optional - show recent hand positions)
        if hand_pos and state != "INACTIVE":
            # Scale hand position to same region as first orbit for reference
            ref_center_x = start_x
            ref_center_y = start_y
            
            hand_screen_x = int(hand_pos[0] * w)
            hand_screen_y = int(hand_pos[1] * h)
            
            # Draw small hand indicator
            cv2.circle(frame, (hand_screen_x, hand_screen_y), 8, (255, 0, 255), 2)
    
    def cleanup(self):
        """Release resources."""
        if self.cap:
            self.cap.release()
        if self.tv_cap:
            self.tv_cap.release()
        cv2.destroyAllWindows()
        self.hands.close()
        print("TV Orbit Controller Stopped")


def main():
    controller = TVOrbitController()
    controller.start()


if __name__ == "__main__":
    main()
