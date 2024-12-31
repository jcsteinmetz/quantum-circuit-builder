from PySide6.QtCore import Qt, QPointF, QRectF
from PySide6.QtGui import QColor, QPen, QIntValidator, QDoubleValidator
from copy import copy
from abc import ABC, abstractmethod
from properties_manager import PropertiesManager

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

        # Property manager
        self.property_manager = PropertiesManager(self, self.window.canvas)

        # Default style
        self.color = None
        self.border_color = None
        self.line_width = 3
        self.shape_scale = 1
        self.shape_type = "square"
        self.error_color = (255, 0, 0)
        self.set_style()

    # Setup

    @abstractmethod
    def create_property_manager(self):
        raise NotImplementedError

    @property
    @abstractmethod
    def placeable(self):
        raise NotImplementedError
    
    def set_cursor(self):
        self.window.canvas.setCursor(self.cursor)

    # Interface

    @abstractmethod
    def addToConsole(self):
        raise NotImplementedError

    # Serialization
    def __getstate__(self):
        state = self.__dict__.copy()
        del state["window"]
        del state["property_manager"]
        return state
    
    def set_unserializable_attributes(self, window):
        self.window = window
        self.property_manager = PropertiesManager(self, self.window.canvas)
        self.create_property_manager()
        self.set_style()

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
        inverse_color = self._invert(self.color)
        self.property_manager.setStyleSheet(f"background-color: {QColor(*self.color).name()}; color: {QColor(*inverse_color).name()}")

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
        elif shape_type == "circle":
            painter.drawEllipse(pos, 0.5*scale, 0.5*scale)
        elif shape_type == "half circle":
            rectangle = QRectF(pos.x() - 0.75*scale, pos.y() - 0.5*scale, scale, scale)
            start_angle = -90 * 16 # in 16ths of a degree
            span_angle = 180 * 16
            painter.drawPie(rectangle, start_angle, span_angle)
        elif shape_type == "X":
            painter.drawLine(bottom_left, top_right)
            painter.drawLine(top_left, bottom_right)
            painter.drawEllipse(pos, 0.25*scale, 0.25*scale)
        elif shape_type == "diagonal line":
            painter.drawLine(bottom_left, top_right)
            painter.drawEllipse(pos, 0.25*scale, 0.25*scale)
        elif shape_type == "arrow":
            painter.drawLine(bottom_left, pos)
            painter.drawLine(top_left, pos)

    # Transformations

    def snap(self):
        self.position = self.window.canvas.grid.snap(self.position)
        if hasattr(self, "end_position"):
            self.end_position = self.window.canvas.grid.snap(self.end_position)

    def delete(self):
        self.property_manager.hide()
        if self in self.window.canvas.placed_components["wires"]:
            self.window.canvas.placed_components["wires"].remove(self)
            # delete components attached to the wire
            for comp_list in self.window.canvas.placed_components.values():
                for comp in comp_list[:]:
                    comp.snap()
                    self.snap()
                    if comp.position[1] == self.position[1]:
                        comp.delete()
        elif self in self.window.canvas.placed_components["components"]:
            self.window.canvas.placed_components["components"].remove(self)
        elif self in self.window.canvas.placed_components["detectors"]:
            self.window.canvas.placed_components["detectors"].remove(self)

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

    def set_selected(self, check):
        if check:
            self.is_selected = True
            self.window.control_panel.components_tab.select_item(self)
        else:
            self.is_selected = False
            self.window.control_panel.components_tab.deselect_item(self)
        self.set_style()

    def contains(self, pos):
        scale = self.shape_scale*self.window.canvas.grid.size
        if self.position:
            x_min = self.position[0] - 0.5*scale
            x_max = self.position[0] + 0.5*scale
            y_min = self.position[1] - 0.5*scale
            y_max = self.position[1] + 0.5*scale
            if x_min <= pos[0] <= x_max and y_min <= pos[1] <= y_max:
                return True
            
        if hasattr(self, "end_position"):
            if self.end_position and not isinstance(self, Wire):
                x_min = self.end_position[0] - 0.5*scale
                x_max = self.end_position[0] + 0.5*scale
                y_min = self.end_position[1] - 0.5*scale
                y_max = self.end_position[1] + 0.5*scale
                if x_min <= pos[0] <= x_max and y_min <= pos[1] <= y_max:
                    return True
        return False        

    # Placeable checks

    @property
    def connected_wires(self):
        comp_wires = []
        self.snap()
        for w, wire in enumerate(self.window.canvas.placed_components["wires"]):
            wire.snap()
            if self.position[1] == wire.position[1]:
                if wire.position[0] <= self.position[0] <= wire.end_position[0]:
                    comp_wires.append(w+1)
            if hasattr(self, "end_position"):
                if self.end_position[1] == wire.end_position[1]:
                    if wire.position[0] <= self.end_position[0] <= wire.end_position[0]:
                        comp_wires.append(w+1)
        return comp_wires

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

    def place(self):
        # hide the component underneath where this component is placed
        for comp_list in self.window.canvas.placed_components.values():
            for comp in comp_list:
                if issubclass(comp.__class__, DoubleComponent):
                    if self.snappedPosition == self.window.canvas.grid.snap(comp.position):
                        comp.hide_start = True
                    if self.snappedPosition == self.window.canvas.grid.snap(comp.end_position):
                        comp.hide_end = True
                elif issubclass(comp.__class__, SingleComponent):
                    if self.snappedPosition == self.window.canvas.grid.snap(comp.position):
                        comp.hide = True

        self.position = copy(self.snappedPosition)
        self.window.canvas.active_tool = self.__class__(self.window)
        if isinstance(self, Detector):
            self.window.canvas.placed_components["detectors"].append(self)
        else:
            self.window.canvas.placed_components["components"].append(self)
        self.window.canvas.sort_components()

        self.window.console.refresh()
        self.window.control_panel.components_tab.refresh()
        self.window.mark_unsaved_changes()

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

    def draw(self, painter):
        if self.position and not self.hide:
            pen = QPen(QColor(*self.border_color))
            pen.setWidth(self.line_width)
            painter.setPen(pen)
            painter.setBrush(QColor(*self.color))
            self.draw_shape(painter, self.position, self.shape_type)

            self.draw_name(painter, self.position)

            if not (self.is_selected and self.property_manager.properties):
                self.property_manager.hide()

