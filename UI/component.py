from PySide6.QtCore import Qt, QPointF, QRectF
from PySide6.QtGui import QColor, QPen, QIntValidator, QDoubleValidator
from abc import ABC, abstractmethod
from UI.property_box import PropertyBox

class ComponentRenderer:

    SHAPE_METHODS = {
        "square": "draw_square",
        "circle": "draw_ellipse",
        "half circle": "draw_half_circle",
        "X": "draw_X",
        "diagonal line": "draw_diagonal_line",
        "arrow": "draw_arrow",
    }

    def __init__(self, window):
        self.window = window

        # Style
        self.face_color = self.window.style_manager.get_style("face_color")
        self.border_color = self.window.style_manager.get_style("border_color")
        self.selected_border_color = self.window.style_manager.get_style("selected_border_color")
        self.error_color = self.window.style_manager.get_style("error_color")
        self.name_color = self.window.style_manager.get_style("name_color")

        self.line_width = 3
        self.shape_type = ["square"]

    # Colors

    def _transparent(self, col):
        return (col[0], col[1], col[2], 128)
    
    def update_node_styles(self):
        styles = self.window.style_manager.get_node_styles()
        self.face_color = styles["face_color"]
        self.border_color = styles["border_color"]
        self.selected_border_color = styles["selected_border_color"]
        self.error_color = styles["error_color"]
        self.name_color = styles["name_color"]

    def set_painter_style(self, painter, pen_color = None, brush_color = None, transparent = False):
        if not pen_color:
            pen_color = self.border_color
        if not brush_color:
            brush_color = self.face_color

        if transparent:
            pen_color = self._transparent(pen_color)
            brush_color = self._transparent(brush_color)

        pen = QPen(QColor(*pen_color))
        pen.setWidth(self.line_width)
        painter.setPen(pen)

        painter.setBrush(QColor(*brush_color))

    def draw_name(self, painter, comp):
        name_position = comp.node_positions[0]
        self.set_painter_style(painter, pen_color = self.name_color)
        scale = comp.shape_scale * self.window.canvas.grid.size
        rectangle = QRectF(name_position[0] - 0.5*scale, name_position[1] - 0.5*scale, scale, scale)
        painter.drawText(rectangle, Qt.AlignCenter, comp.name)

    def draw_property_box(self, comp):
        comp.property_box.draw()

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

        draw_method_name = self.SHAPE_METHODS.get(shape_type)
        if draw_method_name:
            draw_method = getattr(self, draw_method_name)
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

        if comp.is_selected and comp.is_only_selected_component():
            self.draw_property_box(comp)

    def preview(self, painter, comp):
        for i, pos in enumerate(comp.node_positions):
            if pos:
                # draw node
                self.set_painter_style(painter)
                self.draw_shape(painter, comp, pos, comp.shape_type[i])
            else:
                if comp.placeable:
                    self.set_painter_style(painter, transparent = True)
                else:
                    self.set_painter_style(painter, brush_color = self.error_color, transparent = True)
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
        self.shape_type = []

        # Property manager
        self.property_box = PropertyBox(self, self.window.canvas)

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
    def create_property_box(self):
        raise NotImplementedError

    @property
    @abstractmethod
    def placeable(self):
        raise NotImplementedError
    
    @property
    def connected_wires(self):
        wires_connected_to_component = []
        self.snap()
        for wire in self.window.canvas.placed_components["wires"]:
            if self.is_connected_to_wire(wire):
                wires_connected_to_component.append(wire)
        return wires_connected_to_component
    
    @property
    def connected_components(self):
        components_connected_to_wire = []
        self.snap()
        for comp in self.window.canvas.all_placed_components():
            comp.snap()
            if comp.is_connected_to_wire(self):
                components_connected_to_wire.append(comp)
        return components_connected_to_wire
    
    def is_connected_to_wire(self, wire):
        wire.snap()
        wire_y = wire.node_positions[0][1]
        wire_range = [pos[0] for pos in self.node_positions]
        for pos in self.node_positions:
            on_axis = pos[1] == wire_y
            in_range = min(wire_range) <= pos[0] <= max(wire_range)
            if on_axis and in_range:
                return True
        return False

    def place(self):
        for i, pos in enumerate(self.node_positions):

            # Fill in the earliest unplaced node
            if not pos:
                self.node_positions[i] = self.potential_placement

                # If that was the last node, log the component
                if i == len(self.node_positions) - 1:
                    self.window.canvas.place(self)

                break

    def is_only_selected_component(self):
        selected_components = [comp for comp in self.window.canvas.all_placed_components() if comp.is_selected]
        if len(selected_components) == 1 and selected_components[0] == self:
            return True
        return False

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
        del state["property_box"]
        return state
    
    def set_unserializable_attributes(self, window):
        self.window = window
        self.property_box = PropertyBox(self, self.window.canvas)
        self.create_property_box()
    
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
        self.property_box.hide()
        if self in self.window.canvas.placed_components["wires"]:
            self.window.canvas.placed_components["wires"].remove(self)

            for comp in self.connected_components:
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

    def toggle_selection(self, selected):
        self.is_selected = selected
        self.window.control_panel.components_tab.toggle_selection(self, selected)
        if not selected:
            self.property_box.hide()

    def contains(self, position_to_check):
        for i, pos in enumerate(self.node_positions):
            if self._node_contains(pos, position_to_check) and self.shape_type[i]:
                return True
        return False

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
    
    def overlaps_a_wire_edge(self, position_to_check):
        for wire in self.window.canvas.placed_components["wires"]:
            wire.snap()
            for pos in wire.node_positions:
                if position_to_check == pos:
                    return True
        return False
    
    def _check_overlap(self, position_to_check, component_group):
        for comp in self.window.canvas.placed_components[component_group]:
            comp.snap()
            if comp.direction == "H":
                on_axis = position_to_check[1] == comp.node_positions[0][1]
                comp_range = [pos[0] for pos in comp.node_positions]
                in_range = min(comp_range) <= position_to_check[0] <= max(comp_range)
            else: # case with neither H nor V could be handled by either H or V logic
                on_axis = position_to_check[0] == comp.node_positions[0][0]
                comp_range = [pos[1] for pos in comp.node_positions]
                in_range = min(comp_range) <= position_to_check[1] <= max(comp_range)
            if on_axis and in_range:
                return True
        return False
    
    def overlaps_a_wire(self, position_to_check):
        return self._check_overlap(position_to_check, "wires")
    
    def overlaps_a_component(self, position_to_check):
        return self._check_overlap(position_to_check, "components")
    
    def overlaps_itself(self, position_to_check):
        self.snap()
        return any([position_to_check == pos for pos in self.node_positions])
    
    def spans_a_component(self, position_to_check):
        if len(self.node_positions) > 0:
            if self.node_positions[0]:
                for comp in self.window.canvas.all_placed_components():
                    comp.snap()
                    if self.direction == "H":
                        range_idx = 0
                        axis_idx = 1
                    elif self.direction == "V":
                        range_idx = 1
                        axis_idx = 0
                    
                    comp_range = [pos[range_idx] for pos in comp.node_positions]
                    self_range = [pos[range_idx] for pos in self.node_positions if pos] + [position_to_check[range_idx]]
                    on_axis = self.node_positions[0][axis_idx] == comp.node_positions[0][axis_idx]
                    in_range = min(self_range) <= min(comp_range) and max(comp_range) <= max(self_range)
                    if on_axis and in_range:
                        return True
        return False
    
    def get_wire_index(self, wire_to_find):
        wire_index = None
        for w, wire in enumerate(self.window.canvas.placed_components["wires"]):
            if wire == wire_to_find:
                wire_index = w+1
        return wire_index

