from PySide6.QtCore import Qt, QRect, QSize, QPoint
from PySide6.QtGui import QMouseEvent, QWheelEvent
from PySide6.QtWidgets import QRubberBand
from abc import ABC, abstractmethod

class CanvasTool(ABC):
    def __init__(self, window):
        self.window = window
        self.placeable = False
        self.cursor_type = Qt.ArrowCursor

    def update_canvas(self):
        self.window.canvas.update()

class Select(CanvasTool):
    def __init__(self, window):
        super().__init__(window)
        self.rubber_band = QRubberBand(QRubberBand.Rectangle, self.window.canvas)
        self.rubber_band_origin = None

    def on_mouse_press(self, event: QMouseEvent):
        """
        Action to perform when a mouse press occurs on the canvas.
        """
        if event.button() == Qt.LeftButton:
            # Begin drawing the rectangular area selection
            self.rubber_band_origin = event.pos()
            self.rubber_band.setGeometry(QRect(self.rubber_band_origin, QSize()))
            self.rubber_band.show()

    def on_mouse_move(self, event: QMouseEvent):
        """
        Action to perform when the mouse is moved on the canvas.
        """
        if self.rubber_band_origin:
            # Expand the rectangular area selection
            rect = QRect(self.rubber_band_origin, event.pos()).normalized()
            self.rubber_band.setGeometry(rect)

    def on_mouse_release(self, event: QMouseEvent):
        """
        Action to perform when the mouse button is released on the canvas.
        """
        if event.button() == Qt.LeftButton:
            # Hide the rectangular area selection
            self.rubber_band.hide()
            selected_rect = self.rubber_band.geometry()
            for comp_list in self.window.canvas.placed_components.values():
                for comp in comp_list:
                    # Select all components inside the rectangle
                    is_selected = selected_rect.contains(QPoint(*comp.position))
                    if hasattr(comp, "end_position"):
                        is_selected = is_selected and selected_rect.contains(QPoint(*comp.end_position))
                    comp.set_selected(is_selected)
                
                    # If the user clicked on a component without moving the mouse, then select that component
                    if self.window.canvas.current_mouse_position == self.window.canvas.mouse_pressed_position:
                        is_selected = comp.contains(event.position().toTuple())
                        if is_selected:
                            comp.property_manager.draw(comp.position)
                        comp.set_selected(is_selected)

class Grab(CanvasTool):
    def __init__(self, window):
        super().__init__(window)
        self.dragging_enabled = False
        self.cursor_type = Qt.OpenHandCursor

    def on_mouse_press(self, event: QMouseEvent):
        """
        Action to perform when a mouse press occurs on the canvas.
        """
        if event.button() == Qt.LeftButton:
            self.dragging_enabled = True
            self.cursor_type = Qt.ClosedHandCursor
            # self.window.canvas.setCursor(self.cursor_type)

    def on_mouse_move(self, event: QMouseEvent):
        """
        Action to perform when the mouse is moved on the canvas.
        """
        if self.dragging_enabled:
            delta_x = event.position().toTuple()[0] - self.window.canvas.current_mouse_position[0]
            delta_y = event.position().toTuple()[1] - self.window.canvas.current_mouse_position[1]
            delta = (delta_x, delta_y)
            self.window.canvas.drag(delta)

    def on_mouse_release(self, event: QMouseEvent):
        """
        Action to perform when the mouse button is released on the canvas.
        """
        if event.button() == Qt.LeftButton:
            self.dragging_enabled = False
            self.cursor_type = Qt.OpenHandCursor
            # self.window.canvas.setCursor(self.cursor_type)