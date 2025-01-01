from PySide6.QtCore import Qt, QPointF, QRectF
from PySide6.QtGui import QColor, QPen, QIntValidator, QDoubleValidator
from copy import copy
from abc import ABC, abstractmethod
from properties_manager import PropertiesManager

class Component(ABC):
    def __init__(self, window):
        self.window = window
        self._position = []
        self.cursor_type = Qt.CrossCursor
        self.is_selected = False

        # Property manager
        self.property_manager = PropertiesManager(self, self.window.canvas)

        # Default style
        self.color = None
        self.border_color = None
        self.line_width = 3
        self.shape_scale = 1
        self.shape_type = ["square"]
        self.error_color = (255, 0, 0)
        self.set_style()

    # Setup

    @property
    def position(self):
        if len(self._position) != self.length:
            self._position = [None] * self.length
        return self._position
    
    @position.setter
    def position(self, value):
        if len(value) != self.length:
            raise ValueError(f"Position must have {self.length} elements.")
        self._position = value

    @property
    @abstractmethod
    def length(self):
        pass

    @abstractmethod
    def create_property_manager(self):
        raise NotImplementedError

    @property
    @abstractmethod
    def placeable(self):
        raise NotImplementedError

    def place(self):
        for i, pos in enumerate(self.position):
            # Place the earliest unplaced node
            if not pos:
                self.position[i] = copy(self.potential_placement)

                # If all nodes are placed, log the component
                if i == len(self.position) - 1:
                    self.log()

                break

    def log(self):
        self.window.canvas.active_tool = self.__class__(self.window)
        if isinstance(self, Wire):
            self.window.canvas.placed_components["wires"].append(self)
        elif isinstance(self, Detector):
            self.window.canvas.placed_components["detectors"].append(self)
        else:
            self.window.canvas.placed_components["components"].append(self)

        self.window.canvas.sort_components()
        self.window.console.refresh()
        self.window.control_panel.components_tab.refresh()

        self.window.mark_unsaved_changes()

    def draw(self, painter):
        for i, pos in enumerate(self.position):
            if pos:
                # draw connecting wire
                if i != 0:
                    pen = QPen(QColor(*self.border_color))
                    pen.setWidth(self.line_width)
                    painter.setPen(pen)
                    previous_pos = self.position[i-1]
                    painter.drawLine(QPointF(previous_pos[0], previous_pos[1]), QPointF(pos[0], pos[1]))

                # draw node
                pen = QPen(QColor(*self.border_color))
                pen.setWidth(self.line_width)
                painter.setPen(pen)
                painter.setBrush(QColor(*self.color))
                self.draw_shape(painter, pos, self.shape_type[i])
        self.draw_name(painter, self.position[0])

    def preview(self, painter):
        for i, pos in enumerate(self.position):
            if pos:
                pen = QPen(QColor(*self.border_color))
                pen.setWidth(self.line_width)
                painter.setPen(pen)

                # draw node
                painter.setBrush(QColor(*self.color))
                self.draw_shape(painter, pos, self.shape_type[i])
            else:
                pen = QPen(self._transparent(QColor(*self.border_color)))
                pen.setWidth(self.line_width)
                painter.setPen(pen)
                if self.placeable:
                    painter.setBrush(self._transparent(QColor(*self.color)))
                else:
                    painter.setBrush(self._transparent(QColor(*self.error_color)))
                self.draw_shape(painter, self.potential_placement, self.shape_type[i])

                # draw wire
                if i != 0:
                    previous_pos = self.position[i-1]
                    painter.drawLine(QPointF(previous_pos[0], previous_pos[1]), QPointF(self.potential_placement[0], self.potential_placement[1]))
                break

    # Interface

    @abstractmethod
    def add_to_console(self):
        raise NotImplementedError
    
    def add_to_sim(self):
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
    def potential_placement(self):
        self.snap()
        snapped_mouse_position = self.window.canvas.grid.snap(self.window.canvas.current_mouse_position)
        if len(self.position) == 1:
            if not self.position[0]:
                return snapped_mouse_position
        if len(self.position) > 1:
            if self.position[0]:
                start_position = self.position[0]
                if isinstance(self, Wire):
                    # enforce wire being horizontal
                    x = snapped_mouse_position[0]
                    y = start_position[1]
                    return (x, y)
                # enforce components being vertical
                x = start_position[0]
                y = snapped_mouse_position[1]
                return (x, y)
        return snapped_mouse_position
            
    def set_style(self):
        if self.window.canvas.style_choice == "basic":
            self.color = (0, 0, 0)
            if not self.is_selected:
                self.border_color = (0, 0, 0)
            else:
                self.border_color = (219, 197, 119)
                # self.border_color = (0, 128, 255)
        elif self.window.canvas.style_choice == "darkmode":
            self.color = (255, 255, 255)
            if not self.is_selected:
                self.border_color = (255, 255, 255)
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
        self.position = [self.window.canvas.grid.snap(pos) if pos else None for pos in self.position]

    def delete(self):
        self.property_manager.hide()
        if self in self.window.canvas.placed_components["wires"]:
            self.window.canvas.placed_components["wires"].remove(self)

            # delete components attached to the wire
            for comp_list in self.window.canvas.placed_components.values():
                for comp in comp_list[:]:
                    comp.snap()
                    self.snap()
                    if len(comp.position) > 0:
                        if comp.position[0][1] == self.position[0][1] and (self.position[0][0] <= comp.position[0][0] <= self.position[1][0]):
                            comp_list.remove(comp)
                    if len(comp.position) > 1:
                        if comp.position[1][1] == self.position[0][1] and (self.position[0][0] <= comp.position[1][0] <= self.position[1][0]):
                            comp_list.remove(comp)

        elif self in self.window.canvas.placed_components["components"]:
            self.window.canvas.placed_components["components"].remove(self)
        elif self in self.window.canvas.placed_components["detectors"]:
            self.window.canvas.placed_components["detectors"].remove(self)

    def move(self, delta):
        self.position = [self._move_node(pos, delta) for pos in self.position]

    def _move_node(self, node, delta):
        if not node:
            return None
        return (node[0] + delta[0], node[1] + delta[1])

    def zoom(self, mouse_pos, new_grid_size):
        self.position = [self._zoom_node(pos, mouse_pos, new_grid_size) for pos in self.position]

    def _zoom_node(self, node, mouse_pos, new_grid_size):
        if not node:
            return None
        distance_to_mouse = (node[0] - mouse_pos[0], node[1] - mouse_pos[1])
        new_distance_to_mouse = (distance_to_mouse[0] * (new_grid_size / self.window.canvas.grid.size), distance_to_mouse[1] * (new_grid_size / self.window.canvas.grid.size))
        return (mouse_pos[0] + new_distance_to_mouse[0], mouse_pos[1] + new_distance_to_mouse[1])

    # Selecting

    def set_selected(self, check):
        if check:
            self.is_selected = True
            self.window.control_panel.components_tab.select_item(self)
        else:
            self.is_selected = False
            self.window.control_panel.components_tab.deselect_item(self)
        self.set_style()

    def contains(self, position_to_check):
        return any([self._node_contains(pos, position_to_check) for pos in self.position])    

    def _node_contains(self, node, position_to_check):
        if not node:
            return False
        scale = self.shape_scale*self.window.canvas.grid.size
        x_min = node[0] - 0.5*scale
        x_max = node[0] + 0.5*scale
        y_min = node[1] - 0.5*scale
        y_max = node[1] + 0.5*scale
        if x_min <= position_to_check[0] <= x_max and y_min <= position_to_check[1] <= y_max:
            return True

    # Placeable checks

    @property
    def connected_wires(self):
        comp_wires = []
        self.snap()
        for w, wire in enumerate(self.window.canvas.placed_components["wires"]):
            wire.snap()
            wire_y = wire.position[0][1]
            wire_x_start = wire.position[0][0]
            wire_x_end = wire.position[1][0]
            for pos in self.position:
                if pos:
                    if pos[1] == wire_y:
                        if wire_x_start <= pos[0] <= wire_x_end:
                            comp_wires.append(w+1)
        return comp_wires

    def overlaps_a_wire(self, position_to_check):
        for wire in self.window.canvas.placed_components["wires"]:
            wire.snap()
            wire_x_start = wire.position[0][0]
            wire_x_end = wire.position[1][0]
            wire_y = wire.position[0][1]
            if position_to_check[1] == wire_y:
                if wire_x_start < position_to_check[0] < wire_x_end:
                    return True
        return False
    
    def overlaps_a_wire_edge(self, position_to_check):
        for wire in self.window.canvas.placed_components["wires"]:
            wire.snap()
            wire_x_start = wire.position[0][0]
            wire_x_end = wire.position[1][0]
            wire_y = wire.position[0][1]
            if position_to_check[1] == wire_y:
                if wire_x_start == position_to_check[0] or wire_x_end == position_to_check[0]:
                    return True
        return False
    
    def overlaps_a_component(self, position_to_check):
        for comp in self.window.canvas.placed_components["components"]:
            comp.snap()
            if len(self.position) == 2:
                comp_start = comp.position[0]
                comp_end = comp.position[1]
                if position_to_check[0] == comp_start[0]:
                    if min(comp_start[1], comp_end[1]) <= position_to_check[1] <= max(comp_start[1], comp_end[1]):
                        return True
            elif len(self.position) == 1:
                if position_to_check == comp.position[0]:
                    return True
        return False
    
    def overlaps_itself(self, position_to_check):
        self.snap()
        return any([position_to_check == pos for pos in self.position])
    
    def spans_a_component(self, pos):
        if len(self.position) > 0:
            if self.position[0]:
                for comp_list in self.window.canvas.placed_components.values():
                    for comp in comp_list:
                        comp.snap()
                        comp_start = comp.position[0]
                        if self.position[0][0] == comp_start[0]:
                            if len(self.position) > 1:
                                comp_end = comp.position[1]
                                if self.position[0][1] <= comp_start[1] and pos[1] >= comp_end[1]:
                                    return True
                                if self.position[0][1] <= comp_end[1] and pos[1] >= comp_start[1]:
                                    return True
                                if self.position[0][1] >= comp_start[1] and pos[1] <= comp_end[1]:
                                    return True
                                if self.position[0][1] >= comp_end[1] and pos[1] <= comp_start[1]:
                                    return True
                            else:
                                if self.position[0][1] <= comp_start[1] and pos[1] >= comp_start[1]:
                                    return True
                                if pos[1] <= comp_start[1] and self.position[0][1] >= comp_start[1]:
                                    return True
        return False
    
    def spans_a_wire(self, pos):
        if len(self.position) > 0:
            if self.position[0]:
                # Can't be on the opposite side of a wire from the start point
                for comp in self.window.canvas.placed_components["wires"]:
                    comp.snap()
                    comp_start = comp.position[0]
                    comp_end = comp.position[1]
                    if self.position[0][1] == comp_start[1]:
                        if self.position[0][0] <= comp_start[0] and pos[0] >= comp_end[0]:
                            return True
                        if self.position[0][0] >= comp_end[0] and pos[0] <= comp_start[0]:
                            return True
        return False