class Detector(Component):
    def __init__(self, window):
        super().__init__(window)

        self.shape_type = ["half circle"]
        self.shape_scale = 0.75

        # Properties
        self.herald = 0
        self.create_property_box()

    @property
    def length(self):
        return 1

    def create_property_box(self):
        self.property_box.add_property("herald", self.herald, QIntValidator(0, 100))

    def update_property(self, property_name):
        if property_name == "herald":
            self.herald = int(self.property_box.properties["herald"].text())
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
        wire_index = self.get_wire_index(self.connected_wires[0])
        self.window.console.code += "add_detector(wire = "+str(wire_index)+", herald = "+str(self.herald)+")\n"
    
    def add_to_sim(self):
        wires = [self.window.canvas.placed_components["wires"].index(w) + 1 for w in self.connected_wires]
        self.window.interface.circuit.add_detector(wires = wires, herald = self.herald)

class Loss(Component):
    def __init__(self, window):
        super().__init__(window)

        # Style
        self.shape_scale = 0.5
        self.shape_type = ["diagonal line"]

        # Properties
        self.eta = 1
        self.create_property_box()

    @property
    def length(self):
        return 1

    def create_property_box(self):
        self.property_box.add_property("eta", self.eta, QDoubleValidator(0, 1, 2))

    def update_property(self, property_name):
        if property_name == "eta":
            self.eta = float(self.property_box.properties["eta"].text())
            self.window.console.refresh()
    
    @property
    def placeable(self):
        if self.overlaps_a_component(self.potential_placement):
            return False
        if self.overlaps_a_wire(self.potential_placement):
            return True
        
    def add_to_console(self):
        wire_index = self.get_wire_index(self.connected_wires[0])
        if self.eta == 1:
            self.window.console.code += "add_loss(wire = "+str(wire_index)+")\n"
        else:
            self.window.console.code += "add_loss(wire = "+str(wire_index)+", eta = "+str(self.eta)+")\n"

    def add_to_sim(self):
        wires = [self.window.canvas.placed_components["wires"].index(w) + 1 for w in self.connected_wires]
        self.window.interface.circuit.add_loss(wire = wires[0], eta = self.eta)

