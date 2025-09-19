from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
                            QLabel, QSlider, QFrame, QSizePolicy)
from PySide6.QtCore import Qt, Signal, QTimer, QUrl, QSize
from PySide6.QtGui import QFont, QPixmap
from PySide6.QtMultimedia import QMediaPlayer, QAudioOutput
from PySide6.QtMultimediaWidgets import QVideoWidget

from .styling import COLORS

class VideoViewer(QWidget):
    """Video viewer widget with playback controls"""

    def __init__(self):
        super().__init__()
        self.current_video_data = None
        self.setup_ui()
        self.setup_media_player()

    def setup_ui(self):
        """Setup the user interface"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Video widget
        self.video_widget = QVideoWidget()
        self.video_widget.setStyleSheet(f"background-color: {COLORS['background']};")
        layout.addWidget(self.video_widget)

        # Controls panel
        controls_frame = QFrame()
        controls_frame.setFixedHeight(80)
        controls_frame.setStyleSheet(f"""
            QFrame {{
                background-color: {COLORS['surface']};
                border-top: 1px solid {COLORS['border']};
            }}
        """)

        controls_layout = QVBoxLayout(controls_frame)
        controls_layout.setContentsMargins(20, 10, 20, 10)

        # Progress slider
        self.progress_slider = QSlider(Qt.Horizontal)
        self.progress_slider.setStyleSheet(f"""
            QSlider::groove:horizontal {{
                background: {COLORS['border']};
                height: 4px;
                border-radius: 2px;
            }}
            QSlider::handle:horizontal {{
                background: {COLORS['primary']};
                width: 16px;
                height: 16px;
                border-radius: 8px;
                margin: -6px 0;
            }}
            QSlider::sub-page:horizontal {{
                background: {COLORS['primary']};
                border-radius: 2px;
            }}
        """)
        self.progress_slider.sliderPressed.connect(self.on_slider_pressed)
        self.progress_slider.sliderReleased.connect(self.on_slider_released)
        controls_layout.addWidget(self.progress_slider)

        # Control buttons and time labels
        button_layout = QHBoxLayout()

        # Play/Pause button
        self.play_button = QPushButton("▶")
        self.play_button.setFixedSize(40, 40)
        self.play_button.setStyleSheet(f"""
            QPushButton {{
                background-color: {COLORS['primary']};
                color: white;
                border: none;
                border-radius: 20px;
                font-size: 16px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: {COLORS['primary_hover']};
            }}
        """)
        self.play_button.clicked.connect(self.toggle_playback)
        button_layout.addWidget(self.play_button)

        # Time labels
        self.time_label = QLabel("00:00 / 00:00")
        self.time_label.setStyleSheet(f"color: {COLORS['text']}; font-size: 12px;")
        button_layout.addWidget(self.time_label)

        button_layout.addStretch()

        # Volume control
        volume_label = QLabel("🔊")
        volume_label.setStyleSheet(f"color: {COLORS['text']};")
        button_layout.addWidget(volume_label)

        self.volume_slider = QSlider(Qt.Horizontal)
        self.volume_slider.setFixedWidth(100)
        self.volume_slider.setRange(0, 100)
        self.volume_slider.setValue(50)
        self.volume_slider.setStyleSheet(self.progress_slider.styleSheet())
        self.volume_slider.valueChanged.connect(self.on_volume_changed)
        button_layout.addWidget(self.volume_slider)

        controls_layout.addLayout(button_layout)
        layout.addWidget(controls_frame)

    def setup_media_player(self):
        """Setup the media player"""
        self.media_player = QMediaPlayer()
        self.audio_output = QAudioOutput()
        self.media_player.setAudioOutput(self.audio_output)
        self.media_player.setVideoOutput(self.video_widget)

        # Connect signals
        self.media_player.positionChanged.connect(self.on_position_changed)
        self.media_player.durationChanged.connect(self.on_duration_changed)
        self.media_player.playbackStateChanged.connect(self.on_playback_state_changed)

        # Timer for updating UI
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.update_ui)
        self.update_timer.start(100)  # Update every 100ms

        # Set initial volume
        self.audio_output.setVolume(0.5)

    def load_video(self, video_data):
        """Load a video file"""
        self.current_video_data = video_data
        file_path = video_data['file_path']

        # Convert to QUrl for proper path handling
        url = QUrl.fromLocalFile(file_path)
        self.media_player.setSource(url)

        # Reset slider
        self.progress_slider.setValue(0)

    def toggle_playback(self):
        """Toggle play/pause"""
        if self.media_player.playbackState() == QMediaPlayer.PlayingState:
            self.media_player.pause()
        else:
            self.media_player.play()

    def on_playback_state_changed(self, state):
        """Handle playback state changes"""
        if state == QMediaPlayer.PlayingState:
            self.play_button.setText("⏸")
        else:
            self.play_button.setText("▶")

    def on_position_changed(self, position):
        """Handle position changes"""
        if not self.progress_slider.isSliderDown():
            self.progress_slider.setValue(position)

    def on_duration_changed(self, duration):
        """Handle duration changes"""
        self.progress_slider.setRange(0, duration)

    def on_slider_pressed(self):
        """Handle slider press"""
        pass

    def on_slider_released(self):
        """Handle slider release"""
        position = self.progress_slider.value()
        self.media_player.setPosition(position)

    def on_volume_changed(self, value):
        """Handle volume changes"""
        volume = value / 100.0
        self.audio_output.setVolume(volume)

    def update_ui(self):
        """Update UI elements"""
        if self.media_player.duration() > 0:
            position = self.media_player.position()
            duration = self.media_player.duration()

            # Format time strings
            pos_time = self.format_time(position)
            dur_time = self.format_time(duration)
            self.time_label.setText(f"{pos_time} / {dur_time}")

    def format_time(self, milliseconds):
        """Format time in milliseconds to MM:SS"""
        seconds = milliseconds // 1000
        minutes = seconds // 60
        seconds = seconds % 60
        return f"{minutes:02d}:{seconds:02d}"

    def stop(self):
        """Stop playback"""
        self.media_player.stop()

    def get_current_video_data(self):
        """Get current video data"""
        return self.current_video_data
