import numpy as np
from PySide6.QtWidgets import QWidget
from PySide6.QtCore import QPointF
from PySide6.QtGui import QPainter, QColor, QPen
from event_handler import EventHandler
from components import Grab

class Canvas(QWidget):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.grid_size = 100  # Size of each grid cell
        self.zoom_factor = 1.0  # Initial zoom factor
        self.dragging_enabled = False  # Track which button is toggled
        self.offset = QPointF(0, 0)  # Offset for grid dragging
        self.setMouseTracking(True)
        self.event_handler = EventHandler(self)

        self.active_tool = Grab(self)
        self.components = []

    def paintEvent(self, event):
        painter = QPainter(self)

        self.draw_grid(painter)

        # Draw placed components
        for comp in self.components:
            comp.draw(painter, self.zoom_factor)

        # Draw active tool preview
        if self.active_tool and self.active_tool.show_preview:
            self.active_tool.draw(painter, self.zoom_factor)
    
    def snap(self, mouse_pos):
        zoomed_grid_size = self.grid_size * self.zoom_factor

        # Calculate the nearest grid point by rounding to the nearest grid cell
        x = round((mouse_pos.x() + self.offset.x()) / zoomed_grid_size) * zoomed_grid_size - self.offset.x()
        y = round((mouse_pos.y() + self.offset.y()) / zoomed_grid_size) * zoomed_grid_size - self.offset.y()
        return QPointF(x, y)
    
    def drag(self, delta):
        self.offset -= delta  # Move the grid by the delta

        for comp in self.components:
            comp.move(delta)

        self.update()  # Redraw the grid with the new offset

    def zoom(self, mouse_pos, new_zoom_factor):
        # Ensure the zoom factor is within reasonable bounds
        if 0.1 <= new_zoom_factor <= 5.0:
            self.zoom_grid(mouse_pos, new_zoom_factor)
            self.zoom_components(mouse_pos, new_zoom_factor)

            # Set the new zoom factor
            self.zoom_factor = new_zoom_factor

            # Trigger a redraw
            self.update()

    def zoom_components(self, mouse_pos, new_zoom_factor):
        # Scale the distance from mouse to each component
        for comp in self.components:
            distance_to_mouse = comp.pos - mouse_pos
            new_distance_to_mouse = distance_to_mouse * (new_zoom_factor / self.zoom_factor)
            comp.pos = mouse_pos + new_distance_to_mouse
            if comp.start_pos:
                distance_to_mouse = comp.start_pos - mouse_pos
                new_distance_to_mouse = distance_to_mouse * (new_zoom_factor / self.zoom_factor)
                comp.start_pos = mouse_pos + new_distance_to_mouse

    def zoom_grid(self, mouse_pos, new_zoom_factor):
        # Adjust the offset to keep the grid under the mouse stationary
        mouse_pos_before_zoom = (mouse_pos + self.offset) / (self.grid_size * self.zoom_factor)
        mouse_pos_after_zoom = (mouse_pos + self.offset) / (self.grid_size * new_zoom_factor)
        self.offset += (mouse_pos_before_zoom - mouse_pos_after_zoom) * self.grid_size * new_zoom_factor

    def draw_grid(self, painter):
        # Fill the canvas with the background color
        painter.fillRect(self.rect(), QColor(255, 255, 255))

        # Light gray color for grid lines
        painter.setPen(QColor(200, 200, 200))

        # Apply zoom factor to grid size
        zoomed_grid_size = self.grid_size * self.zoom_factor

        # Draw vertical grid lines
        for x in np.arange(-self.offset.x() % zoomed_grid_size, self.width(), zoomed_grid_size):
            painter.drawLine(x, 0, x, self.height())

        # Draw horizontal grid lines
        for y in np.arange(-self.offset.y() % zoomed_grid_size, self.height(), zoomed_grid_size):
            painter.drawLine(0, y, self.width(), y)