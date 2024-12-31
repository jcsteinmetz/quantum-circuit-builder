from PySide6.QtWidgets import QWidget
from PySide6.QtGui import QPainter
from grid import Grid
from component import Select, Grab
from event_handler import EventHandler

class Canvas(QWidget):
    def __init__(self, window):
        super().__init__()
        self.window = window
        self.grid = Grid(self)
        self.event_handler = EventHandler(self)
        self.setMouseTracking(True)
        self.preview_enabled = False

        # Style
        self.bg_color = None
        self.gridline_color = None
        self.set_style()

        self.active_tool = Grab(window)

    def paintEvent(self, event):
        painter = QPainter(self)

        # Draw the grid
        self.grid.draw(painter)

    def drag(self, delta):
        """
        Drag the canvas, including the grid and all components, by an amount delta
        """
        # Move the grid
        self.grid.offset = (self.grid.offset[0] - delta[0], self.grid.offset[1] - delta[1])

    def set_style(self):
        self.bg_color = (255, 255, 255)
        self.gridline_color = (0, 0, 0)

    def enablePreview(self):
        self.preview_enabled = True

    def disablePreview(self):
        self.preview_enabled = False