import sys
from PySide6.QtWidgets import QApplication
import qdarktheme
from UI.window import MainWindow

if __name__ == "__main__":
    app = QApplication(sys.argv)
    qdarktheme.setup_theme()
    window = MainWindow()
    window.show()
    app.exec()