class Detector(SingleComponent):
    def __init__(self, window):
        super().__init__(window)

        self.shape_type = "half circle"
        self.shape_scale = 0.75

        # Properties
        self.herald = 0
        self.create_property_manager()

    def create_property_manager(self):
        self.property_manager.add_property("herald", self.update_herald, self.herald, QIntValidator(0, 100))

    def update_herald(self):
        self.herald = int(self.property_manager.properties["herald"].text())
    
    @property
    def placeable(self):
        # Can only be placed on top of a wire end
        for comp in self.window.canvas.placed_components["wires"]:
            allowed_point = self.window.canvas.grid.snap(comp.end_position)
            if self.snappedPosition == allowed_point:
                return True
        return False
    
    def addToConsole(self):
        raise NotImplementedError

class Loss(SingleComponent):
    def __init__(self, window):
        super().__init__(window)

        # Style
        self.shape_scale = 0.5
        self.shape_type = "diagonal line"

        # Properties
        self.eta = 1
        self.create_property_manager()

    def create_property_manager(self):
        self.property_manager.add_property("eta", self.update_eta, self.eta, QDoubleValidator(0, 1, 2))

    def update_eta(self):
        self.eta = float(self.property_manager.properties["eta"].text())
    
    @property
    def placeable(self):
        if self.overlaps_a_component(self.snappedPosition):
            return False
        if self.overlaps_a_wire(self.snappedPosition):
            return True
        
    def addToConsole(self):
        if self.eta == 1:
            self.window.console.code += "add loss on wire"+str(self.connected_wires[0])+"\n"
        else:
            self.window.console.code += "add loss on wire"+str(self.connected_wires[0])+"with eta"+str(self.eta)+"\n"

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

            self.window.console.refresh()
            self.window.control_panel.components_tab.refresh()

            self.window.mark_unsaved_changes()
    
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

            if not (self.is_selected and self.property_manager.properties):
                self.property_manager.hide()

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

        # Properties
        self.n_photons = 0
        self.create_property_manager()

    def create_property_manager(self):
        self.property_manager.add_property("n_photons", self.update_n_photons, self.n_photons, QIntValidator(0, 100))

    def update_n_photons(self):
        self.n_photons = int(self.property_manager.properties["n_photons"].text())

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
    
    def addToConsole(self):
        pass
    
class BeamSplitter(DoubleComponent):
    def __init__(self, window):
        super().__init__(window)

        # Style
        self.shape_scale = 0.5
        self.shape_type = "circle"
        self.end_shape_type = "circle"

        # Properties
        self.theta = 90
        self.create_property_manager()

    def create_property_manager(self):
        self.property_manager.add_property("angle", self.update_theta, self.theta, QDoubleValidator(0, 180, 2))

    def update_theta(self):
        self.theta = float(self.property_manager.properties["angle"].text())

    @property
    def placeable(self):
        if self.overlaps_a_component(self.snappedPosition):
            return False
        if self.overlaps_itself(self.snappedPosition):
            return False
        if self.spans_a_component(self.snappedPosition):
            return False
        if self.overlaps_a_wire(self.snappedPosition):
            return True
        return False
    
    def addToConsole(self):
        if self.theta == 90:
            self.window.console.code += "add beamsplitter on wires"+str(self.connected_wires)+"\n"
        else:
            self.window.console.code += "add beamsplitter on wires"+str(self.connected_wires)+"with theta"+str(self.theta)+"\n"
    
class Switch(DoubleComponent):
    def __init__(self, window):
        super().__init__(window)

        # Style
        self.shape_scale = 0.5
        self.shape_type = "X"
        self.end_shape_type = "X"

    def create_property_manager(self):
        pass

    @property
    def placeable(self):
        if self.overlaps_a_component(self.snappedPosition):
            return False
        if self.overlaps_itself(self.snappedPosition):
            return False
        if self.spans_a_component(self.snappedPosition):
            return False
        if self.overlaps_a_wire(self.snappedPosition):
            return True
        return False
    
    def addToConsole(self):
        self.window.console.code += "add switch on wires"+str(self.connected_wires)+"\n"