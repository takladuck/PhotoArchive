import os
import hashlib
from datetime import datetime
from PIL import Image, ExifTags
from PIL.ExifTags import TAGS
import io
import shutil

class FileManager:
    def __init__(self, thumbnail_dir='data/thumbnails'):
        self.thumbnail_dir = thumbnail_dir
        self._ensure_dirs()

    def _ensure_dirs(self):
        """Ensure the thumbnail directory exists"""
        os.makedirs(self.thumbnail_dir, exist_ok=True)

    def scan_directory(self, directory_path):
        """Scan a directory for image files"""
        supported_formats = ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff']
        image_files = []

        if not os.path.exists(directory_path):
            print(f"Directory not found: {directory_path}")
            return []

        for root, _, files in os.walk(directory_path):
            for file in files:
                if any(file.lower().endswith(ext) for ext in supported_formats):
                    file_path = os.path.join(root, file)
                    image_files.append(file_path)

        return image_files

    def get_file_metadata(self, file_path):
        """Extract metadata from an image file"""
        if not os.path.exists(file_path):
            return None

        metadata = {
            'file_path': file_path,
            'file_size': os.path.getsize(file_path),
            'last_modified': datetime.fromtimestamp(os.path.getmtime(file_path)).isoformat(),
            'hash': None,
            'date_taken': None,
            'location': None,
            'thumbnail_path': None
        }

        # Extract EXIF data
        try:
            with Image.open(file_path) as img:
                # Create thumbnail
                metadata['thumbnail_path'] = self._create_thumbnail(file_path, img)

                # Extract EXIF
                if hasattr(img, '_getexif') and img._getexif():
                    exif = {
                        TAGS.get(k, k): v
                        for k, v in img._getexif().items()
                        if k in TAGS
                    }

                    # Get date taken
                    if 'DateTimeOriginal' in exif:
                        date_str = exif['DateTimeOriginal']
                        try:
                            # Format: 'YYYY:MM:DD HH:MM:SS'
                            dt = datetime.strptime(date_str, '%Y:%m:%d %H:%M:%S')
                            metadata['date_taken'] = dt.isoformat()
                        except ValueError:
                            pass

                    # Get GPS info (simplified)
                    if 'GPSInfo' in exif:
                        metadata['location'] = str(exif['GPSInfo'])
        except Exception as e:
            print(f"Error processing image {file_path}: {e}")

        # Calculate file hash
        metadata['hash'] = self._calculate_file_hash(file_path)

        return metadata

    def _create_thumbnail(self, file_path, img=None, size=(300, 300)):
        """Create a high-quality thumbnail for the image

        Args:
            file_path: Path to the original image
            img: Optional PIL Image object (to avoid reopening the file)
            size: Thumbnail size (width, height)

        Returns:
            Path to the created thumbnail
        """
        try:
            if img is None:
                img = Image.open(file_path)

            # Create filename for thumbnail
            file_name = os.path.basename(file_path)
            thumb_path = os.path.join(self.thumbnail_dir, f"thumb_{file_name}")

            # Create a copy to avoid modifying the original
            thumb_img = img.copy()

            # Use high quality thumbnail generation
            thumb_img.thumbnail(size, Image.LANCZOS)

            # For JPG format, save with high quality
            if file_path.lower().endswith(('.jpg', '.jpeg')):
                thumb_img.save(thumb_path, quality=95)
            else:
                thumb_img.save(thumb_path)

            return thumb_path
        except Exception as e:
            print(f"Error creating thumbnail for {file_path}: {e}")
            return None

    def _calculate_file_hash(self, file_path, block_size=65536):
        """Calculate a hash for the file (for duplicate detection)"""
        try:
            hasher = hashlib.md5()
            with open(file_path, 'rb') as f:
                buf = f.read(block_size)
                while len(buf) > 0:
                    hasher.update(buf)
                    buf = f.read(block_size)
            return hasher.hexdigest()
        except Exception as e:
            print(f"Error calculating hash for {file_path}: {e}")
            return None
