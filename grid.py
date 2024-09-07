from PySide6.QtGui import QColor
from PySide6.QtCore import QPointF
import numpy as np

class Grid:
    def __init__(self, canvas):
        self.canvas = canvas
        self.size = 100  # Size of each grid cell
        self.offset = QPointF(0, 0)
        self.line_color = QColor(200, 200, 200)
        self.bg_color = QColor(255, 255, 255)
    
    def draw(self, painter):
        # Fill in background
        painter.fillRect(self.canvas.rect(), self.bg_color)

        # Draw grid lines
        painter.setPen(self.line_color)

        for x in np.arange(-self.offset.x() % self.size, self.canvas.width(), self.size):
            painter.drawLine(x, 0, x, self.canvas.height())

        for y in np.arange(-self.offset.y() % self.size, self.canvas.height(), self.size):
            painter.drawLine(0, y, self.canvas.width(), y)

    def zoom(self, mouse_pos, new_grid_size):
        # Adjust the offset to keep the grid under the mouse stationary
        mouse_pos_before_zoom = (mouse_pos + self.offset) / self.size
        mouse_pos_after_zoom = (mouse_pos + self.offset) / new_grid_size
        self.offset += (mouse_pos_before_zoom - mouse_pos_after_zoom) * new_grid_size

    def snap(self, mouse_pos):
        # Calculate the nearest grid point by rounding to the nearest grid cell
        x = round((mouse_pos.x() + self.offset.x()) / self.size) * self.size - self.offset.x()
        y = round((mouse_pos.y() + self.offset.y()) / self.size) * self.size - self.offset.y()
        return QPointF(x, y)