from PySide6.QtWidgets import QSpinBox
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
        self.spinbox = None

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

        # Draw the spinbox in the center of the square
        if self.placed and self.spinbox:
            box_pos = self.pos - QPointF(self.spinbox.width() / 2, self.spinbox.height() / 2)
            self.spinbox.move(int(box_pos.x()), int(box_pos.y()))
            self.spinbox.show()

            if isinstance(self.canvas.active_tool, NormalCursor):
                self.spinbox.setEnabled(True)
            else:
                self.spinbox.setEnabled(False)

    def place(self):
        self.canvas.placed_components.append(self)
        self.canvas.active_tool = WireEnd(self.canvas, copy(self.pos))
        self.placed = True

        # Create and configure the spinbox when placing the component
        self.spinbox = QSpinBox(self.canvas)
        self.spinbox.setRange(0, 100)  # Set the range of the spinbox
        self.spinbox.setSingleStep(1)  # Set the step size for arrows
        self.spinbox.setValue(0)  # Set initial value

        # Position the spinbox inside the square
        box_pos = self.pos - QPointF(self.spinbox.width() / 2, self.spinbox.height() / 2)
        self.spinbox.move(int(box_pos.x()), int(box_pos.y()))
        self.spinbox.resize(int(self.canvas.grid.size * 0.8), int(self.canvas.grid.size * 0.8))
        self.spinbox.show()

    def move(self, delta):
        self.pos += delta
        if self.placed and self.spinbox:
            box_pos = self.pos - QPointF(self.spinbox.width() / 2, self.spinbox.height() / 2)
            self.spinbox.move(int(box_pos.x()), int(box_pos.y()))

    def zoom(self, mouse_pos, new_grid_size):
        distance_to_mouse = self.pos - mouse_pos
        new_distance_to_mouse = distance_to_mouse * (new_grid_size / self.canvas.grid.size)
        self.pos = mouse_pos + new_distance_to_mouse

        self.spinbox.resize(int(new_grid_size * 0.8), int(new_grid_size * 0.8))

    def set_position(self, mouse_pos):
        self.pos = self.canvas.grid.snap(mouse_pos)

    def delete(self):
        # Remove the spinbox if it exists
        if self.spinbox:
            self.spinbox.hide()  # Hide the spinbox
            self.spinbox.deleteLater()  # Schedule it for deletion
            self.spinbox = None

        # Remove the component itself from the canvas
        if self in self.canvas.placed_components:
            self.canvas.placed_components.remove(self)

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

    def delete(self):
        # Remove the component itself from the canvas
        if self in self.canvas.placed_components:
            self.canvas.placed_components.remove(self)

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
    def delete(self):
        pass
    @property
    def overlapping(self):
        return False
    
class NormalCursor:
    def __init__(self, canvas):
        self.canvas = canvas
        self.canvas.dragging_enabled = False
        self.show_preview = False
        self.cursor = Qt.ArrowCursor

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
    def delete(self):
        pass
    @property
    def overlapping(self):
        return False