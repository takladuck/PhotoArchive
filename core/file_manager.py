import os
import hashlib
from datetime import datetime
from PIL import Image, ExifTags
from PIL.ExifTags import TAGS
import io
import shutil
import subprocess
import json

class FileManager:
    def __init__(self, thumbnail_dir='data/thumbnails'):
        self.thumbnail_dir = thumbnail_dir
        self._ensure_dirs()

    def _ensure_dirs(self):
        """Ensure the thumbnail directory exists"""
        os.makedirs(self.thumbnail_dir, exist_ok=True)

    def scan_directory(self, directory_path):
        """Scan a directory for image and video files"""
        supported_formats = [
            # Image formats
            '.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.webp',
            # Video formats
            '.mp4', '.avi', '.mov', '.mkv', '.wmv', '.flv', '.webm', '.m4v', '.3gp'
        ]
        media_files = []

        if not os.path.exists(directory_path):
            print(f"Directory not found: {directory_path}")
            return []

        for root, _, files in os.walk(directory_path):
            for file in files:
                if any(file.lower().endswith(ext) for ext in supported_formats):
                    file_path = os.path.join(root, file)
                    media_files.append(file_path)

        return media_files

    def get_file_metadata(self, file_path):
        """Extract metadata from an image or video file"""
        if not os.path.exists(file_path):
            return None

        metadata = {
            'file_path': file_path,
            'file_size': os.path.getsize(file_path),
            'last_modified': datetime.fromtimestamp(os.path.getmtime(file_path)).isoformat(),
            'hash': None,
            'date_taken': None,
            'location': None,
            'thumbnail_path': None,
            'file_type': self._get_file_type(file_path),
            'duration': None,  # For videos
            'resolution': None
        }

        # Determine if it's an image or video
        if metadata['file_type'] == 'video':
            metadata = self._extract_video_metadata(file_path, metadata)
        else:
            metadata = self._extract_image_metadata(file_path, metadata)

        # Calculate file hash
        metadata['hash'] = self._calculate_file_hash(file_path)

        return metadata

    def _get_file_type(self, file_path):
        """Determine if file is image or video"""
        video_extensions = ['.mp4', '.avi', '.mov', '.mkv', '.wmv', '.flv', '.webm', '.m4v', '.3gp']
        if any(file_path.lower().endswith(ext) for ext in video_extensions):
            return 'video'
        return 'image'

    def _extract_image_metadata(self, file_path, metadata):
        """Extract metadata from image files"""
        try:
            with Image.open(file_path) as img:
                # Create thumbnail
                metadata['thumbnail_path'] = self._create_image_thumbnail(file_path, img)
                metadata['resolution'] = f"{img.width}x{img.height}"

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
                            dt = datetime.strptime(date_str, '%Y:%m:%d %H:%M:%S')
                            metadata['date_taken'] = dt.isoformat()
                        except ValueError:
                            pass

                    # Get GPS info
                    if 'GPSInfo' in exif:
                        metadata['location'] = str(exif['GPSInfo'])
        except Exception as e:
            print(f"Error processing image {file_path}: {e}")

        return metadata

    def _extract_video_metadata(self, file_path, metadata):
        """Extract metadata from video files using ffprobe"""
        try:
            # Create thumbnail for video
            metadata['thumbnail_path'] = self._create_video_thumbnail(file_path)

            # Use ffprobe to get video metadata
            cmd = [
                'ffprobe', '-v', 'quiet', '-print_format', 'json',
                '-show_format', '-show_streams', file_path
            ]

            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            if result.returncode == 0:
                video_info = json.loads(result.stdout)

                # Extract duration
                if 'format' in video_info and 'duration' in video_info['format']:
                    duration = float(video_info['format']['duration'])
                    metadata['duration'] = duration

                # Extract resolution from video stream
                for stream in video_info.get('streams', []):
                    if stream.get('codec_type') == 'video':
                        width = stream.get('width')
                        height = stream.get('height')
                        if width and height:
                            metadata['resolution'] = f"{width}x{height}"
                        break

                # Try to get creation time
                if 'format' in video_info and 'tags' in video_info['format']:
                    tags = video_info['format']['tags']
                    creation_time = tags.get('creation_time') or tags.get('date')
                    if creation_time:
                        try:
                            dt = datetime.fromisoformat(creation_time.replace('Z', '+00:00'))
                            metadata['date_taken'] = dt.isoformat()
                        except:
                            pass

        except subprocess.TimeoutExpired:
            pass  # Silently handle timeout
        except FileNotFoundError:
            pass  # Silently handle missing ffprobe
        except Exception as e:
            pass  # Silently handle other video processing errors

        return metadata

    def _create_image_thumbnail(self, file_path, img=None, size=(300, 300)):
        """Create a high-quality thumbnail for image files"""
        try:
            if img is None:
                img = Image.open(file_path)

            file_name = os.path.basename(file_path)
            thumb_path = os.path.join(self.thumbnail_dir, f"thumb_{file_name}")

            thumb_img = img.copy()
            thumb_img.thumbnail(size, Image.LANCZOS)

            if file_path.lower().endswith(('.jpg', '.jpeg')):
                thumb_img.save(thumb_path, quality=95)
            else:
                thumb_img.save(thumb_path)

            return thumb_path
        except Exception as e:
            print(f"Error creating image thumbnail for {file_path}: {e}")
            return None

    def _create_video_thumbnail(self, file_path, size=(300, 300)):
        """Create a thumbnail for video files using ffmpeg"""
        try:
            file_name = os.path.basename(file_path)
            # Change extension to jpg for video thumbnails
            name_without_ext = os.path.splitext(file_name)[0]
            thumb_path = os.path.join(self.thumbnail_dir, f"thumb_{name_without_ext}.jpg")

            # Use ffmpeg to extract a frame at 1 second with suppressed output
            cmd = [
                'ffmpeg', '-v', 'error',  # Only show errors
                '-i', file_path,
                '-ss', '00:00:01',
                '-vframes', '1',
                '-vf', f'scale={size[0]}:{size[1]}:force_original_aspect_ratio=decrease',
                '-y', thumb_path
            ]

            # Suppress both stdout and stderr
            result = subprocess.run(cmd, capture_output=True, timeout=30)
            if result.returncode == 0 and os.path.exists(thumb_path):
                return thumb_path
            else:
                # Only print error if something goes wrong and we're debugging
                return None

        except subprocess.TimeoutExpired:
            pass  # Silently handle timeout
        except FileNotFoundError:
            pass  # Silently handle missing ffmpeg
        except Exception as e:
            pass  # Silently handle other errors

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