class Wire(Component):
    def __init__(self, window):
        super().__init__(window)

        # Style
        self.shape_scale = 0.75
        self.shape_type = ["square", None]

        # Properties
        self.n_photons = 0
        self.create_property_box()
        self.direction = "H"

    @property
    def length(self):
        return 2

    def create_property_box(self):
        self.property_box.add_property("n_photons", self.n_photons, QIntValidator(0, 100))

    def update_property(self, property_name):
        if property_name == "n_photons":
            self.n_photons = int(self.property_box.properties["n_photons"].text())
            self.window.control_panel.input_state_tab.update_gram_matrix()
            self.window.console.refresh()

    @property
    def placeable(self):
        if self.overlaps_a_wire(self.potential_placement):
            return False
        if self.overlaps_a_wire_edge(self.potential_placement):
            return False
        if self.overlaps_a_component(self.potential_placement):
            return False
        if self.spans_a_component(self.potential_placement):
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
        self.create_property_box()
        self.direction = "V"

    @property
    def length(self):
        return 2

    def create_property_box(self):
        self.property_box.add_property("angle", self.theta, QDoubleValidator(0, 180, 2))

    def update_property(self, property_name):
        if property_name == "angle":
            self.theta = float(self.property_box.properties["angle"].text())
            self.window.console.refresh()

    @property
    def placeable(self):
        if self.overlaps_a_component(self.potential_placement):
            return False
        if self.overlaps_itself(self.potential_placement):
            return False
        if self.spans_a_component(self.potential_placement):
            return False
        if self.overlaps_a_wire_edge(self.potential_placement):
            return False
        if self.overlaps_a_wire(self.potential_placement):
            return True
        return False
    
    def add_to_console(self):
        wire_indices = [self.get_wire_index(wire) for wire in self.connected_wires]
        if self.theta == 90:
            self.window.console.code += "add_beamsplitter(wire = "+str(wire_indices)+")\n"
        else:
            self.window.console.code += "add_beamsplitter(wire = "+str(wire_indices)+", theta = "+str(self.theta)+")\n"
    
    def add_to_sim(self):
        wires = [self.window.canvas.placed_components["wires"].index(w) + 1 for w in self.connected_wires]
        self.window.interface.circuit.add_beamsplitter(wires = wires, theta = self.theta)

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

    def create_property_box(self):
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
        wire_indices = [self.get_wire_index(wire) for wire in self.connected_wires]
        self.window.console.code += "add_switch(wire = "+str(wire_indices)+")\n"

    def add_to_sim(self):
        wires = [self.window.canvas.placed_components["wires"].index(w) + 1 for w in self.connected_wires]
        self.window.interface.circuit.add_switch(wires = wires)

class PhaseShift(Component):
    def __init__(self, window):
        super().__init__(window)

        # Style
        self.shape_scale = 0.5
        self.shape_type = ["square"]

        # Properties
        self.phase = 180
        self.create_property_box()

    @property
    def length(self):
        return 1

    def create_property_box(self):
        self.property_box.add_property("phase", self.phase, QDoubleValidator(0, 360, 2))

    def update_property(self, property_name):
        if property_name == "phase":
            self.phase = float(self.property_box.properties["phase"].text())
            self.window.console.refresh()
    
    @property
    def placeable(self):
        if self.overlaps_a_component(self.potential_placement):
            return False
        if self.overlaps_a_wire(self.potential_placement):
            return True
        
    def add_to_console(self):
        wire_index = self.get_wire_index(self.connected_wires[0])
        if self.phase == 180:
            self.window.console.code += "add_phaseshift(wire = "+str(wire_index)+")\n"
        else:
            self.window.console.code += "add_phaseshift(wire = "+str(wire_index)+", phase = "+str(self.phase)+")\n"

    def add_to_sim(self):
        wires = [self.window.canvas.placed_components["wires"].index(w) + 1 for w in self.connected_wires]
        self.window.interface.circuit.add_phaseshift(wire = wires[0], phase = self.phase)