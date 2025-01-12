import sys
from PySide6.QtWidgets import QApplication, QDialog
from UI.startup_dialog import StartupDialog
import qdarktheme
from UI.window import MainWindow

if __name__ == "__main__":
    app = QApplication(sys.argv)
    qdarktheme.setup_theme()
    dialog = StartupDialog()
    if dialog.exec() == QDialog.Accepted:
        simulation_type, file_path = dialog.get_selected_data()
        window = MainWindow(simulation_type, file_path)
        window.show()
        app.exec()
