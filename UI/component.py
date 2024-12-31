from PySide6.QtCore import Qt

class Select:
    def __init__(self, window):
        self.window = window
        self.placeable = False

    def set_cursor(self):
        self.window.canvas.setCursor(Qt.ArrowCursor)

class Grab:
    def __init__(self, window):
        self.window = window
        self.placeable = False
        self.cursor = Qt.OpenHandCursor

    def set_dragging_cursor(self):
        self.window.canvas.setCursor(Qt.ClosedHandCursor)

    def set_cursor(self):
        self.window.canvas.setCursor(Qt.OpenHandCursor)