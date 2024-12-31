from PySide6.QtCore import Qt, QPointF, QRectF
from PySide6.QtGui import QColor, QPen
from copy import copy
from abc import ABC, abstractmethod

class Select:
    def __init__(self, window):
        self.window = window
        self.placeable = False

    def set_cursor(self):
        self.window.canvas.setCursor(Qt.ArrowCursor)

class Grab:
    def __init__(self, window):
        self.window = window
        self.placeable = False
        self.cursor = Qt.OpenHandCursor

    def set_dragging_cursor(self):
        self.window.canvas.setCursor(Qt.ClosedHandCursor)

    def set_cursor(self):
        self.window.canvas.setCursor(Qt.OpenHandCursor)

class Component(ABC):
    def __init__(self, window):
        self.window = window
        self.position = None
        self.cursor = Qt.CrossCursor
        self.is_selected = False

        # Default style
        self.color = None
        self.border_color = None
        self.line_width = 3
        self.shape_scale = 1
        self.shape_type = "square"
        self.error_color = (255, 0, 0)
        self.set_style()

    @property
    @abstractmethod
    def placeable(self):
        raise NotImplementedError
    
    def set_cursor(self):
        self.window.canvas.setCursor(self.cursor)

    # Colors

    def _transparent(self, col):
        transparent_col = copy(col)
        transparent_col.setAlpha(0.5*col.alpha())
        return transparent_col
    
    def _invert(self, col):
        return (255-col[0], 255-col[1], 255-col[2])
    
    # Drawing

    @property
    def snappedPosition(self):
        if not self.position:
            return self.window.canvas.grid.snap(self.window.canvas.event_handler.mouse_position)
        elif hasattr(self, "end_position"):
            if self.position and not self.end_position:
                # Wires are horizontal
                if isinstance(self, Wire):
                    x = self.window.canvas.grid.snap(self.window.canvas.event_handler.mouse_position)[0]
                    y = self.window.canvas.grid.snap(self.position)[1]
                    return (x, y)
                # Other double components are vertical
                x = self.window.canvas.grid.snap(self.position)[0]
                y = self.window.canvas.grid.snap(self.window.canvas.event_handler.mouse_position)[1]
                return (x, y)
            
    def set_style(self):
        self.color = (0, 0, 0)
        if not self.is_selected:
            self.border_color = (0, 0, 0)
        else:
            self.border_color = (219, 197, 119)
            # self.border_color = (0, 128, 255)

    @property
    def name(self):
        all_components = self.window.canvas.placed_components["wires"] + self.window.canvas.placed_components["components"] + self.window.canvas.placed_components["detectors"]
        overall_index = all_components.index(self)
        type_index = sum(isinstance(i, self.__class__) for i in all_components[:overall_index])
        child_name = type(self).__name__[0] + str(type_index+1)
        return child_name

    def draw_name(self, painter, pos):
        inverse_color = self._invert(self.color)
        pen = QPen(QColor(*inverse_color))
        pen.setWidth(self.line_width)
        painter.setPen(pen)
        scale = self.shape_scale * self.window.canvas.grid.size
        rectangle = QRectF(pos[0] - 0.5*scale, pos[1] - 0.5*scale, scale, scale)
        painter.drawText(rectangle, Qt.AlignCenter, self.name)

    def draw_shape(self, painter, pos, shape_type):
        scale = self.shape_scale * self.window.canvas.grid.size

        pos = QPointF(pos[0], pos[1])

        bottom_left = QPointF(pos.x() - 0.5*scale, pos.y() - 0.5*scale)
        top_left = QPointF(pos.x() - 0.5*scale, pos.y() + 0.5*scale)
        bottom_right = QPointF(pos.x() + 0.5*scale, pos.y() - 0.5*scale)
        top_right = QPointF(pos.x() + 0.5*scale, pos.y() + 0.5*scale)

        if shape_type == "square":
            painter.drawRect(bottom_left.x(), bottom_left.y(), scale, scale)

    def move(self, delta):
        if self.position:
            self.position = (self.position[0] + delta[0], self.position[1] + delta[1])
        if hasattr(self, "end_position"):
            if self.end_position:
                self.end_position = (self.end_position[0] + delta[0], self.end_position[1] + delta[1])

    def zoom(self, mouse_pos, new_grid_size):
        if self.position:
            distance_to_mouse = (self.position[0] - mouse_pos[0], self.position[1] - mouse_pos[1])
            new_distance_to_mouse = (distance_to_mouse[0] * (new_grid_size / self.window.canvas.grid.size), distance_to_mouse[1] * (new_grid_size / self.window.canvas.grid.size))
            self.position = (mouse_pos[0] + new_distance_to_mouse[0], mouse_pos[1] + new_distance_to_mouse[1])
        if hasattr(self, "end_position"):
            if self.end_position:
                distance_to_mouse = (self.end_position[0] - mouse_pos[0], self.end_position[1] - mouse_pos[1])
                new_distance_to_mouse = (distance_to_mouse[0] * (new_grid_size / self.window.canvas.grid.size), distance_to_mouse[1] * (new_grid_size / self.window.canvas.grid.size))
                self.end_position = (mouse_pos[0] + new_distance_to_mouse[0], mouse_pos[1] + new_distance_to_mouse[1])

    # Placeable checks

    def overlaps_a_wire(self, pos):
        for comp in self.window.canvas.placed_components["wires"]:
            snapped_wire_start_point = self.window.canvas.grid.snap(comp.position)
            snapped_wire_end_point = self.window.canvas.grid.snap(comp.end_position)
            if pos[1] == snapped_wire_start_point[1]:
                if snapped_wire_start_point[0] < pos[0] < snapped_wire_end_point[0]:
                    return True
        return False
    
    def overlaps_a_wire_edge(self, pos):
        for comp in self.window.canvas.placed_components["wires"]:
            snapped_wire_start_point = self.window.canvas.grid.snap(comp.position)
            snapped_wire_end_point = self.window.canvas.grid.snap(comp.end_position)
            if pos[1] == snapped_wire_start_point[1]:
                if snapped_wire_start_point[0] == pos[0]:
                    return True
                if snapped_wire_end_point[0] == pos[0]:
                    return True
        return False
    
    def overlaps_a_component(self, pos):
        for comp in self.window.canvas.placed_components["components"]:
            if issubclass(comp.__class__, DoubleComponent):
                snapped_comp_start_point = self.window.canvas.grid.snap(comp.position)
                snapped_comp_end_point = self.window.canvas.grid.snap(comp.end_position)
                if pos[0] == snapped_comp_start_point[0]:
                    if snapped_comp_start_point[1] <= pos[1] <= snapped_comp_end_point[1]:
                        return True
                    if snapped_comp_end_point[1] <= pos[1] <= snapped_comp_start_point[1]:
                        return True
            elif issubclass(comp.__class__, SingleComponent):
                if pos == self.window.canvas.grid.snap(comp.position):
                    return True
        return False
    
    def overlaps_itself(self, pos):
        if self.position:
            if pos == self.window.canvas.grid.snap(self.position):
                return True
        return False
    
    def spans_a_component(self, pos):
        if self.position:
            for comp_list in self.window.canvas.placed_components.values():
                for comp in comp_list:
                    snapped_comp_start_point = self.window.canvas.grid.snap(comp.position)
                    if self.position[0] == snapped_comp_start_point[0]:
                        if hasattr(comp, "end_position"):
                            snapped_comp_end_point = self.window.canvas.grid.snap(comp.end_position)
                            if self.position[1] <= snapped_comp_start_point[1] and pos[1] >= snapped_comp_end_point[1]:
                                return True
                            if self.position[1] <= snapped_comp_end_point[1] and pos[1] >= snapped_comp_start_point[1]:
                                return True
                            if self.position[1] >= snapped_comp_start_point[1] and pos[1] <= snapped_comp_end_point[1]:
                                return True
                            if self.position[1] >= snapped_comp_end_point[1] and pos[1] <= snapped_comp_start_point[1]:
                                return True
                        else:
                            if self.position[1] <= snapped_comp_start_point[1] and pos[1] >= snapped_comp_start_point[1]:
                                return True
                            if pos[1] <= snapped_comp_start_point[1] and self.position[1] >= snapped_comp_start_point[1]:
                                return True
        return False
    
    def spans_a_wire(self, pos):
        if self.position:
            # Can't be on the opposite side of a wire from the start point
            for comp in self.window.canvas.placed_components["wires"]:
                snapped_comp_start_point = self.window.canvas.grid.snap(comp.position)
                snapped_comp_end_point = self.window.canvas.grid.snap(comp.end_position)
                if self.position[1] == snapped_comp_start_point[1]:
                    if self.position[0] <= snapped_comp_start_point[0] and pos[0] >= snapped_comp_end_point[0]:
                        return True
                    if self.position[0] >= snapped_comp_end_point[0] and pos[0] <= snapped_comp_start_point[0]:
                        return True
        return False
    
