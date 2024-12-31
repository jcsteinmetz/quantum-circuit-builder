from PySide6.QtWidgets import QWidget
from PySide6.QtGui import QPainter
from grid import Grid
from component import Select, Grab
from event_handler import EventHandler
import numpy as np

class Canvas(QWidget):
    def __init__(self, window):
        super().__init__()
        self.window = window
        self.style_choice = "darkmode"
        self.grid = Grid(self)
        self.event_handler = EventHandler(self)
        self.setMouseTracking(True)
        self.preview_enabled = False
        self.gram_matrix = np.ones((0, 0))

        # Placed components
        self.placed_components = {"wires": [], "components": [], "detectors": []}

        # Style
        self.bg_color = None
        self.gridline_color = None
        self.set_style()

        self.active_tool = Select(window)

    @property
    def overlaps(self):
        if self.n_photons in [0, 1]:
            return [1]
        upper_triangular_indices = np.triu_indices(self.n_photons, k=1)
        return list(self.gram_matrix[upper_triangular_indices])

    @property
    def n_wires(self):
        return len(self.placed_components["wires"])
    
    @property
    def n_photons(self):
        n_photons = 0
        for wire in self.placed_components["wires"]:
            n_photons += wire.n_photons
        return n_photons

    def sort_components(self):
        self.placed_components["wires"] = sorted(self.placed_components["wires"], key = lambda comp: (comp.position[1], comp.position[0]))
        self.placed_components["components"] = sorted(self.placed_components["components"], key = lambda comp: (comp.position[0], comp.position[1]))
        self.placed_components["detectors"] = sorted(self.placed_components["detectors"], key = lambda comp: (comp.position[1], comp.position[0]))

    def set_style(self):
        if self.style_choice == "basic":
            self.bg_color = (255, 255, 255)
            self.gridline_color = (0, 0, 0)
        elif self.style_choice == "darkmode":
            self.bg_color = (0, 0, 0)
            self.gridline_color = (50, 50, 50)

    def deselect_all(self):
        for comp_list in self.placed_components.values():
            for comp in comp_list:
                comp.is_selected = False
        self.update()

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

        # Move placed components
        for comp_list in self.placed_components.values():
            for comp in comp_list:
                comp.move(delta)

    def zoom(self, zoom_delta):
        zoom_step = 0.1
        new_grid_size = self.grid.size * (1 + zoom_step * zoom_delta)

        if 5 <= new_grid_size <= 250: # make sure the canvas is a reasonable size
            # zoom the grid
            self.grid.zoom(self.event_handler.mouse_position, new_grid_size)

            # zoom placed components
            for comp_list in self.placed_components.values():
                for comp in comp_list:
                    comp.zoom(self.event_handler.mouse_position, new_grid_size)

            # zoom the active component preview
            if not isinstance(self.active_tool, Select) and not isinstance(self.active_tool, Grab):
                self.active_tool.zoom(self.event_handler.mouse_position, new_grid_size)

            self.grid.size = new_grid_size

    def enablePreview(self):
        self.preview_enabled = True

    def disablePreview(self):
        self.preview_enabled = False