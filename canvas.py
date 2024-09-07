import numpy as np
from PySide6.QtWidgets import QWidget
from PySide6.QtCore import Qt, QPointF
from PySide6.QtGui import QPainter, QColor, QPen
from event_handler import EventHandler

class Canvas(QWidget):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.grid_size = 100  # Size of each grid cell
        self.zoom_factor = 1.0  # Initial zoom factor
        self.status = "grab"  # Track which button is toggled
        self.offset = QPointF(0, 0)  # Offset for grid dragging
        self.show_floating_image = False  # Track if square should be shown
        self.floating_image_pos = QPointF(0, 0)  # Position of the square
        self.setMouseTracking(True)
        self.placed_components = []  # List to store placed components
        self.wires = []  # List to store wires with their start and end positions
        self.update_cursor()
        self.event_handler = EventHandler(self)

    def update_floating_image(self, mouse_pos):
        # Make floating image show whenever mouse moves
        self.show_floating_image = True

        # Calculate the grid-aligned position
        self.floating_image_pos = self.snap(mouse_pos)

        # Redraw to show the square at the new position
        self.update()
    
    def snap(self, mouse_pos):
        zoomed_grid_size = self.grid_size * self.zoom_factor

        # Calculate the nearest grid point by rounding to the nearest grid cell
        x = round((mouse_pos.x() + self.offset.x()) / zoomed_grid_size) * zoomed_grid_size - self.offset.x()
        y = round((mouse_pos.y() + self.offset.y()) / zoomed_grid_size) * zoomed_grid_size - self.offset.y()
        return QPointF(x, y)
    
    def drag(self, delta):
        self.offset -= delta  # Move the grid by the delta

        # Move placed components
        for comp in self.placed_components:
            comp['pos'] += delta
        for wire in self.wires:
            wire['start'] += delta
            wire['end'] += delta

        self.update()  # Redraw the grid with the new offset

    def zoom(self, mouse_pos, new_zoom_factor):
        # Ensure the zoom factor is within reasonable bounds
        if 0.1 <= new_zoom_factor <= 5.0:
            self.zoom_grid(mouse_pos, new_zoom_factor)
            self.zoom_components(mouse_pos, new_zoom_factor)
            self.zoom_wires(mouse_pos, new_zoom_factor)

            # Set the new zoom factor
            self.zoom_factor = new_zoom_factor

            # Trigger a redraw
            self.update()
    
    def zoom_wires(self, mouse_pos, new_zoom_factor):
        for wire in self.wires:
            distance_from_start_to_mouse = wire['start'] - mouse_pos
            distance_from_end_to_mouse = wire['end'] - mouse_pos
            new_distance_from_start_to_mouse = distance_from_start_to_mouse * (new_zoom_factor / self.zoom_factor)
            new_distance_from_end_to_mouse = distance_from_end_to_mouse * (new_zoom_factor / self.zoom_factor)
            wire['start'] = mouse_pos + new_distance_from_start_to_mouse
            wire['end'] = mouse_pos + new_distance_from_end_to_mouse

    def zoom_components(self, mouse_pos, new_zoom_factor):
        # Scale the distance from mouse to each component
        for comp in self.placed_components:
            distance_to_mouse = comp['pos'] - mouse_pos
            new_distance_to_mouse = distance_to_mouse * (new_zoom_factor / self.zoom_factor)
            comp['pos'] = mouse_pos + new_distance_to_mouse

    def zoom_grid(self, mouse_pos, new_zoom_factor):
        # Adjust the offset to keep the grid under the mouse stationary
        mouse_pos_before_zoom = (mouse_pos + self.offset) / (self.grid_size * self.zoom_factor)
        mouse_pos_after_zoom = (mouse_pos + self.offset) / (self.grid_size * new_zoom_factor)
        self.offset += (mouse_pos_before_zoom - mouse_pos_after_zoom) * self.grid_size * new_zoom_factor

    def update_cursor(self):
        if self.status == "grab":
            self.setCursor(Qt.SizeAllCursor)
        elif self.status in ["wire_start", "wire_end"]:
            self.setCursor(Qt.CrossCursor)
        else:
            self.setCursor(Qt.ArrowCursor)

    def paintEvent(self, event):
        painter = QPainter(self)

        # Fill the canvas with the background color
        painter.fillRect(self.rect(), QColor(255, 255, 255))

        # Light gray color for grid lines
        painter.setPen(QColor(200, 200, 200))

        self.draw_grid(painter)

        # Draw placed components
        for component in self.placed_components:
            self.draw_component(painter, component)

        # Draw wires
        for wire in self.wires:
            self.draw_wire(painter, wire)

        # Draw a floating image if needed
        if self.show_floating_image:
            self.draw_floating_image()

    def draw_grid(self, painter):
        # Apply zoom factor to grid size
        zoomed_grid_size = self.grid_size * self.zoom_factor

        # Draw vertical grid lines
        for x in np.arange(-self.offset.x() % zoomed_grid_size, self.width(), zoomed_grid_size):
            painter.drawLine(x, 0, x, self.height())

        # Draw horizontal grid lines
        for y in np.arange(-self.offset.y() % zoomed_grid_size, self.height(), zoomed_grid_size):
            painter.drawLine(0, y, self.width(), y)

    def draw_wire(self, painter, wire):
        if wire['start'] and wire['end']:
            pen = QPen(QColor(0, 0, 0, 100))
            pen.setWidth(5)  # Set the width of the line (you can adjust this value)
            painter.setPen(pen)
            painter.drawLine(QPointF(wire['start'].x(), wire['start'].y()), QPointF(wire['end'].x(), wire['end'].y()))

    def draw_component(self, painter, comp):
        pen = QPen(comp['color'])
        pen.setWidth(5)  # Set the width of the line (you can adjust this value)
        painter.setPen(pen)
        painter.setBrush(comp['color'])  # Semi-transparent blue color
        painter.drawRect(comp['pos'].x() - 50 * self.zoom_factor, comp['pos'].y() - 50 * self.zoom_factor, 100 * self.zoom_factor, 100 * self.zoom_factor)  # 100x100 square

    def draw_floating_image(self):
        painter = QPainter(self)
        if self.status == "wire_start":
            pen = QPen(QColor(0, 0, 255, 100))
            pen.setWidth(5)  # Set the width of the line (you can adjust this value)
            painter.setPen(pen)
            painter.setBrush(QColor(0, 0, 255, 100))  # Semi-transparent blue color
            painter.drawRect(self.floating_image_pos.x() - 50 * self.zoom_factor, self.floating_image_pos.y() - 50 * self.zoom_factor, 100 * self.zoom_factor, 100 * self.zoom_factor)  # 100x100 square

        elif self.status == "wire_end":
            if self.wires:
                wire_start_pos = self.wires[-1]['start']
                wire_end_pos = self.floating_image_pos

                pen = QPen(QColor(0, 0, 0, 100))
                pen.setWidth(5)  # Set the width of the line (you can adjust this value)
                painter.setPen(pen)
                painter.drawLine(QPointF(wire_start_pos.x(), wire_start_pos.y()), QPointF(wire_end_pos.x(), wire_start_pos.y()))

                pen = QPen(QColor(255, 0, 0, 100))
                pen.setWidth(5)  # Set the width of the line (you can adjust this value)
                painter.setPen(pen)
                painter.setBrush(QColor(255, 0, 0, 100))  # Semi-transparent red color
                painter.drawRect(wire_end_pos.x() - 50 * self.zoom_factor, wire_start_pos.y() - 50 * self.zoom_factor, 100 * self.zoom_factor, 100 * self.zoom_factor)  # 100x100 square