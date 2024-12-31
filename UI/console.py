from PySide6.QtWidgets import QTextEdit

class Console(QTextEdit):
    def __init__(self, window):
        super().__init__()
        self.window = window