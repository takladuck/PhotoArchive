from PySide6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                            QPushButton, QFileDialog, QLabel, QComboBox, QGridLayout,
                            QScrollArea, QSizePolicy, QMessageBox, QFrame)
from PySide6.QtCore import Qt, QSize, Signal, Slot, QRect, QThread, QObject
from PySide6.QtGui import QPixmap, QImage, QIcon, QFont
from PySide6.QtWidgets import QStyle

from .photo_viewer import PhotoViewer
from .photo_grid import PhotoGrid
from .loading_overlay import LoadingOverlay
from .styling import MAIN_STYLESHEET, COLORS, TOOLBAR_STYLESHEET


class ImageProcessorWorker(QObject):
    """Worker object to process images and videos in a separate thread"""
    progress = Signal(int, int)  # current, total
    finished = Signal(list)      # processed media files
    error = Signal(str)          # error message

    def __init__(self, file_manager, db_manager, directory):
        super().__init__()
        self.file_manager = file_manager
        self.db_manager = db_manager
        self.directory = directory
        self.running = True

    def process_images(self):
        """Process images and videos in the given directory"""
        try:
            # Scan for images and videos
            media_files = self.file_manager.scan_directory(self.directory)
            total_files = len(media_files)
            processed_media = []

            # Process each media file
            for i, file_path in enumerate(media_files):
                if not self.running:
                    break

                # Extract metadata and create thumbnail
                metadata = self.file_manager.get_file_metadata(file_path)
                if metadata:
                    # Add to database with new fields
                    self.db_manager.add_photo(
                        file_path=metadata['file_path'],
                        file_hash=metadata['hash'],
                        date_taken=metadata['date_taken'],
                        location=metadata['location'],
                        thumbnail_path=metadata['thumbnail_path'],
                        file_size=metadata['file_size'],
                        last_modified=metadata['last_modified'],
                        file_type=metadata.get('file_type', 'image'),
                        duration=metadata.get('duration'),
                        resolution=metadata.get('resolution')
                    )
                    processed_media.append(metadata)

                # Emit progress
                self.progress.emit(i + 1, total_files)

            self.finished.emit(processed_media)

        except Exception as e:
            self.error.emit(str(e))

    def stop(self):
        """Stop processing"""
        self.running = False


