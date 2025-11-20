import cv2
import mediapipe as mp
import numpy as np
from gesture_recognizer import GestureRecognizer


class HandGestureDetector:
    """
    Real-time hand gesture detection system using MediaPipe and OpenCV.
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
        
        # Video capture
        self.cap = None
        
        # UI colors
        self.color_hand = (0, 255, 0)  # Green
        self.color_gesture = (255, 100, 0)  # Blue-ish
        self.color_text = (255, 255, 255)  # White
        
        # Animation for templates
        self.frame_count = 0
        
    def start(self):
        """Start the video capture and gesture detection loop."""
        self.cap = cv2.VideoCapture(0)
        
        if not self.cap.isOpened():
            print("Error: Could not open camera")
            return
        
        # Set camera properties
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
        
        print("Hand Gesture Detection Started")
        print("=" * 50)
        print("HOW TO USE:")
        print("  1. See the 3 animated gestures on the right")
        print("  2. Follow the moving yellow ball with your hand cursor")
        print("  3. Stay close and match the timing for ~2 seconds")
        print("  4. Box turns GREEN when you're matching well (70%+)")
        print("  5. Gesture detected when you maintain high sync")
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
            cv2.imshow('Hand Gesture Detection', annotated_frame)
            
            # Handle key presses
            key = cv2.waitKey(1) & 0xFF
            if key == ord('q'):
                break
            elif key == ord('r'):
                self.gesture_recognizer.reset()
                print("Gesture detection reset")
        
        self.cleanup()
    
    def process_frame(self, frame):
        """
        Process a single frame to detect hands and gestures.
        
        Args:
            frame: BGR image from camera
            
        Returns:
            Annotated frame with hand landmarks and gesture info
        """
        # Convert to RGB for MediaPipe
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        
        # Detect hands
        results = self.hands.process(rgb_frame)
        
        # Draw hand landmarks
        if results.multi_hand_landmarks:
            for hand_landmarks in results.multi_hand_landmarks:
                # Draw landmarks
                self.mp_drawing.draw_landmarks(
                    frame,
                    hand_landmarks,
                    self.mp_hands.HAND_CONNECTIONS,
                    self.mp_drawing_styles.get_default_hand_landmarks_style(),
                    self.mp_drawing_styles.get_default_hand_connections_style()
                )
                
                # Add position to gesture recognizer
                self.gesture_recognizer.add_hand_position(hand_landmarks.landmark)
                
                # Draw hand cursor
                self._draw_hand_cursor(frame)
        
        # Detect gesture
        gesture, confidence = self.gesture_recognizer.detect_gesture()
        
        # Draw UI elements
        self._draw_ui(frame, gesture, confidence, results.multi_hand_landmarks is not None)
        
        return frame
    
    def _draw_hand_cursor(self, frame):
        """Draw a cursor at the current hand position."""
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
    
    def _draw_hand_trail(self, frame):
        """Draw the trail of hand movement."""
        if len(self.gesture_recognizer.position_history) < 2:
            return
        
        h, w, _ = frame.shape
        positions = list(self.gesture_recognizer.position_history)
        
        # Draw trail with fading effect
        for i in range(1, len(positions)):
            pt1 = (int(positions[i-1][0] * w), int(positions[i-1][1] * h))
            pt2 = (int(positions[i][0] * w), int(positions[i][1] * h))
            
            # Fade color based on position in history
            alpha = i / len(positions)
            color = (int(100 * alpha), int(200 * alpha), int(255 * alpha))
            thickness = max(1, int(3 * alpha))
            
            cv2.line(frame, pt1, pt2, color, thickness)
    
    def _draw_ui(self, frame, gesture, confidence, hand_detected):
        """Draw UI overlay with gesture information."""
        h, w, _ = frame.shape
        
        # Create semi-transparent overlay for info panel
        overlay = frame.copy()
        
        # Top panel
        cv2.rectangle(overlay, (0, 0), (w, 120), (0, 0, 0), -1)
        frame_blend = cv2.addWeighted(frame, 0.6, overlay, 0.4, 0)
        frame[:120] = frame_blend[:120]
        
        # Title
        cv2.putText(frame, "Hand Gesture Detection", (20, 40),
                   cv2.FONT_HERSHEY_SIMPLEX, 1.2, self.color_text, 2)
        
        # Hand detection status
        status_text = "Hand Detected" if hand_detected else "No Hand Detected"
        status_color = (0, 255, 0) if hand_detected else (0, 0, 255)
        cv2.putText(frame, status_text, (20, 80),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, status_color, 2)
        
        # Current gesture
        if gesture:
            gesture_desc = self.gesture_recognizer.get_gesture_description(gesture)
            conf_percent = int(confidence * 100)
            
            # Gesture panel
            panel_y = 140
            panel_h = 100
            cv2.rectangle(overlay, (0, panel_y), (w, panel_y + panel_h), (0, 50, 0), -1)
            frame_blend = cv2.addWeighted(frame, 0.5, overlay, 0.5, 0)
            frame[panel_y:panel_y + panel_h] = frame_blend[panel_y:panel_y + panel_h]
            
            cv2.putText(frame, f"Gesture: {gesture_desc}", (20, panel_y + 40),
                       cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 255, 0), 2)
            cv2.putText(frame, f"Confidence: {conf_percent}%", (20, panel_y + 75),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)
        
        # Gesture templates (right side) - animate the gestures
        self._draw_gesture_templates(frame)
        
        # Controls info (bottom left)
        controls_y = h - 60
        cv2.putText(frame, "Press 'q' to quit | Press 'r' to reset", (20, controls_y),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, (200, 200, 200), 1)
    
    def _draw_gesture_templates(self, frame):
        """Draw animated gesture templates on the right side of the frame."""
        h, w, _ = frame.shape
        
        # Position for templates (right side, stacked vertically)
        start_x = w - 400
        start_y = 100
        template_size = 200
        spacing = 230
        
        gestures = ['CIRCLE_CLOCKWISE', 'CIRCLE_COUNTER_CLOCKWISE', 'TRIANGLE']
        labels = ['Clockwise Circle', 'Counter-Clockwise', 'Triangle']
        
        # Store sync scores for this frame
        sync_data = {}
        
        for idx, (gesture_name, label) in enumerate(zip(gestures, labels)):
            # Get template from recognizer
            template = self.gesture_recognizer.get_template(gesture_name)
            if template is None:
                continue
            
            # Calculate position for this template
            box_x = start_x
            box_y = start_y + idx * spacing
            
            # Animate the template (ball following the path)
            total_points = len(template)
            anim_speed = 0.5  # Points per frame (slower)
            current_idx = int(self.frame_count * anim_speed) % total_points
            
            # Check sync with current animation position
            sync_score = self.gesture_recognizer.check_sync_with_template(
                gesture_name, current_idx, box_x, box_y, template_size
            )
            sync_data[gesture_name] = sync_score
            
            # Determine box color based on sync score
            if sync_score > 0.7:
                box_color = (0, 200, 0)  # Green - excellent match
            elif sync_score > 0.5:
                box_color = (0, 200, 200)  # Yellow - okay match
            else:
                box_color = (40, 40, 40)  # Gray - poor match
            
            # Draw semi-transparent background with color based on sync
            overlay = frame.copy()
            cv2.rectangle(overlay, (box_x - 10, box_y - 10),
                         (box_x + template_size + 10, box_y + template_size + 40),
                         box_color, -1)
            frame[:] = cv2.addWeighted(frame, 0.7, overlay, 0.3, 0)
            
            # Draw label with sync percentage
            sync_percent = int(sync_score * 100)
            label_text = f"{label} ({sync_percent}%)"
            cv2.putText(frame, label_text, (box_x, box_y - 15),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (200, 200, 200), 1)
            
            # Draw the full template path (faded)
            for i in range(1, total_points):
                pt1 = template[i-1]
                pt2 = template[i]
                x1 = int(box_x + pt1[0] * template_size)
                y1 = int(box_y + pt1[1] * template_size)
                x2 = int(box_x + pt2[0] * template_size)
                y2 = int(box_y + pt2[1] * template_size)
                cv2.line(frame, (x1, y1), (x2, y2), (100, 100, 100), 1)
            
            # Draw the animated ball (larger)
            ball_pos = template[current_idx]
            ball_x = int(box_x + ball_pos[0] * template_size)
            ball_y = int(box_y + ball_pos[1] * template_size)
            cv2.circle(frame, (ball_x, ball_y), 12, (0, 255, 255), -1)
            cv2.circle(frame, (ball_x, ball_y), 14, (255, 255, 255), 2)
            
            # Draw trailing effect (longer trail for slower animation)
            trail_length = 5
            for i in range(1, min(trail_length, current_idx + 1)):
                if current_idx - i >= 0:
                    trail_idx = current_idx - i
                    trail_pos = template[trail_idx]
                    trail_x = int(box_x + trail_pos[0] * template_size)
                    trail_y = int(box_y + trail_pos[1] * template_size)
                    alpha = 1.0 - (i / trail_length)
                    radius = int(8 * alpha)
                    color = (0, int(200 * alpha), int(200 * alpha))
                    cv2.circle(frame, (trail_x, trail_y), radius, color, -1)
        
        # Update sync scores in recognizer
        self.gesture_recognizer.update_sync_scores(sync_data)
    
    def cleanup(self):
        """Release resources."""
        if self.cap:
            self.cap.release()
        cv2.destroyAllWindows()
        self.hands.close()
        print("Hand Gesture Detection Stopped")


def main():
    """Main entry point."""
    detector = HandGestureDetector()
    detector.start()


if __name__ == "__main__":
    main()
