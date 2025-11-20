import sys
import os
import vlc
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtWidgets import QApplication, QWidget, QLabel, QVBoxLayout, QStackedLayout

NUM_CHANNELS = 6
os.add_dll_directory(r"C:\Program Files\VideoLAN\VLC")


class TVSimulator(QWidget):
    def __init__(self):
        super().__init__()

        # --- Window setup ---
        self.setWindowTitle("TV Simulator")
        self.setGeometry(100, 100, 960, 540)
        self.setStyleSheet("background-color: black;")

        # --- VLC setup ---
        self.instance = vlc.Instance()
        self.player = self.instance.media_player_new()

        # --- Channel / Volume setup ---
        self.channels = [f"channel{i}.mp4" for i in range(1, NUM_CHANNELS + 1)]
        self.current_channel = 0
        self.volume = 50

        # --- Video frame for VLC output ---
        self.video_frame = QWidget(self)
        self.video_frame.setStyleSheet("background-color: black;")

        # --- Overlay setup ---
        self.overlay = QLabel("", self)
        self.overlay.setStyleSheet("""
            color: white;
            background-color: rgba(0, 0, 0, 180);
            font-size: 32px;
            border-radius: 12px;
            padding: 12px 24px;
        """)
        self.overlay.setAlignment(Qt.AlignCenter)
        self.overlay.setVisible(False)

        # Use stacked layout to layer overlay on top of video
        self.stack = QStackedLayout()
        self.stack.addWidget(self.video_frame)
        self.stack.addWidget(self.overlay)
        self.setLayout(self.stack)

        # Bind VLC output to the video frame
        self.player.set_hwnd(self.video_frame.winId())

        # --- Overlay timer ---
        self.overlay_timer = QTimer(self)
        self.overlay_timer.timeout.connect(self.hide_overlay)

        # --- Start first channel ---
        self.play_channel(self.current_channel)
        self.player.audio_set_volume(self.volume)

    def resizeEvent(self, event):
        """Keep overlay at bottom-center when window is resized."""
        super().resizeEvent(event)
        overlay_width = int(self.width() * 0.5)
        overlay_height = 60
        x = (self.width() - overlay_width) // 2
        y = self.height() - overlay_height - 40  # 40 px above bottom edge
        self.overlay.setGeometry(x, y, overlay_width, overlay_height)

    def play_channel(self, index):
        """Play video for the given channel index."""
        if not os.path.exists(self.channels[index]):
            self.show_overlay(f"Channel {index + 1} not found")
            return

        media = self.instance.media_new(self.channels[index])
        self.player.set_media(media)
        self.player.play()
        self.show_overlay(f"Channel: {index + 1}")

    def keyPressEvent(self, event):
        """Handle key presses for channel and volume control."""
        key = event.key()

        # Volume Up
        if key == Qt.Key_Up:
            self.volume = min(100, self.volume + 5)
            self.player.audio_set_volume(self.volume)
            self.show_overlay(f"Volume: {self.volume}%")

        # Volume Down
        elif key == Qt.Key_Down:
            self.volume = max(0, self.volume - 5)
            self.player.audio_set_volume(self.volume)
            self.show_overlay(f"Volume: {self.volume}%")

        # Channel Up
        elif key == Qt.Key_Right:
            self.current_channel = (self.current_channel + 1) % len(self.channels)
            self.play_channel(self.current_channel)

        # Channel Down
        elif key == Qt.Key_Left:
            self.current_channel = (self.current_channel - 1) % len(self.channels)
            self.play_channel(self.current_channel)

        # Exit
        elif key == Qt.Key_Escape:
            self.close()

    def show_overlay(self, text):
        """Display an on-screen overlay for feedback."""
        self.overlay.setText(text)
        self.overlay.adjustSize()
        self.overlay.setVisible(True)
        self.overlay.raise_()
        self.resizeEvent(None)  # reposition after adjusting size
        self.overlay_timer.start(2000)  # Hide after 2 seconds

    def hide_overlay(self):
        """Hide the overlay text."""
        self.overlay.setVisible(False)
        self.overlay_timer.stop()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    tv = TVSimulator()
    tv.show()
    sys.exit(app.exec_())
