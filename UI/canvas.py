from PySide6.QtWidgets import QWidget

class Canvas(QWidget):
    def __init__(self, window):
        super().__init__()
        self.window = window