class Detector(Component):
    def __init__(self, window):
        super().__init__(window)

        self.shape_type = ["half circle"]
        self.shape_scale = 0.75

        # Properties
        self.herald = 0
        self.create_property_manager()

    @property
    def length(self):
        return 1

    def create_property_manager(self):
        self.property_manager.add_property("herald", self.update_herald, self.herald, QIntValidator(0, 100))

    def update_herald(self):
        self.herald = int(self.property_manager.properties["herald"].text())
        self.window.console.refresh()
    
    @property
    def placeable(self):
        # Can only be placed on top of a wire end
        for wire in self.window.canvas.placed_components["wires"]:
            wire.snap()
            allowed_point = wire.position[1]
            if self.potential_placement == allowed_point:
                return True
        return False
    
    def add_to_console(self):
        pass
    
    def add_to_sim(self):
        pass

class Loss(Component):
    def __init__(self, window):
        super().__init__(window)

        # Style
        self.shape_scale = 0.5
        self.shape_type = ["diagonal line"]

        # Properties
        self.eta = 1
        self.create_property_manager()

    @property
    def length(self):
        return 1

    def create_property_manager(self):
        self.property_manager.add_property("eta", self.update_eta, self.eta, QDoubleValidator(0, 1, 2))

    def update_eta(self):
        self.eta = float(self.property_manager.properties["eta"].text())
        self.window.console.refresh()
    
    @property
    def placeable(self):
        if self.overlaps_a_component(self.potential_placement):
            return False
        if self.overlaps_a_wire(self.potential_placement):
            return True
        
    def add_to_console(self):
        if self.eta == 1:
            self.window.console.code += "add loss on wire"+str(self.connected_wires[0])+"\n"
        else:
            self.window.console.code += "add loss on wire"+str(self.connected_wires[0])+"with eta"+str(self.eta)+"\n"

    def add_to_sim(self):
        print("adding loss (placeholder code)")

