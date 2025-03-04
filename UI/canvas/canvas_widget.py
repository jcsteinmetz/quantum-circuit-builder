from PySide6.QtWidgets import QWidget
from PySide6.QtGui import QPainter, QWheelEvent, QMouseEvent
from PySide6.QtCore import QEvent, Qt
from UI.canvas.grid import Grid
from UI.canvas.canvas_tools import Select, CanvasTool
from UI.component import Detector
from UI.component_renderer import ComponentRenderer
import numpy as np

class Canvas(QWidget):
    """The main working area where circuit components can be drawn."""
    def __init__(self, window):
        super().__init__()
        self.window = window
        self.grid = Grid(self)
        self.setMouseTracking(True)
        self.current_mouse_position = None
        self.mouse_pressed_position = None
        self.double_click_flag = False
        self.preview_enabled = False
        self.gram_matrix = np.ones((0, 0))

        self.component_renderer = ComponentRenderer(self.window)

        # Placed components
        self.placed_components = {"wires": [], "components": [], "detectors": []}

        # Style
        self.bg_color = self.window.style_manager.get_style("bg_color")
        self.gridline_color = self.window.style_manager.get_style("gridline_color")

        self.active_tool = None

    def update_styles(self):
        """Change the colours of the canvas background and grid depending on the current theme."""
        self.bg_color = self.window.style_manager.get_style("bg_color")
        self.gridline_color = self.window.style_manager.get_style("gridline_color")

    def paintEvent(self, event):
        """Repaints the canvas."""
        painter = QPainter(self)

        # Draw the grid
        self.grid.draw(painter)

        # Draw placed components
        for comp in self.all_placed_components():
            self.component_renderer.draw(painter, comp)

        # Draw tool preview
        if self.preview_enabled:
            self.component_renderer.preview(painter, self.active_tool)

    def all_placed_components(self):
        """Returns a list of all components, no matter their type."""
        for comp_list in self.placed_components.values():
            for comp in comp_list[:]:
                yield comp

    def eventFilter(self, obj, event):
        """Calls the corresponding action when a mouse event occurs on the canvas."""
        if obj == self:
            handlers = {
                QEvent.MouseButtonPress: self.on_mouse_press,
                QEvent.MouseMove: self.on_mouse_move,
                QEvent.MouseButtonRelease: self.on_mouse_release,
                QEvent.Enter: self.on_mouse_enter,
                QEvent.Leave: self.on_mouse_leave,
                QEvent.Wheel: self.on_mouse_wheel,
                QEvent.MouseButtonDblClick: self.on_double_click
            }
            handler = handlers.get(event.type())
            if handler:
                handler(event)
        return super().eventFilter(obj, event)
    
    def initialize_active_tool(self):
        """Start with the Select tool."""
        self.active_tool = Select(self.window)
        self.installEventFilter(self)

    @property
    def overlaps(self):
        """
        List of overlaps between photons' internal states. This is the same as a flattened version of
        the upper triangular part of the Gram matrix.
        """
        if self.n_photons in [0, 1]:
            return [1]
        upper_triangular_indices = np.triu_indices(self.n_photons, k=1)
        return list(self.gram_matrix[upper_triangular_indices])

    @property
    def n_wires(self):
        """Current number of wires on the canvas."""
        return len(self.placed_components["wires"])
    
    @property
    def n_photons(self):
        """Current number of photons entered into the simulation."""
        n_photons = 0
        for wire in self.placed_components["wires"]:
            n_photons += wire.n_photons
        return n_photons

    def sort_components(self):
        """
        Sorts all categories of components. Components are sorted into the order they will be applied
        in the simulation - basically left-to-right, top-to-bottom.
        """
        self.placed_components["wires"] = sorted(self.placed_components["wires"], key = lambda comp: (comp.node_positions[0][1], comp.node_positions[0][0]))
        self.placed_components["components"] = sorted(self.placed_components["components"], key = lambda comp: (comp.node_positions[0][0], comp.node_positions[0][1]))
        self.placed_components["detectors"] = sorted(self.placed_components["detectors"], key = lambda comp: (comp.node_positions[0][1], comp.node_positions[0][0]))

    def deselect_all(self):
        """Deselects all components on the canvas."""
        for comp in self.all_placed_components():
            comp.is_selected = False
            comp.property_box.hide()
        self.update()

    def snap_all_components(self):
        """Snaps all placed components to the grid"""
        for comp in self.all_placed_components():
            comp.snap()

    def drag(self, delta):
        """Drag the canvas, including the grid and all components, by an amount delta"""
        # Move the grid
        self.grid.offset = (self.grid.offset[0] - delta[0], self.grid.offset[1] - delta[1])

        # Move placed components
        for comp in self.all_placed_components():
            comp.move(delta)

    def recenter(self):
        """Resets the canvas offset to return to the original position."""
        self.drag(self.grid.offset)
        self.repaint()

    def zoom(self, zoom_delta):
        zoom_step = 0.1
        new_grid_size = self.grid.size * (1 + zoom_step * zoom_delta)

        if 5 <= new_grid_size <= 250: # make sure the canvas is a reasonable size
            # zoom the grid
            self.grid.zoom(self.current_mouse_position, new_grid_size)

            # zoom placed components
            for comp in self.all_placed_components():
                comp.zoom(self.current_mouse_position, new_grid_size)

            # zoom the active component preview
            if not isinstance(self.active_tool, CanvasTool):
                self.active_tool.zoom(self.current_mouse_position, new_grid_size)

            self.grid.size = new_grid_size

    def enablePreview(self):
        self.preview_enabled = True

    def disablePreview(self):
        self.preview_enabled = False

    def place(self, comp):
        """Place a component on the canvas. The component is drawn and saved in placed_components."""
        self.active_tool = comp.__class__(self.window)
        if comp.direction == "H":
            self.placed_components["wires"].append(comp)
        elif isinstance(comp, Detector):
            self.placed_components["detectors"].append(comp)
        else:
            self.placed_components["components"].append(comp)

        self.sort_components()
        self.window.console.refresh()
        self.window.control_panel.components_tab.refresh()
        self.window.update_undo_stack()
        self.window.mark_unsaved_changes()

    def on_mouse_press(self, event: QMouseEvent):
        """Action to perform when a mouse press occurs on the canvas."""
        if isinstance(self.active_tool, CanvasTool):
            self.active_tool.on_mouse_press(event)

        if event.button() == Qt.LeftButton:
            # Remember where the mouse press occured
            self.mouse_pressed_position = event.position().toTuple()

            if not isinstance(self.active_tool, CanvasTool):
                if self.active_tool.placeable:
                    self.active_tool.place()

            self.update()
            self.deselect_all()

    def on_mouse_move(self, event: QMouseEvent):
        """Action to perform when the mouse is moved on the canvas."""
        if isinstance(self.active_tool, CanvasTool):
            self.active_tool.on_mouse_move(event)
        # Update the mouse position
        self.current_mouse_position = event.position().toTuple()
        self.update()

    def on_mouse_release(self, event: QMouseEvent):
        """Action to perform when the mouse button is released on the canvas."""
        if not self.double_click_flag:
            if isinstance(self.active_tool, CanvasTool):
                self.active_tool.on_mouse_release(event)
            if event.button() == Qt.LeftButton:
                # Forget where the mouse press occured
                self.mouse_pressed_position = None
                self.update()
        else:
            self.double_click_flag = False

    def on_mouse_enter(self, event):
        """Action to perform when the mouse enters the canvas."""
        # Begin tracking the mouse position
        self.current_mouse_position = event.position().toTuple()

        # Set the cursor depending on which tool is selected
        self.setCursor(self.active_tool.cursor_type)

        if not isinstance(self.active_tool, CanvasTool):
            self.enablePreview()

        self.update()
    
    def on_mouse_leave(self, event):
        """Action to perform when the mouse leaves the canvas."""
        # Stop tracking the mouse position
        self.current_mouse_position = None

        # Reset the cursor
        self.setCursor(Qt.ArrowCursor)

        if not isinstance(self.active_tool, CanvasTool):
            self.disablePreview()

        self.update()

    def on_mouse_wheel(self, event: QWheelEvent):
        """Action to perform when the mouse wheel scrolls on the canvas."""
        # Zoom the canvas
        zoom_delta = event.angleDelta().y() / 120
        self.zoom(zoom_delta)
        self.update()

    def on_double_click(self, event: QMouseEvent):
        self.double_click_flag = True