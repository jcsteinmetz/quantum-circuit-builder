from PySide6.QtCore import Qt, QPointF, QRectF
from PySide6.QtGui import QColor, QPen, QIntValidator, QDoubleValidator
from copy import copy
from abc import ABC, abstractmethod
from properties_manager import PropertiesManager

class ComponentRenderer:
    def __init__(self, window):
        self.window = window

        # Default style
        self.color = None
        self.border_color = None
        self.selected_border_color = None
        self.error_color = None

        self.line_width = 3
        self.shape_type = ["square"]

        # Style
        self.set_style()

    def set_style(self):
        # Component style
        self.color = self.window.style_manager.get_style("color")
        self.border_color = self.window.style_manager.get_style("border_color")
        self.selected_border_color = self.window.style_manager.get_style("selected_border_color")
        self.error_color = self.window.style_manager.get_style("error_color")

    # Colors

    def _transparent(self, col):
        return (col[0], col[1], col[2], 128)
    
    def _invert(self, col):
        return (255-col[0], 255-col[1], 255-col[2])

    def set_painter_style(self, painter, pen_color = None, brush_color = None):
        if not pen_color:
            pen_color = self.border_color
        if not brush_color:
            brush_color = self.color

        pen = QPen(QColor(*pen_color))
        pen.setWidth(self.line_width)
        painter.setPen(pen)

        painter.setBrush(QColor(*brush_color))

    def draw_name(self, painter, comp):
        name_position = comp.node_positions[0]
        self.set_painter_style(painter, pen_color = self._invert(self.color))
        scale = comp.shape_scale * self.window.canvas.grid.size
        rectangle = QRectF(name_position[0] - 0.5*scale, name_position[1] - 0.5*scale, scale, scale)
        painter.drawText(rectangle, Qt.AlignCenter, comp.name)

    def draw_property_manager(self, comp):

        # Property manager style
        inverse_color = self._invert(self.window.canvas.bg_color)
        comp.property_manager.setStyleSheet(f"background-color: {QColor(*inverse_color).name()}; color: {QColor(*self.window.canvas.bg_color).name()}")

        comp.property_manager.move(int(comp.node_positions[0][0] + comp.property_manager.offset[0]), int(comp.node_positions[0][1]+comp.property_manager.offset[1]))
        if not comp.property_manager.isVisible():
            comp.property_manager.show()

    def draw_square(self, painter, pos, scale):
        bottom_left = QPointF(pos.x() - 0.5*scale, pos.y() - 0.5*scale)
        painter.drawRect(bottom_left.x(), bottom_left.y(), scale, scale)

    def draw_ellipse(self, painter, pos, scale):
        painter.drawEllipse(pos, 0.5*scale, 0.5*scale)

    def draw_half_circle(self, painter, pos, scale):
        rectangle = QRectF(pos.x() - 0.75*scale, pos.y() - 0.5*scale, scale, scale)
        start_angle = -90 * 16 # in 16ths of a degree
        span_angle = 180 * 16
        painter.drawPie(rectangle, start_angle, span_angle)

    def draw_X(self, painter, pos, scale):
        bottom_left = QPointF(pos.x() - 0.5*scale, pos.y() - 0.5*scale)
        top_left = QPointF(pos.x() - 0.5*scale, pos.y() + 0.5*scale)
        bottom_right = QPointF(pos.x() + 0.5*scale, pos.y() - 0.5*scale)
        top_right = QPointF(pos.x() + 0.5*scale, pos.y() + 0.5*scale)

        painter.drawLine(bottom_left, top_right)
        painter.drawLine(top_left, bottom_right)
        painter.drawEllipse(pos, 0.25*scale, 0.25*scale)
    
    def draw_diagonal_line(self, painter, pos, scale):
        bottom_left = QPointF(pos.x() - 0.5*scale, pos.y() - 0.5*scale)
        top_right = QPointF(pos.x() + 0.5*scale, pos.y() + 0.5*scale)
        painter.drawLine(bottom_left, top_right)
        painter.drawEllipse(pos, 0.25*scale, 0.25*scale)

    def draw_arrow(self, painter, pos, scale):
        bottom_left = QPointF(pos.x() - 0.5*scale, pos.y() - 0.5*scale)
        top_left = QPointF(pos.x() - 0.5*scale, pos.y() + 0.5*scale)

        painter.drawLine(bottom_left, pos)
        painter.drawLine(top_left, pos)

    def draw_shape(self, painter, comp, pos, shape_type):
        scale = comp.shape_scale * self.window.canvas.grid.size

        pos = QPointF(pos[0], pos[1])

        shape_methods = {
            "square": self.draw_square,
            "circle": self.draw_ellipse,
            "half circle": self.draw_half_circle,
            "X": self.draw_X,
            "diagonal line": self.draw_diagonal_line,
            "arrow": self.draw_arrow,
        }

        draw_method = shape_methods.get(shape_type)
        
        if draw_method:
            draw_method(painter, pos, scale)

    def draw_wire(self, painter, comp, start_position, end_position):
        if comp.is_selected:
            self.set_painter_style(painter, pen_color = self.selected_border_color)
        else:
            self.set_painter_style(painter)
        painter.drawLine(QPointF(start_position[0], start_position[1]), QPointF(end_position[0], end_position[1]))

    def draw_node(self, painter, comp, position, shape_type):
        if comp.is_selected:
            self.set_painter_style(painter, pen_color = self.selected_border_color)
        else:
            self.set_painter_style(painter)
        self.draw_shape(painter, comp, position, shape_type)

    def draw(self, painter, comp):
        # draw in reverse order so that wires are underneath nodes
        for j, pos in enumerate(reversed(comp.node_positions)):
            i = len(comp.node_positions) - 1 - j
            if pos:
                if i != 0:
                    self.draw_wire(painter, comp, comp.node_positions[i-1], pos)
                self.draw_node(painter, comp, pos, comp.shape_type[i])
        self.draw_name(painter, comp)

        if comp.is_selected:
            self.draw_property_manager(comp)

    def preview(self, painter, comp):
        for i, pos in enumerate(comp.node_positions):
            if pos:
                # draw node
                self.set_painter_style(painter)
                self.draw_shape(painter, comp, pos, comp.shape_type[i])
            else:
                if comp.placeable:
                    self.set_painter_style(painter, pen_color = self._transparent(self.border_color), brush_color = self._transparent(self.color))
                else:
                    self.set_painter_style(painter, pen_color = self._transparent(self.border_color), brush_color = self._transparent(self.error_color))
                self.draw_shape(painter, comp, comp.potential_placement, comp.shape_type[i])

                # draw wire
                if i != 0:
                    previous_pos = comp.node_positions[i-1]
                    painter.drawLine(QPointF(previous_pos[0], previous_pos[1]), QPointF(comp.potential_placement[0], comp.potential_placement[1]))
                break

