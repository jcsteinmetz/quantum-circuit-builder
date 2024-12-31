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