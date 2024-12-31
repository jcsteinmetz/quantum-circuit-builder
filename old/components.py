from PySide6.QtWidgets import QSpinBox
from PySide6.QtGui import QPen
from PySide6.QtCore import Qt, QPointF
from copy import copy
import numpy as np

class BeamSplitter:
    def __init__(self, canvas):
        self.start_pos = None
        self.end_pos = None
        self.canvas = canvas
        self.canvas.dragging_enabled = False
        self.cursor = Qt.CrossCursor
        self.spinbox = None
        self.placed = False
        self.start_placed = False
        self.show_preview = False

    def draw(self, painter):
        if self.start_pos and self.end_pos and self.start_placed:
            # draw wire
            pen = QPen(self.canvas.style.wire_color)
            pen.setWidth(self.canvas.style.wire_width)
            painter.setPen(pen)
            painter.drawLine(QPointF(self.start_pos.x(), self.start_pos.y()), QPointF(self.end_pos.x(), self.end_pos.y()))

            # Draw wire end
            if not self.placeable:
                pen = QPen(self.canvas.style.overlap_color)
                painter.setBrush(self.canvas.style.overlap_color)
            else:
                pen = QPen(self.canvas.style.wire_color)
                painter.setBrush(self.canvas.style.wireend_color)

            pen.setWidth(self.canvas.style.wire_width)
            painter.setPen(pen)
            painter.drawRect(self.end_pos.x() - 0.25 * self.canvas.grid.size, self.end_pos.y() - 0.25 * self.canvas.grid.size, 0.5*self.canvas.grid.size, 0.5*self.canvas.grid.size)  # 100x100 square

        if self.start_pos:
            # Draw wire start
            if not self.placeable:
                pen = QPen(self.canvas.style.overlap_color)
                painter.setBrush(self.canvas.style.overlap_color)
            else:
                pen = QPen(self.canvas.style.wire_color)
                painter.setBrush(self.canvas.style.wirestart_color)
            pen.setWidth(self.canvas.style.wire_width)
            painter.setPen(pen)
            painter.drawRect(self.start_pos.x() - 0.25 * self.canvas.grid.size, self.start_pos.y() - 0.25 * self.canvas.grid.size, 0.5*self.canvas.grid.size, 0.5*self.canvas.grid.size)  # 100x100 square

    def place(self):
        if self.show_preview:
            if not self.start_placed:
                self.start_placed = True
                self.placeable = False
            elif not self.placeable:
                self.canvas.placed_components.append(self)
                self.canvas.active_tool = BeamSplitter(self.canvas)
                self.placed = True

    def move(self, delta):
        if self.start_pos:
            self.start_pos += delta
        if self.end_pos:
            self.end_pos += delta

    def zoom(self, mouse_pos, new_grid_size):
        if self.start_pos:
            distance_to_mouse = self.start_pos - mouse_pos
            new_distance_to_mouse = distance_to_mouse * (new_grid_size / self.canvas.grid.size)
            self.start_pos = mouse_pos + new_distance_to_mouse

        if self.end_pos:
            distance_to_mouse = self.end_pos - mouse_pos
            new_distance_to_mouse = distance_to_mouse * (new_grid_size / self.canvas.grid.size)
            self.end_pos = mouse_pos + new_distance_to_mouse

    def set_position(self, mouse_pos):
        if not self.start_placed:
            self.start_pos = self.canvas.grid.snap(mouse_pos)
            if self.placeable:
                self.show_preview = True
        else:
            if QPointF(self.start_pos.x(), self.canvas.grid.snap(mouse_pos).y()) == self.start_pos:
                self.end_pos = QPointF(self.start_pos.x(), self.canvas.grid.snap(mouse_pos).y() + self.canvas.grid.size)
            else:
                self.end_pos = QPointF(self.start_pos.x(), self.canvas.grid.snap(mouse_pos).y())
            
            self.placeable = False
            for comp in self.canvas.placed_components:
                if isinstance(comp, Wire) and self.end_pos.y() == comp.start_pos.y() and self.end_pos.x() > comp.start_pos.x() and self.end_pos.x() < comp.end_pos.x():
                    self.placeable = True

    def delete(self):
        # Remove the component itself from the canvas
        if self in self.canvas.placed_components:
            self.canvas.placed_components.remove(self)

    @property
    def occupied_coords(self):
        if not self.start_placed:
            return []
        if not self.placed:
            return [self.start_pos]
        else:
            return [QPointF(self.start_pos.x(), occ_y) for occ_y in np.linspace(min(self.start_pos.y(),self.end_pos.y()), max(self.start_pos.y(),self.end_pos.y()), round((abs(self.end_pos.y()-self.start_pos.y()))/self.canvas.grid.size) + 1)]
    
    @property
    def placeable(self):
        if self.start_pos and not self.start_placed:
            # check if it directly overlaps another component
            if any([self.start_pos in comp.occupied_coords for comp in self.canvas.placed_components if not isinstance(comp, Wire)]):
                return False
            # check if it's one square before another component, which wouldn't leave enough space for a WireEnd
            elif any([self.start_pos + QPointF(0, self.canvas.grid.size) in comp.occupied_coords for comp in self.canvas.placed_components]):
                return False
            for comp in self.canvas.placed_components:
                if isinstance(comp, Wire) and self.start_pos.y() == comp.start_pos.y() and self.start_pos.x() > comp.start_pos.x() and self.start_pos.x() < comp.end_pos.x():
                    return True
            return False
        elif self.start_pos and self.end_pos and not self.placed:
            # check if the end point directly overlaps another component
            if any([self.end_pos in comp.occupied_coords for comp in self.canvas.placed_components if not isinstance(comp, Wire)]):
                return False
            # check if the end point overlaps another part of the current component
            elif self.end_pos in self.occupied_coords:
                return False
            elif any([p in comp.occupied_coords for comp in self.canvas.placed_components if not isinstance(comp, Wire) for p in [QPointF(self.start_pos.x(), occupied_y) for occupied_y in np.arange(self.start_pos.y(), self.end_pos.y() + self.canvas.grid.size, self.canvas.grid.size)]]):
                return False
            else:
                return True
        else:
            return False

