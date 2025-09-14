from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                            QPushButton, QSizePolicy, QScrollArea, QFrame, QGraphicsDropShadowEffect,
                            QGraphicsView, QGraphicsScene, QSlider, QToolButton)
from PySide6.QtCore import Qt, Signal, QSize, QPoint, QTimer, QRectF, QPointF
from PySide6.QtGui import (QPixmap, QImage, QKeyEvent, QFont, QIcon, QColor,
                         QTransform, QWheelEvent, QCursor, QPainter, QPainterPath)
from PySide6.QtWidgets import QStyle

from .styling import PHOTO_VIEWER_STYLESHEET, INFO_PANEL_STYLESHEET, COLORS

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
        self.zoom_factor = 1.0

        # Set zoom limits
        self.min_zoom = 0.1  # Don't allow zooming out beyond 10% of original size
        self.max_zoom = 5.0  # Don't allow zooming in beyond 500% of original size

        # Setup appearance - use integers for render hints to ensure compatibility
        self.setRenderHint(QPainter.Antialiasing, True)
        self.setRenderHint(QPainter.SmoothPixmapTransform, True)
        # No HighQualityAntialiasing in some PySide6 versions

        self.setBackgroundBrush(QColor("#121212"))
        self.setFrameShape(QFrame.NoFrame)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.setTransformationAnchor(QGraphicsView.AnchorUnderMouse)
        self.setResizeAnchor(QGraphicsView.AnchorViewCenter)
        self.setInteractive(True)
        self.setDragMode(QGraphicsView.ScrollHandDrag)

    def set_image(self, pixmap):
        """Set a new image to display"""
        self.scene().clear()
        if pixmap and not pixmap.isNull():
            self.current_pixmap = pixmap
            self.current_pixmap_item = self.scene().addPixmap(pixmap)
            self.current_pixmap_item.setTransformationMode(Qt.SmoothTransformation)
            self.scene().setSceneRect(QRectF(self.current_pixmap_item.boundingRect()))
            self.fit_in_view()

    def fit_in_view(self):
        """Scale the image to fit within the viewport"""
        if self.current_pixmap_item:
            self.fitInView(self.current_pixmap_item, Qt.KeepAspectRatio)
            # Reset the zoom factor
            self.zoom_factor = 1.0

    def wheelEvent(self, event):
        """Handle mouse wheel events for zooming with limits"""
        if self.current_pixmap_item:
            # Determine zoom direction
            zoom_in = event.angleDelta().y() > 0

            # Zoom factor per step
            factor = 1.1 if zoom_in else 0.9

            # Calculate new zoom factor
            new_zoom = self.zoom_factor * factor

            # Check zoom limits
            if new_zoom < self.min_zoom:
                factor = self.min_zoom / self.zoom_factor
            elif new_zoom > self.max_zoom:
                factor = self.max_zoom / self.zoom_factor

            # Apply zoom if within limits
            if self.min_zoom <= new_zoom <= self.max_zoom:
                self.scale(factor, factor)
                self.zoom_factor = new_zoom

    def keyPressEvent(self, event):
        """Handle key press events"""
        if event.key() == Qt.Key_F:
            self.fit_in_view()
        else:
            super().keyPressEvent(event)

    def resizeEvent(self, event):
        """Auto fit when window is resized"""
        if self.current_pixmap_item and self.zoom_factor == 1.0:
            self.fit_in_view()
        super().resizeEvent(event)