class Component(ABC):
    def __init__(self, window):
        self.window = window
        self._node_positions = []
        self.cursor_type = Qt.CrossCursor
        self.is_selected = False
        self.direction = None
        self.shape_scale = 1

        # Property manager
        self.property_manager = PropertiesManager(self, self.window.canvas)

    # Setup

    @property
    def node_positions(self):
        if len(self._node_positions) != self.length:
            self._node_positions = [None] * self.length
        return self._node_positions
    
    @node_positions.setter
    def node_positions(self, value):
        if len(value) != self.length:
            raise ValueError(f"Position must have {self.length} elements.")
        self._node_positions = value

    @property
    @abstractmethod
    def length(self):
        raise NotImplementedError

    @abstractmethod
    def create_property_manager(self):
        raise NotImplementedError

    @property
    @abstractmethod
    def placeable(self):
        raise NotImplementedError

    def place(self):
        for i, pos in enumerate(self.node_positions):

            # Fill in the earliest unplaced node
            if not pos:
                self.node_positions[i] = copy(self.potential_placement)

                # If that was the last node, log the component
                if i == len(self.node_positions) - 1:
                    self.window.canvas.place(self)

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
    
    # Drawing

    @property
    def potential_placement(self):
        self.snap()
        snapped_mouse_position = self.window.canvas.grid.snap(self.window.canvas.current_mouse_position)
        if len(self.node_positions) == 1:
            if not self.node_positions[0]:
                return snapped_mouse_position
        if len(self.node_positions) > 1:
            if self.node_positions[0]:
                start_position = self.node_positions[0]
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

    @property
    def name(self):
        all_components = self.window.canvas.placed_components["wires"] + self.window.canvas.placed_components["components"] + self.window.canvas.placed_components["detectors"]
        overall_index = all_components.index(self)
        type_index = sum(isinstance(i, self.__class__) for i in all_components[:overall_index])
        child_name = type(self).__name__[0] + str(type_index+1)
        return child_name

    # Transformations

    def snap(self):
        self.node_positions = [self.window.canvas.grid.snap(pos) if pos else None for pos in self.node_positions]

    def delete(self):
        self.property_manager.hide()
        if self in self.window.canvas.placed_components["wires"]:
            self.window.canvas.placed_components["wires"].remove(self)

            # delete components attached to the wire
            for comp in self.window.canvas.all_placed_components():
                comp.snap()
                self.snap()
                if len(comp.node_positions) > 0:
                    if comp.node_positions[0][1] == self.node_positions[0][1] and (self.node_positions[0][0] <= comp.node_positions[0][0] <= self.node_positions[1][0]):
                        comp.delete()
                if len(comp.node_positions) > 1:
                    if comp.node_positions[1][1] == self.node_positions[0][1] and (self.node_positions[0][0] <= comp.node_positions[1][0] <= self.node_positions[1][0]):
                        comp.delete()

        elif self in self.window.canvas.placed_components["components"]:
            self.window.canvas.placed_components["components"].remove(self)
        elif self in self.window.canvas.placed_components["detectors"]:
            self.window.canvas.placed_components["detectors"].remove(self)

    def move(self, delta):
        self.node_positions = [self._move_node(pos, delta) for pos in self.node_positions]

    def _move_node(self, node, delta):
        if not node:
            return None
        return (node[0] + delta[0], node[1] + delta[1])

    def zoom(self, mouse_pos, new_grid_size):
        self.node_positions = [self._zoom_node(pos, mouse_pos, new_grid_size) for pos in self.node_positions]

    def _zoom_node(self, node, mouse_pos, new_grid_size):
        if not node:
            return None
        distance_to_mouse = (node[0] - mouse_pos[0], node[1] - mouse_pos[1])
        new_distance_to_mouse = (distance_to_mouse[0] * (new_grid_size / self.window.canvas.grid.size), distance_to_mouse[1] * (new_grid_size / self.window.canvas.grid.size))
        return (mouse_pos[0] + new_distance_to_mouse[0], mouse_pos[1] + new_distance_to_mouse[1])

    # Selecting

    def set_selected(self, check):
        self.is_selected = check
        if check:
            self.select_item_in_ui()
        else:
            self.deselect_item_in_ui()

    def select_item_in_ui(self):
        self.window.control_panel.components_tab.select_item(self)

    def deselect_item_in_ui(self):
        self.window.control_panel.components_tab.deselect_item(self)
        self.property_manager.hide()

    def contains(self, position_to_check):
        return any([self._node_contains(pos, position_to_check) for pos in self.node_positions])    

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
        wires_connected_to_component = []
        self.snap()
        for w, wire in enumerate(self.window.canvas.placed_components["wires"]):
            wire.snap()
            wire_y = wire.node_positions[0][1]
            wire_x_start = wire.node_positions[0][0]
            wire_x_end = wire.node_positions[1][0]
            for pos in self.node_positions:
                if pos:
                    if pos[1] == wire_y:
                        if wire_x_start <= pos[0] <= wire_x_end:
                            wires_connected_to_component.append(w+1)
        return wires_connected_to_component
    
    def overlaps_a_wire_edge(self, position_to_check):
        for wire in self.window.canvas.placed_components["wires"]:
            wire.snap()
            wire_x_start = wire.node_positions[0][0]
            wire_x_end = wire.node_positions[1][0]
            wire_y = wire.node_positions[0][1]
            if position_to_check[1] == wire_y:
                if wire_x_start == position_to_check[0] or wire_x_end == position_to_check[0]:
                    return True
        return False
    
    def _check_overlap(self, position_to_check, component_group):
        for comp in self.window.canvas.placed_components[component_group]:
            comp.snap()
            if comp.direction == "H":
                on_axis = position_to_check[1] == comp.node_positions[0][1]
                comp_range = [pos[0] for pos in comp.node_positions]
                in_range = min(comp_range) < position_to_check[0] < max(comp_range)
            else:
                on_axis = position_to_check[0] == comp.node_positions[0][0]
                comp_range = [pos[1] for pos in comp.node_positions]
                in_range = min(comp_range) <= position_to_check[1] <= max(comp_range)
            if on_axis and in_range:
                return True
        return False
    
    def overlaps_a_wire(self, position_to_check):
        self.snap()
        return self._check_overlap(position_to_check, "wires")
    
    def overlaps_a_component(self, position_to_check):
        self.snap()
        return self._check_overlap(position_to_check, "components")
    
    def overlaps_itself(self, position_to_check):
        self.snap()
        return any([position_to_check == pos for pos in self.node_positions])
    
    def spans_a_component(self, position_to_check):
        if len(self.node_positions) > 0:
            if self.node_positions[0]:
                for comp in self.window.canvas.all_placed_components():
                    comp.snap()
                    comp_range = [pos[1] for pos in comp.node_positions]
                    if self.node_positions[0][0] == comp.node_positions[0][0]:
                        if self.node_positions[0][1] <= min(comp_range) and position_to_check[1] >= max(comp_range):
                            return True
                        if self.node_positions[0][1] >= max(comp_range) and position_to_check[1] <= min(comp_range):
                            return True
        return False
    
    def spans_a_wire(self, pos):
        if len(self.node_positions) > 0:
            if self.node_positions[0]:
                # Can't be on the opposite side of a wire from the start point
                for comp in self.window.canvas.placed_components["wires"]:
                    comp.snap()
                    comp_start = comp.node_positions[0]
                    comp_end = comp.node_positions[1]
                    if self.node_positions[0][1] == comp_start[1]:
                        if self.node_positions[0][0] <= comp_start[0] and pos[0] >= comp_end[0]:
                            return True
                        if self.node_positions[0][0] >= comp_end[0] and pos[0] <= comp_start[0]:
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
            allowed_point = wire.node_positions[1]
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
        self.direction = "H"

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
        if not self.node_positions[0]:
            # Can't place it on the point immediately to the left of another wire, which would leave no room for the end point
            for wire in self.window.canvas.placed_components["wires"]:
                wire.snap()
                wire_start = wire.node_positions[0]
                if self.potential_placement[1] == wire_start[1]:
                    if self.window.canvas.grid.snap((self.potential_placement[0] + self.window.canvas.grid.size, self.potential_placement[1])) == wire_start:
                        return False
        
        # Rules for the end point
        if self.node_positions[0] and not self.node_positions[1]:
            # The end point must be to the right of the start point
            if self.potential_placement[0] <= self.window.canvas.grid.snap(self.node_positions[0])[0]:
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
        self.direction = "V"

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
        self.direction = "V"

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