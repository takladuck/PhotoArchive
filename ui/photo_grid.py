from PySide6.QtWidgets import (QWidget, QGridLayout, QLabel, QScrollArea,
                            QSizePolicy, QVBoxLayout, QFrame, QHBoxLayout)
from PySide6.QtCore import Qt, Signal, QSize, QMargins, QRect
from PySide6.QtGui import QPixmap, QImage, QFont, QPainter, QColor, QPainterPath, QBrush, QPen

from .styling import THUMBNAIL_STYLESHEET, SELECTED_THUMBNAIL_STYLESHEET, COLORS

class PhotoThumbnail(QFrame):
    """Custom widget for photo and video thumbnails with click functionality"""
    clicked = Signal(dict)
    double_clicked = Signal(dict)

    def __init__(self, photo_data):
        super().__init__()
        self.photo_data = photo_data
        self.selected = False
        self.is_video = photo_data.get('file_type') == 'video'
        self.setFixedSize(220, 220)

        # Apply custom shadow effect using stylesheet
        self.setStyleSheet("""
            QFrame {
                background-color: """ + COLORS['card'] + """;
                border-radius: 8px;
                border: none;
            }
        """)

        # Enable shadow effects
        self.setGraphicsEffect(self._create_shadow_effect())

        # Main layout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)

        # Image container (for displaying the thumbnail)
        self.image_container = QLabel()
        self.image_container.setAlignment(Qt.AlignCenter)
        self.image_container.setMinimumSize(200, 160)
        self.image_container.setMaximumSize(200, 160)
        self.image_container.setScaledContents(False)
        self.image_container.setStyleSheet("background-color: transparent; border: none;")

        # Caption for file name and duration (for videos)
        self.caption = QLabel()
        self.caption.setAlignment(Qt.AlignCenter)
        self.caption.setMaximumWidth(200)
        self.caption.setWordWrap(True)
        self.caption.setStyleSheet(f"color: {COLORS['text']}; background-color: transparent; border: none;")
        self.caption.setFont(QFont("Segoe UI", 8))

        layout.addWidget(self.image_container)
        layout.addWidget(self.caption)

        self.load_thumbnail()

    def _create_shadow_effect(self):
        """Create a shadow effect for the thumbnail card"""
        from PySide6.QtWidgets import QGraphicsDropShadowEffect
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(15)
        shadow.setColor(QColor(0, 0, 0, 30))
        shadow.setOffset(0, 3)
        return shadow

    def load_thumbnail(self):
        """Load thumbnail from the file path with high quality"""
        # Set the file name caption
        file_name = self.photo_data['file_path'].split('/')[-1].split('\\')[-1]
        if len(file_name) > 25:
            file_name = file_name[:22] + "..."

        # Add duration info for videos
        caption_text = file_name
        if self.is_video and self.photo_data.get('duration'):
            duration = self.photo_data['duration']
            minutes = int(duration // 60)
            seconds = int(duration % 60)
            caption_text += f"\n{minutes:02d}:{seconds:02d}"

        self.caption.setText(caption_text)

        if self.photo_data.get('thumbnail_path'):
            pixmap = QPixmap(self.photo_data['thumbnail_path'])
            if not pixmap.isNull():
                # Use high quality scaling with aspect ratio preservation
                pixmap = pixmap.scaled(
                    QSize(200, 180),
                    Qt.KeepAspectRatio,
                    Qt.SmoothTransformation
                )

                # Add play icon overlay for videos
                if self.is_video:
                    pixmap = self._add_play_icon_overlay(pixmap)

                self.image_container.setPixmap(pixmap)
            else:
                self.image_container.setText("Error loading thumbnail")
        else:
            # If no thumbnail, try to load from original (for images only)
            if not self.is_video:
                try:
                    pixmap = QPixmap(self.photo_data['file_path'])
                    if not pixmap.isNull():
                        pixmap = pixmap.scaled(
                            QSize(200, 180),
                            Qt.KeepAspectRatio,
                            Qt.SmoothTransformation
                        )
                        self.image_container.setPixmap(pixmap)
                    else:
                        self.image_container.setText("Error loading image")
                except:
                    self.image_container.setText("Error loading image")
            else:
                self.image_container.setText("Video thumbnail unavailable")

    def _add_play_icon_overlay(self, pixmap):
        """Add a play icon overlay to video thumbnails"""
        # Create a new pixmap to draw on
        overlay_pixmap = QPixmap(pixmap)
        painter = QPainter(overlay_pixmap)
        painter.setRenderHint(QPainter.Antialiasing)

        # Semi-transparent dark overlay
        overlay_rect = QRect(0, 0, overlay_pixmap.width(), overlay_pixmap.height())
        painter.fillRect(overlay_rect, QColor(0, 0, 0, 50))

        # Draw play button in center
        center_x = overlay_pixmap.width() // 2
        center_y = overlay_pixmap.height() // 2
        play_size = min(overlay_pixmap.width(), overlay_pixmap.height()) // 6

        # Create play triangle
        play_triangle = [
            (center_x - play_size//2, center_y - play_size//2),
            (center_x - play_size//2, center_y + play_size//2),
            (center_x + play_size//2, center_y)
        ]

        # Draw white play button with border
        painter.setPen(QPen(QColor(255, 255, 255), 2))
        painter.setBrush(QBrush(QColor(255, 255, 255, 200)))

        from PySide6.QtGui import QPolygon
        from PySide6.QtCore import QPoint

        points = [QPoint(x, y) for x, y in play_triangle]
        polygon = QPolygon(points)
        painter.drawPolygon(polygon)

        painter.end()
        return overlay_pixmap

    def set_selected(self, selected):
        """Set the selected state of the thumbnail"""
        self.selected = selected
        if selected:
            # Apply a highlighted border for selected items
            self.setStyleSheet(f"""
                QFrame {{
                    background-color: {COLORS['card']};
                    border-radius: 8px;
                    border: 2px solid {COLORS['primary']};
                }}
            """)
        else:
            # Normal state
            self.setStyleSheet(f"""
                QFrame {{
                    background-color: {COLORS['card']};
                    border-radius: 8px;
                    border: none;
                }}
            """)

    def mousePressEvent(self, event):
        """Handle mouse press to emit clicked signal"""
        self.clicked.emit(self.photo_data)
        super().mousePressEvent(event)

    def mouseDoubleClickEvent(self, event):
        """Handle mouse double click to open the photo"""
        self.double_clicked.emit(self.photo_data)
        super().mouseDoubleClickEvent(event)


class PhotoGrid(QScrollArea):
    """Grid view of photo thumbnails"""
    photo_clicked = Signal(dict)
    photo_double_clicked = Signal(dict)

    def __init__(self, db_manager):
        super().__init__()
        self.db_manager = db_manager
        self.photos = []
        self.current_index = -1
        self.thumbnails = []

        # Setup scroll area
        self.setWidgetResizable(True)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.setStyleSheet(f"background-color: {COLORS['background']}; border: none;")

        # Container widget and layout
        self.container = QWidget()
        self.container.setStyleSheet(f"background-color: {COLORS['background']};")
        self.grid_layout = QGridLayout(self.container)
        self.grid_layout.setSpacing(20)
        self.grid_layout.setContentsMargins(20, 20, 20, 20)
        self.setWidget(self.container)

    def load_photos(self, photos):
        """Load photos into the grid"""
        # Clear existing thumbnails
        while self.grid_layout.count():
            item = self.grid_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        self.photos = photos
        self.current_index = 0 if photos else -1
        self.thumbnails = []

        # Populate grid with thumbnails
        columns = max(1, (self.width() - 40) // 240)  # 220px + 20px spacing
        for i, photo in enumerate(photos):
            row = i // columns
            col = i % columns

            thumbnail = PhotoThumbnail(photo)
            thumbnail.clicked.connect(self.on_thumbnail_clicked)
            thumbnail.double_clicked.connect(self.on_thumbnail_double_clicked)
            self.grid_layout.addWidget(thumbnail, row, col)
            self.thumbnails.append(thumbnail)

        # Add empty row at the end for better spacing
        self.grid_layout.setRowStretch(len(photos) // columns + 1, 1)

        # Update selected state if we have photos
        if self.thumbnails and self.current_index >= 0:
            self.thumbnails[self.current_index].set_selected(True)

    def on_thumbnail_clicked(self, photo_data):
        """Handle thumbnail click - just select it"""
        # Clear previous selection
        if 0 <= self.current_index < len(self.thumbnails):
            self.thumbnails[self.current_index].set_selected(False)

        # Find the index of the clicked photo
        for i, photo in enumerate(self.photos):
            if photo['file_path'] == photo_data['file_path']:
                self.current_index = i
                # Update selection
                self.thumbnails[i].set_selected(True)
                break

        # Emit signal for selection (not opening)
        self.photo_clicked.emit(photo_data)

    def on_thumbnail_double_clicked(self, photo_data):
        """Handle thumbnail double click - open it"""
        # Emit signal for opening
        self.photo_double_clicked.emit(photo_data)

    def get_current_photo(self):
        """Get the current photo data"""
        if self.photos and 0 <= self.current_index < len(self.photos):
            return self.photos[self.current_index]
        return None

    def get_next_photo(self):
        """Get the next photo in the list"""
        if not self.photos:
            return None

        # Clear current selection
        if 0 <= self.current_index < len(self.thumbnails):
            self.thumbnails[self.current_index].set_selected(False)

        if self.current_index < len(self.photos) - 1:
            self.current_index += 1
            # Update selection
            self.thumbnails[self.current_index].set_selected(True)
            return self.photos[self.current_index]
        return None

    def get_prev_photo(self):
        """Get the previous photo in the list"""
        if not self.photos:
            return None

        # Clear current selection
        if 0 <= self.current_index < len(self.thumbnails):
            self.thumbnails[self.current_index].set_selected(False)

        if self.current_index > 0:
            self.current_index -= 1
            # Update selection
            self.thumbnails[self.current_index].set_selected(True)
            return self.photos[self.current_index]
        return None
