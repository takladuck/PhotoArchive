from PySide6.QtWidgets import (QWidget, QLabel, QVBoxLayout, QProgressBar,
                             QGraphicsOpacityEffect)
from PySide6.QtCore import Qt, QPropertyAnimation, Property, Signal
from PySide6.QtGui import QPainter, QColor, QFont

class LoadingOverlay(QWidget):
    """
    A semi-transparent overlay with a loading indicator and message
    that can be shown on top of any widget during long operations
    """

    def __init__(self, parent=None):
        super().__init__(parent)

        # Make this a transparent overlay
        self.setAttribute(Qt.WA_TransparentForMouseEvents)
        self.setAttribute(Qt.WA_TranslucentBackground)

        # Set up the layout
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignCenter)

        # Message label
        self.message_label = QLabel("Loading...")
        self.message_label.setAlignment(Qt.AlignCenter)
        self.message_label.setStyleSheet("""
            color: white;
            font-size: 18px;
            font-weight: bold;
            background-color: transparent;
        """)
        self.message_label.setFont(QFont("Segoe UI", 14))

        # Progress info label
        self.progress_info = QLabel("")
        self.progress_info.setAlignment(Qt.AlignCenter)
        self.progress_info.setStyleSheet("""
            color: #cccccc;
            font-size: 12px;
            background-color: transparent;
        """)
        self.progress_info.setFont(QFont("Segoe UI", 10))

        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(True)
        self.progress_bar.setMinimumWidth(300)
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                background-color: rgba(0, 0, 0, 60);
                color: white;
                border-radius: 5px;
                text-align: center;
                height: 25px;
            }
            
            QProgressBar::chunk {
                background-color: #3498db;
                border-radius: 5px;
            }
        """)

        # Add widgets to layout
        layout.addWidget(self.message_label)
        layout.addWidget(self.progress_bar)
        layout.addWidget(self.progress_info)

        # Hide by default
        self.hide()

    def paintEvent(self, event):
        """Paint a semi-transparent dark background"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setBrush(QColor(0, 0, 0, 180))  # Semi-transparent black
        painter.setPen(Qt.NoPen)
        painter.drawRect(self.rect())
        super().paintEvent(event)

    def showEvent(self, event):
        """Center in parent when shown"""
        if self.parentWidget():
            self.resize(self.parentWidget().size())
        super().showEvent(event)

    def set_message(self, message):
        """Update the message text"""
        self.message_label.setText(message)

    def set_progress(self, value, max_value=100):
        """Update the progress bar"""
        if max_value > 0:
            percent = int((value / max_value) * 100)
            self.progress_bar.setValue(percent)
            self.progress_info.setText(f"Processing {value} of {max_value}")
        else:
            self.progress_bar.setValue(0)
            self.progress_info.setText("")

    def reset(self):
        """Reset the overlay to initial state"""
        self.set_message("Loading...")
        self.set_progress(0, 100)