class MainWindow(QMainWindow):
    def __init__(self, db_manager, file_manager):
        super().__init__()

        self.db_manager = db_manager
        self.file_manager = file_manager
        self.current_directory = None
        self.current_sort = "file_path"
        self.current_sort_order = "ASC"
        self.worker_thread = None

        self.setWindowTitle("Photo Archive")
        self.setMinimumSize(1200, 800)
        self.setStyleSheet(MAIN_STYLESHEET)

        # Main layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Top toolbar
        toolbar_widget = QFrame()
        toolbar_widget.setStyleSheet(TOOLBAR_STYLESHEET)
        toolbar_layout = QHBoxLayout(toolbar_widget)
        toolbar_layout.setContentsMargins(16, 8, 16, 8)

        # Open folder button with icon - use standard QStyle icon
        self.open_btn = QPushButton("Open Folder")
        self.open_btn.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_DirIcon))
        self.open_btn.clicked.connect(self.open_folder)
        toolbar_layout.addWidget(self.open_btn)

        # Add spacing
        toolbar_layout.addSpacing(20)

        # Sort options
        self.sort_label = QLabel("Sort by:")
        self.sort_label.setFont(QFont("Segoe UI", 9))
        toolbar_layout.addWidget(self.sort_label)

        self.sort_combo = QComboBox()
        self.sort_combo.addItems(["File Name", "Date", "Size"])
        self.sort_combo.currentIndexChanged.connect(self.change_sort)
        toolbar_layout.addWidget(self.sort_combo)

        # Order options
        self.order_combo = QComboBox()
        self.order_combo.addItems(["Ascending", "Descending"])
        self.order_combo.currentIndexChanged.connect(self.change_sort_order)
        toolbar_layout.addWidget(self.order_combo)

        # Add spacing
        toolbar_layout.addSpacing(20)

        # View mode (Grid/Single)
        self.view_mode_label = QLabel("View:")
        self.view_mode_label.setFont(QFont("Segoe UI", 9))
        toolbar_layout.addWidget(self.view_mode_label)

        self.view_mode_combo = QComboBox()
        self.view_mode_combo.addItems(["Grid View", "Single View"])
        self.view_mode_combo.currentIndexChanged.connect(self.change_view_mode)
        toolbar_layout.addWidget(self.view_mode_combo)

        # Spacer
        toolbar_layout.addStretch()

        # Current folder display
        self.folder_label = QLabel("No folder selected")
        self.folder_label.setFont(QFont("Segoe UI", 9))
        self.folder_label.setStyleSheet(f"color: {COLORS['text_light']};")
        toolbar_layout.addWidget(self.folder_label)

        main_layout.addWidget(toolbar_widget)

        # Content area (stacked layout)
        # Photo grid view (default)
        self.photo_grid = PhotoGrid(self.db_manager)
        # Connect to selection signal (single click) - just updates selection
        self.photo_grid.photo_clicked.connect(self.on_photo_selected)
        # Connect to open signal (double click) - opens the photo viewer
        self.photo_grid.photo_double_clicked.connect(self.open_single_view)

        # Single photo/video view
        self.photo_viewer = PhotoViewer(self.photo_grid)
        self.photo_viewer.closed.connect(self.close_single_view)
        self.photo_viewer.next_requested.connect(self.next_media)
        self.photo_viewer.prev_requested.connect(self.prev_media)

        # Add both views to main layout
        main_layout.addWidget(self.photo_grid)
        main_layout.addWidget(self.photo_viewer)

        # Default to grid view
        self.photo_viewer.hide()

        # Status bar
        self.statusBar().showMessage("Ready")

        # Create loading overlay
        self.loading_overlay = LoadingOverlay(central_widget)
        self.loading_overlay.hide()

    def open_folder(self):
        """Open a folder dialog and scan for images and videos in a background thread"""
        folder = QFileDialog.getExistingDirectory(self, "Select Directory")
        if folder:
            self.current_directory = folder
            self.folder_label.setText(f"Folder: {folder}")

            # Disable UI components during loading
            self.open_btn.setEnabled(False)
            self.sort_combo.setEnabled(False)
            self.order_combo.setEnabled(False)

            # Show loading overlay
            self.loading_overlay.reset()
            self.loading_overlay.set_message(f"Loading media files from {folder}")
            self.loading_overlay.show()

            # Create worker and thread
            self.worker = ImageProcessorWorker(self.file_manager, self.db_manager, folder)
            self.worker_thread = QThread()
            self.worker.moveToThread(self.worker_thread)

            # Connect signals
            self.worker_thread.started.connect(self.worker.process_images)
            self.worker.progress.connect(self.update_loading_progress)
            self.worker.finished.connect(self.on_processing_finished)
            self.worker.error.connect(self.on_processing_error)
            self.worker.finished.connect(self.worker_thread.quit)
            self.worker.finished.connect(self.worker.deleteLater)
            self.worker_thread.finished.connect(self.worker_thread.deleteLater)

            # Start processing
            self.worker_thread.start()

    def update_loading_progress(self, current, total):
        """Update the loading overlay progress"""
        self.loading_overlay.set_progress(current, total)
        self.statusBar().showMessage(f"Processing media file {current} of {total}")

    def on_processing_finished(self, processed_media):
        """Handle completion of media processing"""
        # Hide loading overlay
        self.loading_overlay.hide()

        # Re-enable UI components
        self.open_btn.setEnabled(True)
        self.sort_combo.setEnabled(True)
        self.order_combo.setEnabled(True)

        # Update status
        num_media = len(processed_media)
        num_images = sum(1 for m in processed_media if m.get('file_type') == 'image')
        num_videos = sum(1 for m in processed_media if m.get('file_type') == 'video')

        status_parts = []
        if num_images > 0:
            status_parts.append(f"{num_images} image{'s' if num_images != 1 else ''}")
        if num_videos > 0:
            status_parts.append(f"{num_videos} video{'s' if num_videos != 1 else ''}")

        status_text = f"Loaded {' and '.join(status_parts)}" if status_parts else f"Loaded {num_media} files"
        self.statusBar().showMessage(status_text)

        # Refresh the grid view
        self.refresh_photos()

    def on_processing_error(self, error_message):
        """Handle processing error"""
        self.loading_overlay.hide()
        self.open_btn.setEnabled(True)
        self.sort_combo.setEnabled(True)
        self.order_combo.setEnabled(True)

        QMessageBox.critical(self, "Error", f"Error processing images: {error_message}")
        self.statusBar().showMessage("Error loading images")

    def on_photo_selected(self, photo_data):
        """Handle media selection (single click) - just updates UI state"""
        # Update status bar with media info
        file_name = photo_data['file_path'].split('/')[-1].split('\\')[-1]
        size_mb = photo_data.get('file_size', 0) / (1024 * 1024)
        file_type = photo_data.get('file_type', 'image').title()

        status_parts = [f"Selected: {file_name}", f"{file_type}", f"{size_mb:.1f} MB"]

        # Add duration for videos
        if photo_data.get('duration'):
            duration = photo_data['duration']
            minutes = int(duration // 60)
            seconds = int(duration % 60)
            status_parts.append(f"{minutes:02d}:{seconds:02d}")

        self.statusBar().showMessage(" • ".join(status_parts))

    def refresh_photos(self):
        """Refresh the photo grid with current sort settings"""
        sort_mapping = {
            0: "file_path",     # File Name
            1: "date_taken",    # Date
            2: "file_size"      # Size
        }
        sort_by = sort_mapping.get(self.sort_combo.currentIndex(), "file_path")
        sort_order = "DESC" if self.order_combo.currentIndex() == 1 else "ASC"

        media_files = self.db_manager.get_all_photos(sort_by=sort_by, sort_order=sort_order)
        self.photo_grid.load_photos(media_files)

        # Update status with file counts
        num_images = sum(1 for m in media_files if m.get('file_type') == 'image')
        num_videos = sum(1 for m in media_files if m.get('file_type') == 'video')

        status_parts = []
        if num_images > 0:
            status_parts.append(f"{num_images} image{'s' if num_images != 1 else ''}")
        if num_videos > 0:
            status_parts.append(f"{num_videos} video{'s' if num_videos != 1 else ''}")

        status_text = f"Displaying {' and '.join(status_parts)}" if status_parts else f"Displaying {len(media_files)} files"
        self.statusBar().showMessage(status_text)

    def change_sort(self, index):
        """Change the sort column"""
        self.refresh_photos()

    def change_sort_order(self, index):
        """Change the sort order"""
        self.refresh_photos()

    def change_view_mode(self, index):
        """Switch between grid and single view"""
        if index == 0:  # Grid View
            self.close_single_view()
        else:  # Single View
            # If we have photos, show the first one
            first_photo = self.photo_grid.get_current_photo()
            if first_photo:
                self.open_single_view(first_photo)

    def open_single_view(self, media_data):
        """Open the single media view with the selected photo or video"""
        self.photo_grid.hide()
        self.photo_viewer.show_media(media_data)
        self.photo_viewer.show()
        self.photo_viewer.setFocus()  # Set focus to enable keyboard shortcuts
        self.view_mode_combo.setCurrentIndex(1)  # Update the view mode combo

    def close_single_view(self):
        """Close the single media view and return to grid"""
        self.photo_viewer.hide()
        self.photo_grid.show()
        self.view_mode_combo.setCurrentIndex(0)  # Update the view mode combo

    def next_media(self):
        """Show the next media file in single view"""
        # This is handled by the photo viewer itself
        pass

    def prev_media(self):
        """Show the previous media file in single view"""
        # This is handled by the photo viewer itself
        pass