class SingleComponent(Component):
    def __init__(self, window):
        super().__init__(window)
        self.hide = False

class DoubleComponent(Component):
    def __init__(self, window):
        super().__init__(window)
        self.end_position = None
        self.end_shape_type = "square"
        self.hide_start = False
        self.hide_end = False

    def place(self):
        if not self.position:
            self.position = copy(self.snappedPosition)
        elif not self.end_position:
            self.end_position = copy(self.snappedPosition)
            self.window.canvas.active_tool = self.__class__(self.window)
            if isinstance(self, Wire):
                self.window.canvas.placed_components["wires"].append(self)
            else:
                self.window.canvas.placed_components["components"].append(self)
            self.window.canvas.sort_components()
    
    def preview(self, painter):
        if not self.position:
            pen = QPen(self._transparent(QColor(*self.border_color)))
            pen.setWidth(self.line_width)
            painter.setPen(pen)

            if self.placeable:
                painter.setBrush(self._transparent(QColor(*self.color)))
            else:
                painter.setBrush(self._transparent(QColor(*self.error_color)))
            self.draw_shape(painter, self.snappedPosition, self.shape_type)

        elif not self.end_position:
            pen = QPen(QColor(*self.border_color))
            pen.setWidth(self.line_width)
            painter.setPen(pen)

            # draw wire start
            painter.setBrush(QColor(*self.color))
            self.draw_shape(painter, self.position, self.shape_type)

            pen = QPen(self._transparent(QColor(*self.border_color)))
            pen.setWidth(self.line_width)
            painter.setPen(pen)

            # draw wire
            painter.drawLine(QPointF(self.position[0], self.position[1]), QPointF(self.snappedPosition[0], self.snappedPosition[1]))

            # draw wire end
            if self.placeable:
                painter.setBrush(self._transparent(QColor(*self.color)))
            else:
                painter.setBrush(self._transparent(QColor(*self.error_color)))
            self.draw_shape(painter, self.snappedPosition, self.end_shape_type)

    def draw(self, painter):
        if self.end_position:
            # draw wire
            pen = QPen(QColor(*self.border_color))
            pen.setWidth(self.line_width)
            painter.setPen(pen)
            painter.drawLine(QPointF(self.position[0], self.position[1]), QPointF(self.end_position[0], self.end_position[1]))

            if not self.hide_end:
                # draw wire end
                pen = QPen(QColor(*self.border_color))
                pen.setWidth(self.line_width)
                painter.setPen(pen)
                painter.setBrush(QColor(*self.color))
                self.draw_shape(painter, self.end_position, self.end_shape_type)

        if self.position:
            if not self.hide_start:
                # draw wire start
                pen = QPen(QColor(*self.border_color))
                pen.setWidth(self.line_width)
                painter.setPen(pen)
                painter.setBrush(QColor(*self.color))
                self.draw_shape(painter, self.position, self.shape_type)
                self.draw_name(painter, self.position)

class Wire(DoubleComponent):
    def __init__(self, window):
        super().__init__(window)

        # Style
        self.shape_scale = 0.75
        self.end_shape_type = None

    @property
    def placeable(self):
        if self.overlaps_a_wire(self.snappedPosition):
            return False
        if self.overlaps_a_wire_edge(self.snappedPosition):
            return False
        if self.overlaps_a_component(self.snappedPosition):
            return False
        
        # Rules for the start point
        if not self.position:
            # Can't place it on the point immediately to the left of another wire, which would leave no room for the end point
            for comp in self.window.canvas.placed_components["wires"]:
                snapped_comp_start_point = self.window.canvas.grid.snap(comp.position)
                if self.snappedPosition[1] == snapped_comp_start_point[1]:
                    if self.window.canvas.grid.snap((self.snappedPosition[0] + self.window.canvas.grid.size, self.snappedPosition[1])) == snapped_comp_start_point:
                        return False
        
        # Rules for the end point
        if self.position:
            # The end point must be to the right of the start point
            if self.snappedPosition[0] <= self.window.canvas.grid.snap(self.position)[0]:
                return False
            
        if self.spans_a_wire(self.snappedPosition):
            return False
        return True
    