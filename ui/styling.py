"""
Styling module for the PhotoArchive application.
Contains color schemes, stylesheets, and styling utilities.
"""

# Color scheme
COLORS = {
    'primary': '#3498db',       # Blue
    'primary_dark': '#2980b9',  # Darker blue
    'primary_hover': '#2980b9', # Hover state for primary buttons
    'accent': '#e74c3c',        # Red accent
    'background': '#121212',    # Very dark background
    'surface': '#1e1e1e',       # Surface/card background (same as card)
    'card': '#1e1e1e',          # Dark grey card background
    'text': '#ffffff',          # White text
    'text_light': '#aaaaaa',    # Light grey text
    'text_secondary': '#aaaaaa', # Secondary text color
    'border': '#333333',        # Dark border
    'success': '#2ecc71',       # Green for success
    'warning': '#f39c12',       # Orange for warnings
    'error': '#e74c3c',         # Red for errors
    'highlight': '#1e88e5',     # Highlight blue
}

# Main application stylesheet
MAIN_STYLESHEET = f"""
QMainWindow, QDialog, QWidget#centralwidget {{
    background-color: {COLORS['background']};
}}

QLabel {{
    color: {COLORS['text']};
}}

QPushButton {{
    background-color: {COLORS['primary']};
    color: white;
    border: none;
    padding: 8px 16px;
    border-radius: 4px;
}}

QPushButton:hover {{
    background-color: {COLORS['primary_hover']};
}}

QPushButton:pressed {{
    background-color: {COLORS['primary_dark']};
    padding: 9px 15px 7px 17px;
}}

QPushButton:disabled {{
    background-color: #596778;
}}

QComboBox {{
    border: 1px solid {COLORS['border']};
    border-radius: 4px;
    padding: 6px 12px;
    background-color: {COLORS['card']};
    color: {COLORS['text']};
    min-width: 120px;
}}

QComboBox::drop-down {{
    border: none;
    width: 20px;
}}

QComboBox::down-arrow {{
    width: 12px;
    height: 12px;
}}

QComboBox QAbstractItemView {{
    border: 1px solid {COLORS['border']};
    background-color: {COLORS['card']};
    selection-background-color: {COLORS['primary']};
    selection-color: white;
}}

QScrollArea {{
    border: none;
    background-color: transparent;
}}

QScrollBar:vertical {{
    border: none;
    background: rgba(255, 255, 255, 0.1);
    width: 8px;
    margin: 0px 0px 0px 0px;
}}

QScrollBar::handle:vertical {{
    background: rgba(255, 255, 255, 0.3);
    min-height: 20px;
    border-radius: 4px;
}}

QScrollBar::handle:vertical:hover {{
    background: rgba(255, 255, 255, 0.5);
}}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
    height: 0px;
}}

QScrollBar:horizontal {{
    border: none;
    background: rgba(255, 255, 255, 0.1);
    height: 8px;
    margin: 0px 0px 0px 0px;
}}

QScrollBar::handle:horizontal {{
    background: rgba(255, 255, 255, 0.3);
    min-width: 20px;
    border-radius: 4px;
}}

QScrollBar::handle:horizontal:hover {{
    background: rgba(255, 255, 255, 0.5);
}}

QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{
    width: 0px;
}}

QStatusBar {{
    background-color: {COLORS['card']};
    color: {COLORS['text_light']};
}}
"""

# PhotoThumbnail stylesheet
THUMBNAIL_STYLESHEET = f"""
background-color: {COLORS['card']};
border-radius: 8px;
border: none;
"""

# Selected thumbnail stylesheet
SELECTED_THUMBNAIL_STYLESHEET = f"""
background-color: {COLORS['card']};
border-radius: 8px;
border: 2px solid {COLORS['primary']};
"""

# Photo viewer stylesheet
PHOTO_VIEWER_STYLESHEET = f"""
background-color: #121212;
"""

# Toolbar stylesheet
TOOLBAR_STYLESHEET = f"""
background-color: {COLORS['card']};
border-bottom: 1px solid rgba(255, 255, 255, 0.1);
padding: 8px;
"""

# Info panel stylesheet
INFO_PANEL_STYLESHEET = f"""
background-color: rgba(0, 0, 0, 0.7);
color: white;
border-radius: 4px;
padding: 8px 12px;
"""
