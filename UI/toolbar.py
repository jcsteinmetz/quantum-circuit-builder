from PySide6.QtWidgets import QToolBar

class ToolBar(QToolBar):
    def __init__(self, window):
        super().__init__()
        self.window = window