class PhotoViewer(QWidget):
    """Single photo viewer with navigation controls"""
    close_signal = Signal()
    next_signal = Signal()
    prev_signal = Signal()

    def __init__(self):
        super().__init__()
        self.current_photo = None

        # Set darker background for photo viewing
        self.setStyleSheet("background-color: #121212;")

        # Main layout
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Top toolbar with info and controls - semi-transparent dark bar
        toolbar_widget = QFrame()
        toolbar_widget.setStyleSheet("background-color: rgba(0, 0, 0, 0.8); color: white;")
        toolbar_widget.setMinimumHeight(50)
        toolbar_layout = QHBoxLayout(toolbar_widget)
        toolbar_layout.setContentsMargins(16, 8, 16, 8)

        # Button styling for dark background
        button_style = """
            QPushButton {
                background-color: rgba(255, 255, 255, 0.2);
                color: white;
                border: none;
                border-radius: 4px;
                padding: 8px 16px;
            }
            QPushButton:hover {
                background-color: rgba(255, 255, 255, 0.3);
            }
            QPushButton:pressed {
                background-color: rgba(255, 255, 255, 0.4);
            }
        """

        # Back button with standard icon
        self.back_btn = QPushButton(" Back to Grid")
        self.back_btn.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_DialogCloseButton))
        self.back_btn.setStyleSheet(button_style)
        self.back_btn.clicked.connect(self.close_view)
        toolbar_layout.addWidget(self.back_btn)

        # Navigation buttons with standard icons
        nav_layout = QHBoxLayout()
        nav_layout.setSpacing(10)

        self.prev_btn = QPushButton(" Previous")
        self.prev_btn.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_ArrowBack))
        self.prev_btn.setStyleSheet(button_style)
        self.prev_btn.clicked.connect(self.prev_photo)
        nav_layout.addWidget(self.prev_btn)

        self.next_btn = QPushButton(" Next")
        self.next_btn.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_ArrowForward))
        self.next_btn.setStyleSheet(button_style)
        self.next_btn.clicked.connect(self.next_photo)
        nav_layout.addWidget(self.next_btn)

        toolbar_layout.addLayout(nav_layout)

        # Zoom controls
        zoom_layout = QHBoxLayout()
        zoom_layout.setSpacing(5)

        # Fit button
        self.fit_btn = QPushButton("Fit")
        self.fit_btn.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_DialogResetButton))
        self.fit_btn.setStyleSheet(button_style)
        self.fit_btn.clicked.connect(self.fit_image)
        self.fit_btn.setToolTip("Fit image to view (Space)")
        zoom_layout.addWidget(self.fit_btn)

        # Zoom in button
        self.zoom_in_btn = QPushButton("+")
        self.zoom_in_btn.setStyleSheet(button_style)
        self.zoom_in_btn.clicked.connect(self.zoom_in)
        self.zoom_in_btn.setToolTip("Zoom in")
        zoom_layout.addWidget(self.zoom_in_btn)

        # Zoom out button
        self.zoom_out_btn = QPushButton("-")
        self.zoom_out_btn.setStyleSheet(button_style)
        self.zoom_out_btn.clicked.connect(self.zoom_out)
        self.zoom_out_btn.setToolTip("Zoom out")
        zoom_layout.addWidget(self.zoom_out_btn)

        toolbar_layout.addLayout(zoom_layout)

        # Spacer
        toolbar_layout.addStretch()

        # Photo info
        self.info_label = QLabel()
        self.info_label.setStyleSheet("color: white; font-size: 11px; background-color: transparent;")
        self.info_label.setFont(QFont("Segoe UI", 9))
        toolbar_layout.addWidget(self.info_label)

        main_layout.addWidget(toolbar_widget)

        # Photo viewer widget with navigation arrows
        photo_container = QWidget()
        photo_container_layout = QHBoxLayout(photo_container)
        photo_container_layout.setContentsMargins(0, 0, 0, 0)
        photo_container_layout.setSpacing(0)

        self.photo_view = PhotoViewerWidget()
        photo_container_layout.addWidget(self.photo_view)

        main_layout.addWidget(photo_container)

        # Create floating arrow buttons
        self.left_arrow = ArrowButton("left", self)
        self.left_arrow.clicked.connect(self.prev_photo)
        self.left_arrow.setToolTip("Previous photo (Left arrow)")

        self.right_arrow = ArrowButton("right", self)
        self.right_arrow.clicked.connect(self.next_photo)
        self.right_arrow.setToolTip("Next photo (Right arrow)")

        # Timer for hiding arrows
        self.arrow_timer = QTimer(self)
        self.arrow_timer.timeout.connect(self.hide_arrows)
        self.arrow_timer.setSingleShot(True)

        # Floating info panel (displays when hovering)
        self.detail_panel = QFrame(self)
        self.detail_panel.setStyleSheet("""
            background-color: rgba(0, 0, 0, 0.7);
            color: white;
            border-radius: 8px;
            padding: 4px;
        """)
        self.detail_panel.setFixedWidth(300)
        panel_layout = QVBoxLayout(self.detail_panel)
        panel_layout.setContentsMargins(12, 12, 12, 12)
        panel_layout.setSpacing(8)

        self.detail_file_label = QLabel()
        self.detail_file_label.setFont(QFont("Segoe UI", 10, QFont.Bold))
        self.detail_file_label.setWordWrap(True)
        self.detail_file_label.setStyleSheet("color: white;")

        self.detail_date_label = QLabel()
        self.detail_date_label.setFont(QFont("Segoe UI", 9))
        self.detail_date_label.setStyleSheet("color: #cccccc;")

        self.detail_size_label = QLabel()
        self.detail_size_label.setFont(QFont("Segoe UI", 9))
        self.detail_size_label.setStyleSheet("color: #cccccc;")

        panel_layout.addWidget(self.detail_file_label)
        panel_layout.addWidget(self.detail_date_label)
        panel_layout.addWidget(self.detail_size_label)

        self.detail_panel.hide()
        self.detail_panel_timer = QTimer(self)
        self.detail_panel_timer.timeout.connect(self.hide_detail_panel)

        # Ensure the widget can receive keyboard focus
        self.setFocusPolicy(Qt.StrongFocus)

    def show_arrows(self):
        """Show navigation arrows"""
        if self.current_photo:
            self.left_arrow.show()
            self.right_arrow.show()
            self.position_arrows()

            # Hide arrows after 3 seconds of no mouse movement
            self.arrow_timer.start(3000)

    def hide_arrows(self):
        """Hide navigation arrows"""
        self.left_arrow.hide()
        self.right_arrow.hide()

    def position_arrows(self):
        """Position the arrow buttons on the sides of the photo viewer"""
        if not self.photo_view:
            return

        viewer_rect = self.photo_view.geometry()

        # Position left arrow
        left_x = 20
        left_y = viewer_rect.height() // 2 - self.left_arrow.height() // 2
        self.left_arrow.move(left_x, left_y + viewer_rect.y())

        # Position right arrow
        right_x = viewer_rect.width() - self.right_arrow.width() - 20
        right_y = viewer_rect.height() // 2 - self.right_arrow.height() // 2
        self.right_arrow.move(right_x, right_y + viewer_rect.y())

    def resizeEvent(self, event):
        """Reposition arrows when window is resized"""
        super().resizeEvent(event)
        self.position_arrows()

    def enterEvent(self, event):
        """Show arrows when mouse enters the widget"""
        self.show_arrows()
        super().enterEvent(event)

    def mouseMoveEvent(self, event):
        """Show arrows and detail panel on mouse move"""
        self.show_arrows()

        # Show detail panel
        self.detail_panel.move(event.position().x() + 10, event.position().y() + 10)
        self.detail_panel.show()

        # Reset timer
        self.detail_panel_timer.stop()
        self.detail_panel_timer.start(2000)  # Hide after 2 seconds

        super().mouseMoveEvent(event)

    def leaveEvent(self, event):
        """Hide arrows when mouse leaves the widget"""
        self.arrow_timer.start(1000)  # Hide arrows after 1 second delay
        super().leaveEvent(event)

    def load_photo(self, photo_data):
        """Load and display a photo"""
        self.current_photo = photo_data

        if not photo_data:
            self.info_label.setText("")
            return

        # Load photo
        pixmap = QPixmap(photo_data['file_path'])
        if not pixmap.isNull():
            # Set the image to the viewer
            self.photo_view.set_image(pixmap)

            # Update info label
            file_name = photo_data['file_path'].split('/')[-1].split('\\')[-1]
            date_info = photo_data.get('date_taken', 'Unknown date')
            size_kb = photo_data.get('file_size', 0) / 1024
            dimensions = f"{pixmap.width()}x{pixmap.height()}"

            self.info_label.setText(f"{file_name} | {dimensions} | {size_kb:.1f} KB")

            # Update detail panel
            self.detail_file_label.setText(file_name)
            self.detail_date_label.setText(f"Date: {date_info}")
            self.detail_size_label.setText(f"Size: {size_kb:.1f} KB | {dimensions}")
        else:
            self.info_label.setText(photo_data['file_path'])

    def fit_image(self):
        """Fit the current image to the view"""
        self.photo_view.fit_in_view()

    def zoom_in(self):
        """Zoom in on the image"""
        self.photo_view.scale(1.2, 1.2)
        self.photo_view.zoom_factor *= 1.2

    def zoom_out(self):
        """Zoom out from the image"""
        self.photo_view.scale(0.8, 0.8)
        self.photo_view.zoom_factor *= 0.8

    def close_view(self):
        """Close the single photo view"""
        self.close_signal.emit()

    def next_photo(self):
        """Show next photo"""
        self.next_signal.emit()

    def prev_photo(self):
        """Show previous photo"""
        self.prev_signal.emit()

    def hide_detail_panel(self):
        """Hide the detail panel after timeout"""
        self.detail_panel.hide()
        self.detail_panel_timer.stop()

    def keyPressEvent(self, event):
        """Handle keyboard navigation"""
        key = event.key()

        if key == Qt.Key.Key_Escape:
            self.close_view()
        elif key == Qt.Key.Key_Right or key == Qt.Key.Key_Down:
            self.next_photo()
        elif key == Qt.Key.Key_Left or key == Qt.Key.Key_Up:
            self.prev_photo()
        elif key == Qt.Key.Key_Space or key == Qt.Key.Key_F:
            self.fit_image()
        elif key == Qt.Key.Key_Plus or key == Qt.Key.Key_Equal:
            self.zoom_in()
        elif key == Qt.Key.Key_Minus:
            self.zoom_out()
        else:
            super().keyPressEvent(event)
