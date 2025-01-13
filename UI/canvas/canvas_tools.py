from PySide6.QtCore import Qt, QRect, QSize, QPoint
from PySide6.QtGui import QMouseEvent
from PySide6.QtWidgets import QRubberBand
from abc import ABC, abstractmethod

class CanvasTool(ABC):
    """Tools to interact with the canvas using the mouse."""
    def __init__(self, window):
        self.window = window
        self.cursor_type = Qt.ArrowCursor

    @abstractmethod
    def on_mouse_press(self, event: QMouseEvent):
        pass

    @abstractmethod
    def on_mouse_move(self, event: QMouseEvent):
        pass

    @abstractmethod
    def on_mouse_release(self, event: QMouseEvent):
        pass

class Select(CanvasTool):
    """Tool that selects a component by clicking or multiple components by clicking and dragging."""
    def __init__(self, window):
        super().__init__(window)
        self.rubber_band = QRubberBand(QRubberBand.Rectangle, self.window.canvas)
        self.rubber_band_origin = None

    def on_mouse_press(self, event: QMouseEvent):
        """Begin drawing the rectangular area selection."""
        if event.button() == Qt.LeftButton:
            self.rubber_band_origin = event.pos()
            self.rubber_band.setGeometry(QRect(self.rubber_band_origin, QSize()))
            self.rubber_band.show()

    def on_mouse_move(self, event: QMouseEvent):
        """Expand the rectangular area selection"""
        if self.rubber_band_origin:
            rect = QRect(self.rubber_band_origin, event.pos()).normalized()
            self.rubber_band.setGeometry(rect)

    def on_mouse_release(self, event: QMouseEvent):
        """Select all components inside the rectangle, or select a single component."""
        if event.button() == Qt.LeftButton:
            # Hide the rectangular area selection
            self.rubber_band.hide()
            selected_rect = self.rubber_band.geometry()
            for comp in self.window.canvas.all_placed_components():
                # Select all components inside the rectangle
                if len(comp.node_positions) > 0:
                    is_selected = selected_rect.contains(QPoint(*comp.node_positions[0]))
                if len(comp.node_positions) > 1:
                    is_selected = is_selected and selected_rect.contains(QPoint(*comp.node_positions[1]))
                comp.toggle_selection(is_selected)
            
                # If the user clicked on a component, then select that component
                if comp.contains(self.window.canvas.mouse_pressed_position) and comp.contains(self.window.canvas.current_mouse_position):
                # if self.window.canvas.current_mouse_position == self.window.canvas.mouse_pressed_position:
                    is_selected = comp.contains(event.position().toTuple())
                    comp.toggle_selection(is_selected)

class Grab(CanvasTool):
    """Tool that allows the canvas and everything on it to be dragged around."""
    def __init__(self, window):
        super().__init__(window)
        self.dragging_enabled = False
        self.cursor_type = Qt.OpenHandCursor

    def on_mouse_press(self, event: QMouseEvent):
        """Enable dragging."""
        if event.button() == Qt.LeftButton:
            self.dragging_enabled = True
            self.cursor_type = Qt.ClosedHandCursor
            self.window.canvas.setCursor(self.cursor_type)

    def on_mouse_move(self, event: QMouseEvent):
        """Drag the canvas."""
        if self.dragging_enabled:
            delta_x = event.position().toTuple()[0] - self.window.canvas.current_mouse_position[0]
            delta_y = event.position().toTuple()[1] - self.window.canvas.current_mouse_position[1]
            delta = (delta_x, delta_y)
            self.window.canvas.drag(delta)

    def on_mouse_release(self, event: QMouseEvent):
        """Disable dragging."""
        if event.button() == Qt.LeftButton:
            self.dragging_enabled = False
            self.cursor_type = Qt.OpenHandCursor
            self.window.canvas.setCursor(self.cursor_type)