class Wire(Component):
    def __init__(self, window):
        super().__init__(window)

        # Style
        self.shape_scale = 0.75
        self.shape_type = ["square", None]

        # Properties
        self.n_photons = 0
        self.create_property_manager()

    @property
    def length(self):
        return 2

    def create_property_manager(self):
        self.property_manager.add_property("n_photons", self.update_n_photons, self.n_photons, QIntValidator(0, 100))

    def update_n_photons(self):
        self.n_photons = int(self.property_manager.properties["n_photons"].text())
        self.window.control_panel.gram_matrix_tab.update_gram_matrix()
        self.window.console.refresh()

    @property
    def placeable(self):
        if self.overlaps_a_wire(self.potential_placement):
            return False
        if self.overlaps_a_wire_edge(self.potential_placement):
            return False
        if self.overlaps_a_component(self.potential_placement):
            return False
        
        # Rules for the start point
        if not self.position[0]:
            # Can't place it on the point immediately to the left of another wire, which would leave no room for the end point
            for wire in self.window.canvas.placed_components["wires"]:
                wire.snap()
                wire_start = wire.position[0]
                if self.potential_placement[1] == wire_start[1]:
                    if self.window.canvas.grid.snap((self.potential_placement[0] + self.window.canvas.grid.size, self.potential_placement[1])) == wire_start:
                        return False
        
        # Rules for the end point
        if self.position[0] and not self.position[1]:
            # The end point must be to the right of the start point
            if self.potential_placement[0] <= self.window.canvas.grid.snap(self.position[0])[0]:
                return False
            
        if self.spans_a_wire(self.potential_placement):
            return False
        return True
    
    def add_to_console(self):
        pass

    def add_to_sim(self):
        pass
    
