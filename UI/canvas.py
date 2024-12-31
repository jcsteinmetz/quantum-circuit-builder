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

        # Placed components
        self.placed_components = {"wires": [], "components": [], "detectors": []}

        # Style
        self.bg_color = None
        self.gridline_color = None
        self.set_style()

        self.active_tool = Select(window)

    def paintEvent(self, event):
        painter = QPainter(self)

        # Draw the grid
        self.grid.draw(painter)

        # Draw placed components
        for comp_list in self.placed_components.values():
            for comp in comp_list:
                comp.draw(painter)

        # Draw tool preview
        if self.preview_enabled:
            if not isinstance(self.active_tool, Select) and not isinstance(self.active_tool, Grab):
                self.active_tool.preview(painter)

    def drag(self, delta):
        """
        Drag the canvas, including the grid and all components, by an amount delta
        """
        # Move the grid
        self.grid.offset = (self.grid.offset[0] - delta[0], self.grid.offset[1] - delta[1])

    def zoom(self, zoom_delta):
        zoom_step = 0.1
        new_grid_size = self.grid.size * (1 + zoom_step * zoom_delta)

        if 5 <= new_grid_size <= 250: # make sure the canvas is a reasonable size
            # zoom the grid
            self.grid.zoom(self.event_handler.mouse_position, new_grid_size)

            self.grid.size = new_grid_size

    def sort_components(self):
        self.placed_components["wires"] = sorted(self.placed_components["wires"], key = lambda comp: (comp.position[1], comp.position[0]))
        self.placed_components["components"] = sorted(self.placed_components["components"], key = lambda comp: (comp.position[0], comp.position[1]))
        self.placed_components["detectors"] = sorted(self.placed_components["detectors"], key = lambda comp: (comp.position[1], comp.position[0]))

    def set_style(self):
        self.bg_color = (255, 255, 255)
        self.gridline_color = (0, 0, 0)

    def enablePreview(self):
        self.preview_enabled = True

    def disablePreview(self):
        self.preview_enabled = False