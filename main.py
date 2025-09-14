import sys
import os
from PySide6.QtWidgets import QApplication

from core.db_manager import DBManager
from core.file_manager import FileManager
from ui.main_window import MainWindow


def main():
    # Create application
    app = QApplication(sys.argv)

    # Set working directory to script location
    app_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(app_dir)

    # Initialize managers
    db_manager = DBManager()
    file_manager = FileManager()

    # Create and show main window
    window = MainWindow(db_manager, file_manager)
    window.show()

    # Run application
    sys.exit(app.exec())


if __name__ == '__main__':
    main()