class BeamSplitter(Component):
    def __init__(self, window):
        super().__init__(window)

        # Style
        self.shape_scale = 0.5
        self.shape_type = ["circle", "circle"]

        # Properties
        self.theta = 90
        self.create_property_manager()

    @property
    def length(self):
        return 2

    def create_property_manager(self):
        self.property_manager.add_property("angle", self.update_theta, self.theta, QDoubleValidator(0, 180, 2))

    def update_theta(self):
        self.theta = float(self.property_manager.properties["angle"].text())
        self.window.console.refresh()

    @property
    def placeable(self):
        if self.overlaps_a_component(self.potential_placement):
            return False
        if self.overlaps_itself(self.potential_placement):
            return False
        if self.spans_a_component(self.potential_placement):
            return False
        if self.overlaps_a_wire(self.potential_placement):
            return True
        return False
    
    def add_to_console(self):
        if self.theta == 90:
            self.window.console.code += "add beamsplitter on wires"+str(self.connected_wires)+"\n"
        else:
            self.window.console.code += "add beamsplitter on wires"+str(self.connected_wires)+"with theta"+str(self.theta)+"\n"
    
    def add_to_sim(self):
        print("add beamsplitter (placeholder code)")

class Switch(Component):
    def __init__(self, window):
        super().__init__(window)

        # Style
        self.shape_scale = 0.5
        self.shape_type = ["X", "X"]

    @property
    def length(self):
        return 2

    def create_property_manager(self):
        pass

    @property
    def placeable(self):
        if self.overlaps_a_component(self.potential_placement):
            return False
        if self.overlaps_itself(self.potential_placement):
            return False
        if self.spans_a_component(self.potential_placement):
            return False
        if self.overlaps_a_wire(self.potential_placement):
            return True
        return False
    
    def add_to_console(self):
        self.window.console.code += "add switch on wires"+str(self.connected_wires)+"\n"

    def add_to_sim(self):
        print("adding switch (placeholder code)")