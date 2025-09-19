from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                            QPushButton, QSizePolicy, QScrollArea, QFrame, QGraphicsDropShadowEffect,
                            QGraphicsView, QGraphicsScene, QSlider, QToolButton, QStackedWidget)
from PySide6.QtCore import Qt, Signal, QSize, QPoint, QTimer, QRectF, QPointF
from PySide6.QtGui import (QPixmap, QImage, QKeyEvent, QFont, QIcon, QColor,
                         QTransform, QWheelEvent, QCursor, QPainter, QPainterPath)
from PySide6.QtWidgets import QStyle

from .styling import PHOTO_VIEWER_STYLESHEET, INFO_PANEL_STYLESHEET, COLORS
from .video_viewer import VideoViewer

class ArrowButton(QPushButton):
    """Custom arrow button that appears on hover"""

    def __init__(self, direction="left", parent=None):
        super().__init__(parent)
        self.direction = direction
        self.setFixedSize(60, 100)
        self.setStyleSheet("""
            QPushButton {
                background-color: rgba(0, 0, 0, 0.6);
                border: none;
                border-radius: 8px;
                color: white;
                font-size: 24px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: rgba(0, 0, 0, 0.8);
            }
            QPushButton:pressed {
                background-color: rgba(255, 255, 255, 0.2);
            }
        """)

        # Set arrow text based on direction
        if direction == "left":
            self.setText("‹")
        else:
            self.setText("›")

        # Initially hidden
        self.hide()

