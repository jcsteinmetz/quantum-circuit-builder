from PySide6.QtGui import QColor
import numpy as np

class Grid:
    def __init__(self, canvas):
        self.canvas = canvas
        self.size = 50
        self.offset = (0, 0)

    def draw(self, painter):
        # Fill in background
        painter.fillRect(self.canvas.rect(), QColor(*self.canvas.bg_color))

        # Draw grid lines
        painter.setPen(QColor(*self.canvas.gridline_color))

        for x in np.arange(-self.offset[0] % self.size, self.canvas.width(), self.size):
            painter.drawLine(x, 0, x, self.canvas.height())

        for y in np.arange(-self.offset[1] % self.size, self.canvas.height(), self.size):
            painter.drawLine(0, y, self.canvas.width(), y)

    def zoom(self, mouse_pos, new_grid_size):
        mouse_pos_before_zoom = ((mouse_pos[0] + self.offset[0])/self.size, (mouse_pos[1] + self.offset[1])/self.size)
        mouse_pos_after_zoom = ((mouse_pos[0] + self.offset[0])/new_grid_size, (mouse_pos[1] + self.offset[1])/new_grid_size)
        self.offset = (self.offset[0] + (mouse_pos_before_zoom[0] - mouse_pos_after_zoom[0])*new_grid_size, self.offset[1] + (mouse_pos_before_zoom[1] - mouse_pos_after_zoom[1])*new_grid_size)

    def snap(self, pos):
        x = round((pos[0] + self.offset[0]) / self.size) * self.size - self.offset[0]
        y = round((pos[1] + self.offset[1]) / self.size) * self.size - self.offset[1]
        return (x, y)