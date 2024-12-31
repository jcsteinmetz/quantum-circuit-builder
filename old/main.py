import sys
from PySide6.QtWidgets import QApplication
from window import MainWindow
import qdarktheme

if __name__ == "__main__":
    app = QApplication(sys.argv)
    qdarktheme.setup_theme()
    window = MainWindow()
    window.show()
    app.exec()