class PhotoViewerWidget(QGraphicsView):
    """Custom widget for displaying photos with pan and zoom functionality"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setScene(QGraphicsScene(self))
        self.current_pixmap_item = None
        self.current_pixmap = None

        # Configure the view
        self.setDragMode(QGraphicsView.ScrollHandDrag)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setRenderHints(QPainter.Antialiasing | QPainter.SmoothPixmapTransform)
        self.setStyleSheet(f"background-color: {COLORS['background']}; border: none;")

        # Track zoom level
        self.zoom_factor = 1.0
        self.max_zoom = 5.0
        self.min_zoom = 0.1

    def display_image(self, image_path):
        """Display an image in the viewer"""
        # Clear existing content
        self.scene().clear()
        self.current_pixmap = QPixmap(image_path)

        if not self.current_pixmap.isNull():
            self.current_pixmap_item = self.scene().addPixmap(self.current_pixmap)
            self.fit_image_to_view()
        else:
            # Display error message
            text_item = self.scene().addText("Error loading image", QFont("Arial", 16))
            text_item.setDefaultTextColor(QColor(COLORS['text']))

    def fit_image_to_view(self):
        """Fit the image to the view while maintaining aspect ratio"""
        if self.current_pixmap_item:
            self.fitInView(self.current_pixmap_item, Qt.KeepAspectRatio)
            self.zoom_factor = 1.0

    def wheelEvent(self, event):
        """Handle zoom with mouse wheel"""
        if self.current_pixmap_item:
            # Get the mouse position
            old_pos = self.mapToScene(event.position().toPoint())

            # Calculate zoom factor
            zoom_in = event.angleDelta().y() > 0
            if zoom_in and self.zoom_factor < self.max_zoom:
                factor = 1.25
                self.zoom_factor = min(self.zoom_factor * factor, self.max_zoom)
            elif not zoom_in and self.zoom_factor > self.min_zoom:
                factor = 0.8
                self.zoom_factor = max(self.zoom_factor * factor, self.min_zoom)
            else:
                return

            # Apply zoom
            self.scale(factor, factor)

            # Keep the mouse position centered
            new_pos = self.mapToScene(event.position().toPoint())
            delta = new_pos - old_pos
            self.translate(delta.x(), delta.y())

class PhotoViewer(QWidget):
    """Photo and Video viewer with navigation controls"""
    next_requested = Signal()
    prev_requested = Signal()
    closed = Signal()

    def __init__(self, photo_grid):
        super().__init__()
        self.photo_grid = photo_grid
        self.current_media_data = None
        self.setup_ui()
        self.setup_shortcuts()

    def setup_ui(self):
        """Setup the user interface"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Create main content area with stacked widget for image/video switching
        content_frame = QFrame()
        content_frame.setStyleSheet(f"background-color: {COLORS['background']};")
        content_layout = QHBoxLayout(content_frame)
        content_layout.setContentsMargins(0, 0, 0, 0)

        # Stacked widget to switch between image and video viewer
        self.stacked_widget = QStackedWidget()

        # Image viewer
        self.image_viewer = PhotoViewerWidget()
        self.stacked_widget.addWidget(self.image_viewer)

        # Video viewer
        self.video_viewer = VideoViewer()
        self.stacked_widget.addWidget(self.video_viewer)

        content_layout.addWidget(self.stacked_widget)

        # Navigation arrows (overlaid on the viewer)
        self.left_arrow = ArrowButton("left", content_frame)
        self.left_arrow.clicked.connect(self.show_previous)
        self.left_arrow.move(20, content_frame.height() // 2 - 50)

        self.right_arrow = ArrowButton("right", content_frame)
        self.right_arrow.clicked.connect(self.show_next)

        layout.addWidget(content_frame)

        # Info panel
        self.info_panel = self.create_info_panel()
        layout.addWidget(self.info_panel)

        # Setup mouse tracking for arrow visibility
        content_frame.setMouseTracking(True)
        self.stacked_widget.setMouseTracking(True)
        self.setMouseTracking(True)

    def create_info_panel(self):
        """Create the information panel at the bottom"""
        panel = QFrame()
        panel.setFixedHeight(60)
        panel.setStyleSheet(f"""
            QFrame {{
                background-color: {COLORS['surface']};
                border-top: 1px solid {COLORS['border']};
            }}
        """)

        layout = QHBoxLayout(panel)
        layout.setContentsMargins(20, 10, 20, 10)

        # File name label
        self.filename_label = QLabel()
        self.filename_label.setStyleSheet(f"color: {COLORS['text']}; font-size: 14px; font-weight: bold;")
        layout.addWidget(self.filename_label)

        layout.addStretch()

        # File info labels
        self.info_label = QLabel()
        self.info_label.setStyleSheet(f"color: {COLORS['text_secondary']}; font-size: 12px;")
        self.info_label.setAlignment(Qt.AlignRight)
        layout.addWidget(self.info_label)

        # Close button
        close_btn = QPushButton("✕")
        close_btn.setFixedSize(30, 30)
        close_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: transparent;
                color: {COLORS['text_secondary']};
                border: none;
                font-size: 16px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: {COLORS['error']};
                color: white;
                border-radius: 15px;
            }}
        """)
        close_btn.clicked.connect(self.close_viewer)
        layout.addWidget(close_btn)

        return panel

    def setup_shortcuts(self):
        """Setup keyboard shortcuts"""
        from PySide6.QtGui import QShortcut, QKeySequence

        # Navigation shortcuts
        QShortcut(QKeySequence(Qt.Key_Left), self, self.show_previous)
        QShortcut(QKeySequence(Qt.Key_Right), self, self.show_next)
        QShortcut(QKeySequence(Qt.Key_Escape), self, self.close_viewer)
        QShortcut(QKeySequence(Qt.Key_Space), self, self.toggle_playback)  # For videos

    def show_media(self, media_data):
        """Display media (image or video) with navigation"""
        self.current_media_data = media_data
        file_type = media_data.get('file_type', 'image')

        if file_type == 'video':
            # Show video viewer
            self.stacked_widget.setCurrentWidget(self.video_viewer)
            self.video_viewer.load_video(media_data)
        else:
            # Show image viewer
            self.stacked_widget.setCurrentWidget(self.image_viewer)
            self.image_viewer.display_image(media_data['file_path'])

        # Update info panel
        self.update_info_panel(media_data)

    def update_info_panel(self, media_data):
        """Update the information panel"""
        # File name
        file_name = media_data['file_path'].split('/')[-1].split('\\')[-1]
        self.filename_label.setText(file_name)

        # File info
        file_size = media_data.get('file_size', 0)
        file_size_mb = file_size / (1024 * 1024) if file_size else 0

        info_parts = []

        # File type and size
        file_type = media_data.get('file_type', 'image').title()
        info_parts.append(f"{file_type}")
        info_parts.append(f"{file_size_mb:.1f} MB")

        # Resolution
        if media_data.get('resolution'):
            info_parts.append(media_data['resolution'])

        # Duration for videos
        if media_data.get('duration'):
            duration = media_data['duration']
            minutes = int(duration // 60)
            seconds = int(duration % 60)
            info_parts.append(f"{minutes:02d}:{seconds:02d}")

        self.info_label.setText(" • ".join(info_parts))

    def show_next(self):
        """Show next media file"""
        next_media = self.photo_grid.get_next_photo()  # This now handles both photos and videos
        if next_media:
            self.show_media(next_media)
        self.next_requested.emit()

    def show_previous(self):
        """Show previous media file"""
        prev_media = self.photo_grid.get_prev_photo()  # This now handles both photos and videos
        if prev_media:
            self.show_media(prev_media)
        self.prev_requested.emit()

    def toggle_playback(self):
        """Toggle video playback (only for videos)"""
        if self.current_media_data and self.current_media_data.get('file_type') == 'video':
            self.video_viewer.toggle_playback()

    def close_viewer(self):
        """Close the viewer"""
        # Stop video playback if playing
        if self.current_media_data and self.current_media_data.get('file_type') == 'video':
            self.video_viewer.stop()
        self.closed.emit()

    def resizeEvent(self, event):
        """Handle window resize to reposition arrows"""
        super().resizeEvent(event)
        if hasattr(self, 'left_arrow') and hasattr(self, 'right_arrow'):
            # Reposition arrows
            content_height = self.height() - 60  # Subtract info panel height
            self.left_arrow.move(20, content_height // 2 - 50)
            self.right_arrow.move(self.width() - 80, content_height // 2 - 50)

    def enterEvent(self, event):
        """Show arrows when mouse enters"""
        if self.current_media_data:
            self.left_arrow.show()
            self.right_arrow.show()
        super().enterEvent(event)

    def leaveEvent(self, event):
        """Hide arrows when mouse leaves"""
        self.left_arrow.hide()
        self.right_arrow.hide()
        super().leaveEvent(event)
