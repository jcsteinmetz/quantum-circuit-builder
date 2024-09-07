from PySide6.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QButtonGroup
from PySide6.QtCore import Qt, QPoint, QPointF, QObject, QEvent
from PySide6.QtGui import QPainter, QColor, QWheelEvent, QMouseEvent, QPen
import numpy as np
from copy import copy

class EventHandler(QObject):
    def __init__(self, canvas):
        super().__init__()
        self.canvas = canvas
        self.last_mouse_pos = None
        self.canvas.installEventFilter(self)

    def eventFilter(self, obj, event):
        if obj == self.canvas:
            handlers = {
                QEvent.MouseButtonPress: self.handle_mouse_press,
                QEvent.MouseMove: self.handle_mouse_move,
                QEvent.MouseButtonRelease: self.handle_mouse_release,
                QEvent.Wheel: self.handle_wheel,
                QEvent.Enter: self.handle_enter,
                QEvent.Leave: self.handle_leave
            }
            handler = handlers.get(event.type())
            if handler:
                handler(event)
        return super().eventFilter(obj, event)

    def handle_mouse_press(self, event: QMouseEvent):
        if event.button() == Qt.LeftButton:
            if self.canvas.status == "wire_start":
                # Place the start of the wire
                self.canvas.placed_components.append({'type': self.canvas.status, 'pos': self.canvas.floating_image_pos, 'color': QColor(0, 0, 255, 100)})
                self.canvas.wires.append({'start': copy(self.canvas.floating_image_pos), 'end': None})  # Start of the wire
                self.canvas.update()  # Redraw to show the new component

                self.canvas.status = "wire_end"
                
                # Make floating image disappear until mouse moves
                self.canvas.show_floating_image = False

            elif self.canvas.status == "wire_end":
                # Update the end of the wire
                wire_end_pos = QPointF(self.canvas.floating_image_pos.x(), self.canvas.placed_components[-1]['pos'].y())
                self.canvas.placed_components.append({'type': self.canvas.status, 'pos': wire_end_pos, 'color': QColor(255, 0, 0, 100)})
                if self.canvas.wires:
                    self.canvas.wires[-1]['end'] = copy(wire_end_pos)  # End of the wire
                self.canvas.update()  # Redraw to show the new component

                self.canvas.status = "wire_start"

                # Make floating image disappear until mouse moves
                self.canvas.show_floating_image = False

            elif self.canvas.status == "grab":
                self.last_mouse_pos = event.position()

    def handle_mouse_move(self, event: QMouseEvent):
        # Handle grid dragging when "Grab" is active
        if self.canvas.status == "grab" and self.last_mouse_pos:
            self.drag_canvas(event)
        self.update_floating_image(event)

    def handle_mouse_release(self, event: QMouseEvent):
        # Stop dragging when the mouse button is released
        if event.button() == Qt.LeftButton and self.canvas.status == "grab":
            self.last_mouse_pos = None

    def handle_wheel(self, event: QWheelEvent):
        # Calculate the zoom factor based on the wheel movement
        zoom_delta = event.angleDelta().y() / 120
        zoom_step = 0.1
        new_zoom_factor = self.canvas.zoom_factor + zoom_step * zoom_delta

        # Ensure the zoom factor is within reasonable bounds
        if 0.1 <= new_zoom_factor <= 5.0:

            mouse_pos = event.position()
            self.zoom_grid(mouse_pos, new_zoom_factor)
            self.zoom_components(mouse_pos, new_zoom_factor)
            self.zoom_wires(mouse_pos, new_zoom_factor)

            # Set the new zoom factor
            self.canvas.zoom_factor = new_zoom_factor

            # Trigger a redraw
            self.canvas.update()

    def handle_enter(self, event):
        self.canvas.update_cursor()  # Update cursor on entering the widget
        if self.canvas.status in ["wire_start", "wire_end"]:
            self.canvas.show_floating_image = True  # Show floating image when entering the canvas
        self.canvas.update()

    def handle_leave(self, event):
        self.canvas.setCursor(Qt.ArrowCursor)  # Reset cursor on leaving the widget
        self.canvas.show_floating_image = False  # Hide floating image when leaving the canvas
        self.canvas.update()

    def drag_canvas(self, event: QMouseEvent):
        delta = event.position() - self.last_mouse_pos
        self.canvas.offset -= delta  # Move the grid by the delta

        # Move placed components
        for comp in self.canvas.placed_components:
            comp['pos'] += delta
        for wire in self.canvas.wires:
            wire['start'] += delta
            wire['end'] += delta

        self.last_mouse_pos = event.position()  # Update the last mouse position
        self.canvas.update()  # Redraw the grid with the new offset

    def update_floating_image(self, event: QMouseEvent):
        # Make floating image show whenever mouse moves
        self.canvas.show_floating_image = True

        # Update the floating image's position
        mouse_pos = event.position()
        # Calculate the grid-aligned position
        zoomed_grid_size = self.canvas.grid_size * self.canvas.zoom_factor

        # Calculate the nearest grid point by rounding to the nearest grid cell
        x = round((mouse_pos.x() + self.canvas.offset.x()) / zoomed_grid_size) * zoomed_grid_size - self.canvas.offset.x()
        y = round((mouse_pos.y() + self.canvas.offset.y()) / zoomed_grid_size) * zoomed_grid_size - self.canvas.offset.y()

        self.canvas.floating_image_pos = QPointF(x, y)
        self.canvas.update()  # Redraw to show the square at the new position

    def zoom_wires(self, mouse_pos, new_zoom_factor):
        for wire in self.canvas.wires:
            distance_from_start_to_mouse = wire['start'] - mouse_pos
            distance_from_end_to_mouse = wire['end'] - mouse_pos
            new_distance_from_start_to_mouse = distance_from_start_to_mouse * (new_zoom_factor / self.canvas.zoom_factor)
            new_distance_from_end_to_mouse = distance_from_end_to_mouse * (new_zoom_factor / self.canvas.zoom_factor)
            wire['start'] = mouse_pos + new_distance_from_start_to_mouse
            wire['end'] = mouse_pos + new_distance_from_end_to_mouse

    def zoom_components(self, mouse_pos, new_zoom_factor):
        # Scale the distance from mouse to each component
        for comp in self.canvas.placed_components:
            distance_to_mouse = comp['pos'] - mouse_pos
            new_distance_to_mouse = distance_to_mouse * (new_zoom_factor / self.canvas.zoom_factor)
            comp['pos'] = mouse_pos + new_distance_to_mouse

    def zoom_grid(self, mouse_pos, new_zoom_factor):
        # Adjust the offset to keep the grid under the mouse stationary
        mouse_pos_before_zoom = (mouse_pos + self.canvas.offset) / (self.canvas.grid_size * self.canvas.zoom_factor)
        mouse_pos_after_zoom = (mouse_pos + self.canvas.offset) / (self.canvas.grid_size * new_zoom_factor)
        self.canvas.offset += (mouse_pos_before_zoom - mouse_pos_after_zoom) * self.canvas.grid_size * new_zoom_factor