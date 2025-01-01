from PySide6.QtWidgets import QWidget
from PySide6.QtGui import QPainter, QWheelEvent, QMouseEvent
from PySide6.QtCore import QEvent, Qt
from grid import Grid
from canvas_tools import Select, Grab
import numpy as np

class Canvas(QWidget):
    def __init__(self, window):
        super().__init__()
        self.window = window
        self.style_choice = "darkmode"
        self.grid = Grid(self)
        self.setMouseTracking(True)
        self.current_mouse_position = None
        self.mouse_pressed_position = None
        self.preview_enabled = False
        self.gram_matrix = np.ones((0, 0))

        # Placed components
        self.placed_components = {"wires": [], "components": [], "detectors": []}

        # Style
        self.bg_color = None
        self.gridline_color = None
        self.set_style()

        self.active_tool = None

    def eventFilter(self, obj, event):
        """
        Calls the corresponding action when a mouse event occurs on the canvas.
        """
        if obj == self:
            handlers = {
                QEvent.MouseButtonPress: self.on_mouse_press,
                QEvent.MouseMove: self.on_mouse_move,
                QEvent.MouseButtonRelease: self.on_mouse_release,
                QEvent.Enter: self.on_mouse_enter,
                QEvent.Leave: self.on_mouse_leave,
                QEvent.Wheel: self.on_mouse_wheel
            }
            handler = handlers.get(event.type())
            if handler:
                handler(event)
        return super().eventFilter(obj, event)
    
    def initialize_active_tool(self):
        self.active_tool = Select(self.window)
        self.installEventFilter(self)

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
            self.grid.zoom(self.current_mouse_position, new_grid_size)

            # zoom placed components
            for comp_list in self.placed_components.values():
                for comp in comp_list:
                    comp.zoom(self.current_mouse_position, new_grid_size)

            # zoom the active component preview
            if not isinstance(self.active_tool, Select) and not isinstance(self.active_tool, Grab):
                self.active_tool.zoom(self.current_mouse_position, new_grid_size)

            self.grid.size = new_grid_size

    def enablePreview(self):
        self.preview_enabled = True

    def disablePreview(self):
        self.preview_enabled = False

    def on_mouse_press(self, event: QMouseEvent):
        """
        Action to perform when a mouse press occurs on the canvas.
        """
        self.active_tool.on_mouse_press(event)
        if event.button() == Qt.LeftButton:
            # Remember where the mouse press occured
            self.mouse_pressed_position = event.position().toTuple()

            if self.active_tool.placeable:
                self.active_tool.place()

            self.update()

    def on_mouse_move(self, event: QMouseEvent):
        """
        Action to perform when the mouse is moved on the canvas.
        """
        self.active_tool.on_mouse_move(event)
        # Update the mouse position
        self.current_mouse_position = event.position().toTuple()
        self.update()

    def on_mouse_release(self, event: QMouseEvent):
        """
        Action to perform when the mouse button is released on the canvas.
        """
        self.active_tool.on_mouse_release(event)
        if event.button() == Qt.LeftButton:
            # Forget where the mouse press occured
            self.mouse_pressed_position = None
            self.update()

    def on_mouse_enter(self, event):
        """
        Action to perform when the mouse enters the canvas.
        """
        # Begin tracking the mouse position
        self.current_mouse_position = event.position().toTuple()

        # Set the cursor depending on which tool is selected
        self.setCursor(self.active_tool.cursor_type)

        if not (isinstance(self.active_tool, Select) or isinstance(self.active_tool, Grab)):
            self.enablePreview()

        self.update()
    
    def on_mouse_leave(self, event):
        """
        Action to perform when the mouse leaves the canvas.
        """
        # Stop tracking the mouse position
        self.current_mouse_position = None

        # Reset the cursor
        self.setCursor(Qt.ArrowCursor)

        if not(isinstance(self.active_tool, Select) or isinstance(self.active_tool, Grab)):
            self.disablePreview()

        self.update()

    def on_mouse_wheel(self, event: QWheelEvent):
        """
        Action to perform when the mouse wheel scrolls on the canvas.
        """
        # Zoom the canvas
        zoom_delta = event.angleDelta().y() / 120
        self.zoom(zoom_delta)
        self.update()