from PySide6.QtWidgets import QWidget
from PySide6.QtGui import QPainter
from event_handler import EventHandler
from components import NormalCursor
from grid import Grid
from style import StyleOptions

class Canvas(QWidget):
    def __init__(self, style_choice, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.grid = Grid(self)
        self.style = StyleOptions(style_choice)
        self.active_tool = NormalCursor(self)
        self.dragging_enabled = False
        self.setMouseTracking(True)
        self.event_handler = EventHandler(self)
        self.placed_components = []
        self.occupied_by_wires = []
        self.occupied_by_components = []

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
        if 5 <= new_grid_size <= 250:

            self.grid.zoom(mouse_pos, new_grid_size)

            for comp in self.placed_components:
                comp.zoom(mouse_pos, new_grid_size)
            if self.active_tool:
                self.active_tool.zoom(mouse_pos, new_grid_size)

            # Set the new zoom factor
            self.grid.size = new_grid_size

            # Trigger a redraw
            self.update()
