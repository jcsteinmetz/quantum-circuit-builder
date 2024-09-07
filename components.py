from PySide6.QtGui import QColor, QPen
from PySide6.QtCore import Qt, QPointF
from copy import copy

class WireStart:
    def __init__(self, canvas):
        self.pos = None
        self.color = QColor(0, 0, 255, 100)
        self.canvas = canvas
        self.canvas.dragging_enabled = False
        self.show_preview = True
        self.cursor = Qt.CrossCursor
        self.start_pos = None

    def draw(self, painter, zoom_factor):
        if self.pos:
            pen = QPen(self.color)
            pen.setWidth(5)  # Set the width of the line (you can adjust this value)
            painter.setPen(pen)
            painter.setBrush(self.color)  # Semi-transparent blue color
            painter.drawRect(self.pos.x() - 0.5 * self.canvas.grid_size * zoom_factor, self.pos.y() - 0.5 * self.canvas.grid_size * zoom_factor, self.canvas.grid_size * zoom_factor, self.canvas.grid_size * zoom_factor)  # 100x100 square

    def place(self):
        self.canvas.components.append(self)
        self.canvas.active_tool = WireEnd(self.canvas, copy(self.pos))

    def move(self, delta):
        self.pos += delta

class WireEnd:
    def __init__(self, canvas, start_pos):
        self.pos = None
        self.start_pos = start_pos
        self.color = QColor(255, 0, 0, 100)
        self.wire_color = QColor(0, 0, 0, 100)
        self.canvas = canvas
        self.show_preview = True
        self.cursor = Qt.CrossCursor

    def draw(self, painter, zoom_factor):
        if self.pos:
            pen = QPen(self.color)
            pen.setWidth(5)  # Set the width of the line (you can adjust this value)
            painter.setPen(pen)
            painter.setBrush(self.color)  # Semi-transparent blue color
            painter.drawRect(self.pos.x() - 0.5 * self.canvas.grid_size * zoom_factor, self.start_pos.y() - 0.5 * self.canvas.grid_size * zoom_factor, self.canvas.grid_size * zoom_factor, self.canvas.grid_size * zoom_factor)  # 100x100 square

            # draw wire
            pen = QPen(self.wire_color)
            pen.setWidth(5)  # Set the width of the line (you can adjust this value)
            painter.setPen(pen)
            painter.drawLine(QPointF(self.start_pos.x(), self.start_pos.y()), QPointF(self.pos.x(), self.start_pos.y()))

    def place(self):
        self.canvas.components.append(self)
        self.canvas.active_tool = WireStart(self.canvas)

    def move(self, delta):
        self.pos += delta
        self.start_pos += delta

class Grab:
    def __init__(self, canvas):
        self.canvas = canvas
        self.canvas.dragging_enabled = True
        self.show_preview = False
        self.cursor = Qt.SizeAllCursor
    def draw(self, painter, zoom_factor):
        pass
    def place(self):
        pass
    def move(self, delta):
        pass