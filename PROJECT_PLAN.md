# 📸 Photo Archive – Project Plan

## 🔹 Overview

Photo Archive is a Windows-friendly photo management application written in **Python (PySide6 + SQLite)**.
The goal is to provide a modern photo viewer with powerful management features while keeping photos in the **normal Windows file system** (no vendor lock-in).

The app builds a **database cache** of metadata, duplicates, and tags to provide fast queries and advanced features.
All file operations (copy, paste, delete, backup) work **directly on the Windows filesystem**.

---

## 🔹 Tech Stack

* **Language**: Python 3.x
* **GUI**: PySide6 (Qt for Python)
* **Database**: SQLite (for metadata, duplicates, tags, backup info)
* **Image Processing**: Pillow, OpenCV (later for duplicates/documents/faces)
* **Packaging**: PyInstaller (to build .exe for Windows)

---

## 🔹 Project Structure

```
photo-archive/
│
├── main.py                # Entry point
├── config/                # Config, settings, themes
│   └── settings.json
├── ui/                    # All UI code
│   ├── main_window.py
│   ├── viewer.py
│   ├── delete_mode.py
│   ├── calendar_view.py
│   └── ...
├── core/                  # Core logic
│   ├── file_manager.py    # File operations, metadata handling
│   ├── db_manager.py      # SQLite database handling
│   ├── duplicate_finder.py
│   ├── document_detector.py
│   ├── face_cluster.py
│   └── backup_manager.py
├── data/                  # Thumbnails, cache, logs, database file
│   └── photo_archive.db
├── assets/                # Icons, themes, static images
└── tests/                 # Unit tests
```

---

## 🔹 Database Schema (Initial + Expandable)

**Table: photos**

| Column         | Type    | Description                       |
| -------------- | ------- | --------------------------------- |
| id             | INTEGER | Primary key                       |
| file\_path     | TEXT    | Absolute path to file             |
| hash           | TEXT    | File hash (for duplicates)        |
| date\_taken    | TEXT    | From EXIF or file modified time   |
| location       | TEXT    | From EXIF GPS, fallback None      |
| is\_document   | BOOLEAN | Flag if photo is a document/scan  |
| face\_ids      | TEXT    | JSON list of detected face IDs    |
| deleted        | BOOLEAN | If moved to recycle bin           |
| backup\_status | TEXT    | not\_backed / backed\_up / failed |

**Table: faces**

| Column       | Type    | Description                              |
| ------------ | ------- | ---------------------------------------- |
| id           | INTEGER | Primary key                              |
| person\_name | TEXT    | User-assigned label for the face cluster |
| encoding     | BLOB    | Face embedding (for recognition)         |

*(More tables can be added later for tags, albums, etc.)*

---

## 🔹 Version Roadmap

### ✅ Version 0 (MVP – Basic Viewer)

* Open folder, scan images, and load into UI.
* **Grid view** and **single photo view** (with arrow keys).
* Sorting by **name, date, size**.
* Database setup (`photos` table) and initial metadata caching.

### 🔜 Version 1 (Easy Delete Mode)

* Toggle delete mode.
* Spacebar to mark/unmark images.
* Arrow keys for navigation.
* “Recycle Bin” = app-managed folder (e.g., `data/trash/`).

### 🔜 Version 2 (Cleanup Tools)

* Duplicate finder (using perceptual hash).
* Document detector (using OpenCV).
* Easy Delete Mode launches with pre-filtered results.

### 🔜 Version 3 (Smart Grouping & Views)

* Group photos by **location, people, trips**.
* Calendar view (photos by date).
* Face clustering and user tagging.

### 🔜 Version 4 (Backups & Advanced)

* Backup manager: incremental backups to external folder/cloud.
* Search bar (search by date, tag, person, location).
* Optional auto-tagging with AI models (CLIP, image classifiers).

---

## 🔹 Guiding Principles

* **Non-intrusive**: Files remain in normal Windows folders. Users can still open them in Explorer without issues.
* **Fast**: Database caches metadata and duplicates → no repeated slow scans.
* **Expandable**: Features are modular (delete mode, cleanup, grouping, backup).
* **User-friendly**: Keyboard shortcuts for power use (arrows, space, delete).
