from PySide6.QtWidgets import QWidget
from PySide6.QtCore import QPointF
from PySide6.QtGui import QPainter
from event_handler import EventHandler
from components import Grab
from grid import Grid

class Canvas(QWidget):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.grid = Grid(self)
        self.active_tool = Grab(self)
        self.dragging_enabled = False
        self.setMouseTracking(True)
        self.event_handler = EventHandler(self)

        self.placed_components = []

    def paintEvent(self, event):
        painter = QPainter(self)

        # Draw the grid
        self.grid.draw(painter)

        # Draw placed components
        for comp in self.placed_components:
            comp.draw(painter)

        # Draw active tool preview
        if self.active_tool and self.active_tool.show_preview:
            self.active_tool.draw(painter)
    
    def drag(self, delta):
        self.grid.offset -= delta  # Move the grid by the delta

        for comp in self.placed_components:
            comp.move(delta)

        self.update()  # Redraw the grid with the new offset

    def zoom(self, mouse_pos, new_grid_size):
        # Ensure the zoom factor is within reasonable bounds
        if 0.1 <= new_grid_size / self.grid.size <= 5.0:
            self.grid.zoom(mouse_pos, new_grid_size)
            for comp in self.placed_components:
                comp.zoom(mouse_pos, new_grid_size)

            # Set the new zoom factor
            self.grid.size = new_grid_size

            # Trigger a redraw
            self.update()
