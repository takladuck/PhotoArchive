import os
import sqlite3
from datetime import datetime
import json
import threading

class DBManager:
    _instance = None
    _lock = threading.Lock()

    def __init__(self, db_path='data/photo_archive.db'):
        self.db_path = db_path
        self._ensure_dir()
        self.local = threading.local()
        self._create_tables()

    def _ensure_dir(self):
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)

    def _connect(self):
        """Create a thread-local database connection"""
        if not hasattr(self.local, 'conn') or self.local.conn is None:
            self.local.conn = sqlite3.connect(self.db_path)
            self.local.conn.row_factory = sqlite3.Row
            self.local.cursor = self.local.conn.cursor()
        return self.local.conn, self.local.cursor

    def _create_tables(self):
        # Get thread-local connection and cursor
        conn, cursor = self._connect()

        # Create media table (renamed from photos to support both images and videos)
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS photos (
            id INTEGER PRIMARY KEY,
            file_path TEXT UNIQUE,
            hash TEXT,
            date_taken TEXT,
            location TEXT,
            is_document BOOLEAN DEFAULT 0,
            face_ids TEXT,
            deleted BOOLEAN DEFAULT 0,
            backup_status TEXT DEFAULT 'not_backed',           
            thumbnail_path TEXT,
            file_size INTEGER,
            last_modified TEXT,
            file_type TEXT DEFAULT 'image',
            duration REAL,
            resolution TEXT
        )
        ''')

        # Add new columns to existing table if they don't exist
        try:
            cursor.execute('ALTER TABLE photos ADD COLUMN file_type TEXT DEFAULT "image"')
        except sqlite3.OperationalError:
            pass  # Column already exists

        try:
            cursor.execute('ALTER TABLE photos ADD COLUMN duration REAL')
        except sqlite3.OperationalError:
            pass  # Column already exists

        try:
            cursor.execute('ALTER TABLE photos ADD COLUMN resolution TEXT')
        except sqlite3.OperationalError:
            pass  # Column already exists

        # Create faces table (for future use)
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS faces (
            id INTEGER PRIMARY KEY,
            person_name TEXT,
            encoding BLOB
        )
        ''')

        conn.commit()

    def add_photo(self, file_path, file_hash=None, date_taken=None, location=None,
                  thumbnail_path=None, file_size=None, last_modified=None,
                  file_type='image', duration=None, resolution=None):
        """Add a photo or video to the database or update if it exists"""
        try:
            # Get thread-local connection and cursor
            conn, cursor = self._connect()

            # Default values
            if date_taken is None:
                date_taken = datetime.now().isoformat()
            if last_modified is None:
                last_modified = datetime.now().isoformat()

            cursor.execute('''
            INSERT OR REPLACE INTO photos 
            (file_path, hash, date_taken, location, thumbnail_path, file_size, last_modified, file_type, duration, resolution)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (file_path, file_hash, date_taken, location, thumbnail_path, file_size, last_modified, file_type, duration, resolution))

            conn.commit()
            return True
        except Exception as e:
            print(f"Error adding media file to database: {e}")
            return False

    def get_all_photos(self, sort_by='file_path', sort_order='ASC', file_type=None):
        """Get all photos/videos from the database with optional filtering by type"""
        valid_columns = ['file_path', 'date_taken', 'file_size', 'last_modified', 'file_type']
        if sort_by not in valid_columns:
            sort_by = 'file_path'

        if sort_order not in ['ASC', 'DESC']:
            sort_order = 'ASC'

        try:
            # Get thread-local connection and cursor
            _, cursor = self._connect()

            where_clause = "WHERE deleted = 0"
            params = []

            if file_type:
                where_clause += " AND file_type = ?"
                params.append(file_type)

            cursor.execute(f'''
            SELECT * FROM photos 
            {where_clause}
            ORDER BY {sort_by} {sort_order}
            ''', params)
            return [dict(row) for row in cursor.fetchall()]
        except Exception as e:
            print(f"Error fetching media files: {e}")
            return []

    def get_photo_by_path(self, file_path):
        """Get a specific photo by path"""
        try:
            # Get thread-local connection and cursor
            _, cursor = self._connect()

            cursor.execute('''
            SELECT * FROM photos 
            WHERE file_path = ?
            ''', (file_path,))
            result = cursor.fetchone()
            return dict(result) if result else None
        except Exception as e:
            print(f"Error fetching photo by path: {e}")
            return None

    def close(self):
        """Close the database connection"""
        if hasattr(self.local, 'conn') and self.local.conn:
            self.local.conn.close()
            self.local.conn = None
