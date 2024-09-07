from PySide6.QtGui import QColor, QPen
from PySide6.QtCore import Qt, QPointF
from copy import copy

class WireStart:
    def __init__(self, canvas):
        self.pos = None
        self.color = QColor(0, 0, 255, 100)
        self.overlap_color = QColor(255, 0, 0, 100)
        self.canvas = canvas
        self.canvas.dragging_enabled = False
        self.show_preview = True
        self.cursor = Qt.CrossCursor
        self.start_pos = None
        self.placed = False

    def draw(self, painter):
        if self.pos:
            if self.overlapping:
                pen = QPen(self.overlap_color)
                painter.setBrush(self.overlap_color)
            else:
                pen = QPen(self.color)
                painter.setBrush(self.color)
            pen.setWidth(5)
            painter.drawRect(self.pos.x() - 0.5 * self.canvas.grid.size, self.pos.y() - 0.5 * self.canvas.grid.size, self.canvas.grid.size, self.canvas.grid.size )  # 100x100 square

    def place(self):
        self.canvas.placed_components.append(self)
        self.canvas.active_tool = WireEnd(self.canvas, copy(self.pos))
        self.placed = True

    def move(self, delta):
        self.pos += delta

    def zoom(self, mouse_pos, new_grid_size):
        distance_to_mouse = self.pos - mouse_pos
        new_distance_to_mouse = distance_to_mouse * (new_grid_size / self.canvas.grid.size)
        self.pos = mouse_pos + new_distance_to_mouse

    def set_position(self, mouse_pos):
        self.pos = self.canvas.grid.snap(mouse_pos)

    @property
    def overlapping(self):
        if not self.placed and self.pos in [comp.pos for comp in self.canvas.placed_components]:
            return True
        else:
            return False

class WireEnd:
    def __init__(self, canvas, start_pos):
        self.pos = None
        self.start_pos = start_pos
        self.color = QColor(0, 255, 0, 100)
        self.overlap_color = QColor(255, 0, 0, 100)
        self.wire_color = QColor(0, 0, 0, 100)
        self.canvas = canvas
        self.show_preview = True
        self.cursor = Qt.CrossCursor
        self.placed = False

    def draw(self, painter):
        if self.pos:
            if self.overlapping:
                pen = QPen(self.overlap_color)
                painter.setBrush(self.overlap_color)
            else:
                pen = QPen(self.color)
                painter.setBrush(self.color)

            pen.setWidth(5)
            painter.setPen(pen)
            painter.drawRect(self.pos.x() - 0.5 * self.canvas.grid.size, self.start_pos.y() - 0.5 * self.canvas.grid.size, self.canvas.grid.size, self.canvas.grid.size)  # 100x100 square

            # draw wire
            pen = QPen(self.wire_color)
            pen.setWidth(5)
            painter.setPen(pen)
            painter.drawLine(QPointF(self.start_pos.x(), self.start_pos.y()), QPointF(self.pos.x(), self.start_pos.y()))

    def place(self):
        self.canvas.placed_components.append(self)
        self.canvas.active_tool = WireStart(self.canvas)
        self.placed = True

    def move(self, delta):
        self.pos += delta
        self.start_pos += delta

    def zoom(self, mouse_pos, new_grid_size):
        distance_to_mouse = self.pos - mouse_pos
        new_distance_to_mouse = distance_to_mouse * (new_grid_size / self.canvas.grid.size)
        self.pos = mouse_pos + new_distance_to_mouse

        distance_to_mouse = self.start_pos - mouse_pos
        new_distance_to_mouse = distance_to_mouse * (new_grid_size / self.canvas.grid.size)
        self.start_pos = mouse_pos + new_distance_to_mouse

    def set_position(self, mouse_pos):
        snapped_mouse_pos = self.canvas.grid.snap(mouse_pos)
        self.pos = QPointF(snapped_mouse_pos.x(), self.start_pos.y())

    @property
    def overlapping(self):
        if not self.placed and (self.pos in [comp.pos for comp in self.canvas.placed_components] or self.pos.x() < self.start_pos.x()):
            return True
        else:
            return False

class Grab:
    def __init__(self, canvas):
        self.canvas = canvas
        self.canvas.dragging_enabled = True
        self.show_preview = False
        self.cursor = Qt.SizeAllCursor
    def draw(self, painter):
        pass
    def place(self):
        pass
    def move(self, delta):
        pass
    def zoom(self, mouse_pos, new_grid_size):
        pass
    def set_position(self, mouse_pos):
        pass
    @property
    def overlapping(self):
        return False