class Wire:
    def __init__(self, canvas):
        self.start_pos = None
        self.end_pos = None
        self.canvas = canvas
        self.canvas.dragging_enabled = False
        self.cursor = Qt.CrossCursor
        self.placed = False
        self.spinbox = None
        self.start_placed = False

        # Create and configure the spinbox when placing the component
        self.spinbox = QSpinBox(self.canvas)
        self.spinbox.setRange(0, 100)  # Set the range of the spinbox
        self.spinbox.setSingleStep(1)  # Set the step size for arrows
        self.spinbox.setValue(0)  # Set initial value
        self.show_preview = True

    def draw(self, painter):
        if self.start_pos and self.end_pos and self.start_placed:
            # draw wire
            pen = QPen(self.canvas.style.wire_color)
            pen.setWidth(self.canvas.style.wire_width)
            painter.setPen(pen)
            painter.drawLine(QPointF(self.start_pos.x(), self.start_pos.y()), QPointF(self.end_pos.x(), self.end_pos.y()))

            # Draw wire end
            if self.overlapping:
                pen = QPen(self.canvas.style.overlap_color)
                painter.setBrush(self.canvas.style.overlap_color)
            else:
                pen = QPen(self.canvas.style.wire_color)
                painter.setBrush(self.canvas.style.wireend_color)

            pen.setWidth(self.canvas.style.wire_width)
            painter.setPen(pen)
            painter.drawRect(self.end_pos.x() - 0.5 * self.canvas.grid.size, self.end_pos.y() - 0.5 * self.canvas.grid.size, self.canvas.grid.size, self.canvas.grid.size)  # 100x100 square

        if self.start_pos:
            # Draw wire start
            if self.overlapping:
                pen = QPen(self.canvas.style.overlap_color)
                painter.setBrush(self.canvas.style.overlap_color)
            else:
                pen = QPen(self.canvas.style.wire_color)
                painter.setBrush(self.canvas.style.wirestart_color)
            pen.setWidth(self.canvas.style.wire_width)
            painter.setPen(pen)
            painter.drawRect(self.start_pos.x() - 0.5 * self.canvas.grid.size, self.start_pos.y() - 0.5 * self.canvas.grid.size, self.canvas.grid.size, self.canvas.grid.size)  # 100x100 square

            # Draw the spinbox in the center of the square
            box_pos = self.start_pos - QPointF(self.spinbox.width() / 2, self.spinbox.height() / 2)
            self.spinbox.move(int(box_pos.x()), int(box_pos.y()))
            self.spinbox.resize(int(self.canvas.grid.size * 0.8), int(self.canvas.grid.size * 0.8))
            self.spinbox.show()

        if isinstance(self.canvas.active_tool, NormalCursor):
            self.spinbox.setEnabled(True)
        else:
            self.spinbox.setEnabled(False)

    def place(self):
        if not self.start_placed:
            self.start_placed = True
        else:
            self.canvas.placed_components.append(self)
            self.canvas.active_tool = Wire(self.canvas)
            self.placed = True

    def move(self, delta):
        if self.start_pos:
            self.start_pos += delta
            if self.placed and self.spinbox:
                box_pos = self.start_pos - QPointF(self.spinbox.width() / 2, self.spinbox.height() / 2)
                self.spinbox.move(int(box_pos.x()), int(box_pos.y()))
        if self.end_pos:
            self.end_pos += delta

    def zoom(self, mouse_pos, new_grid_size):
        if self.start_pos:
            distance_to_mouse = self.start_pos - mouse_pos
            new_distance_to_mouse = distance_to_mouse * (new_grid_size / self.canvas.grid.size)
            self.start_pos = mouse_pos + new_distance_to_mouse

        if self.end_pos:
            distance_to_mouse = self.end_pos - mouse_pos
            new_distance_to_mouse = distance_to_mouse * (new_grid_size / self.canvas.grid.size)
            self.end_pos = mouse_pos + new_distance_to_mouse

        if self.spinbox:
            self.spinbox.resize(int(new_grid_size * 0.8), int(new_grid_size * 0.8))

    def set_position(self, mouse_pos):
        if not self.start_placed:
            self.start_pos = self.canvas.grid.snap(mouse_pos)
        else:
            if QPointF(self.canvas.grid.snap(mouse_pos).x(), self.start_pos.y()) == self.start_pos:
                self.end_pos = QPointF(self.canvas.grid.snap(mouse_pos).x() + self.canvas.grid.size, self.start_pos.y())
            else:
                self.end_pos = QPointF(self.canvas.grid.snap(mouse_pos).x(), self.start_pos.y())

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
    def occupied_coords(self):
        if not self.start_placed:
            return []
        if not self.placed:
            return [self.start_pos]
        else:
            print(self.start_pos, self.end_pos, self.start_placed, self.placed)
            return [QPointF(occ_x, self.start_pos.y()) for occ_x in np.linspace(self.start_pos.x(), self.end_pos.x(), round((self.end_pos.x()-self.start_pos.x())/self.canvas.grid.size) + 1)]
    
    @property
    def overlapping(self):
        if self.start_pos and not self.start_placed:
            # check if it directly overlaps another component
            if any([self.start_pos in comp.occupied_coords for comp in self.canvas.placed_components]):
                return True
            # check if it's one square before another component, which wouldn't leave enough space for a WireEnd
            elif any([self.start_pos + QPointF(self.canvas.grid.size, 0) in comp.occupied_coords for comp in self.canvas.placed_components]):
                return True
            else:
                return False
        elif self.start_pos and self.end_pos and not self.placed:
            # check if the end point directly overlaps another component
            if any([self.end_pos in comp.occupied_coords for comp in self.canvas.placed_components]):
                return True
            # check if the end point overlaps another part of the current component
            elif self.end_pos in self.occupied_coords:
                return True
            # make sure the end point comes after the start point
            elif self.end_pos.x() <= self.start_pos.x():
                return True
            # check if ANY point overlaps any other component
            elif any([p in comp.occupied_coords for comp in self.canvas.placed_components for p in [QPointF(occupied_x, self.start_pos.y()) for occupied_x in np.arange(self.start_pos.x(), self.end_pos.x() + self.canvas.grid.size, self.canvas.grid.size)]]):
                return True
            else:
                return False
        else:
            return False

class Grab:
    def __init__(self, canvas):
        self.canvas = canvas
        self.canvas.dragging_enabled = True
        self.cursor = Qt.OpenHandCursor
        self.spinbox = None
        self.show_preview = False

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
        self.cursor = Qt.ArrowCursor
        self.spinbox = None
        self.show_preview = False

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