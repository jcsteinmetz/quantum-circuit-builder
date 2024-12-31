from PySide6.QtWidgets import QTabWidget

class ControlPanel(QTabWidget):
    def __init__(self, window):
        super().__init__()
        self.window = window