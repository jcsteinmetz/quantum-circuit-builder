from PySide6.QtCore import Qt
from PySide6.QtGui import QIntValidator, QDoubleValidator
from abc import ABC, abstractmethod
from UI.property_box import PropertyBox

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
        self.snap()
        placed_wires = self.window.canvas.placed_components.get("wires", [])
        return [wire for wire in placed_wires if self.is_connected_to_wire(wire)]
    
    @property
    def connected_components(self):
        self.snap()
        self.window.canvas.snap_all_components()
        return [comp for comp in self.window.canvas.all_placed_components() if comp.is_connected_to_wire(self)]
    
    def is_connected_to_wire(self, wire):
        wire.snap()
        wire_y = wire.node_positions[0][1]
        wire_x = [pos[0] for pos in self.node_positions]
        x_min, x_max = min(wire_x), max(wire_x)

        for pos in self.node_positions:
            on_axis = pos[1] == wire_y
            in_range = x_min <= pos[0] <= x_max
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
        start_position = self.node_positions[0]

        # If no part of the component has been placed yet, snap to grid
        if not start_position:
            return snapped_mouse_position
        
        # If earlier parts of the component have been placed, snap to the component's axis
        if len(self.node_positions) > 1:
            if self.direction == "H":
                # enforce wire being horizontal
                return (snapped_mouse_position[0], start_position[1])
            else:
                # enforce components being vertical
                return (start_position[0], snapped_mouse_position[1])
        return snapped_mouse_position

    @property
    def name(self):
        all_components = list(self.window.canvas.all_placed_components())
        overall_index = all_components.index(self)
        type_index = sum(isinstance(c, self.__class__) for c in all_components[:overall_index])
        return f"{type(self).__name__[0]}{type_index+1}"

    # Transformations

    def snap(self):
        self.node_positions = [self.window.canvas.grid.snap(pos) if pos else None for pos in self.node_positions]

    def delete(self):
        self.property_box.hide()

        for component_type in ["wires", "components", "detectors"]:       

            # Delete the component
            if self in self.window.canvas.placed_components[component_type]:
                self.window.canvas.placed_components[component_type].remove(self)

                if component_type == "wires":

                    # Delete connected_components
                    for comp in self.connected_components:
                        comp.delete()

        self.window.mark_unsaved_changes()
        self.window.console.refresh()

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
        self.window.canvas.snap_all_components()
        for comp in self.window.canvas.placed_components[component_group]:
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
        if len(self.node_positions) > 0 and self.node_positions[0]:
            self.window.canvas.snap_all_components()

            for comp in self.window.canvas.all_placed_components():
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
        wire_indices = [self.get_wire_index(wire) for wire in self.connected_wires]
        if self.eta == 1:
            self.window.console.code += "circuit.add_loss(wires = "+str(wire_indices)+")\n"
        else:
            self.window.console.code += "circuit.add_loss(wires = "+str(wire_indices)+", eta = "+str(self.eta)+")\n"

    def add_to_sim(self):
        wires = [self.window.canvas.placed_components["wires"].index(w) + 1 for w in self.connected_wires]
        self.window.interface.circuit.add_loss(wires = wires, eta = self.eta)

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
            self.window.console.code += "circuit.add_beamsplitter(wires = "+str(wire_indices)+")\n"
        else:
            self.window.console.code += "circuit.add_beamsplitter(wires = "+str(wire_indices)+", theta = "+str(self.theta)+")\n"
    
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
        self.window.console.code += "circuit.add_switch(wires = "+str(wire_indices)+")\n"

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
        wire_indices = [self.get_wire_index(wire) for wire in self.connected_wires]
        if self.phase == 180:
            self.window.console.code += "circuit.add_phaseshift(wires = "+str(wire_indices)+")\n"
        else:
            self.window.console.code += "circuit.add_phaseshift(wires = "+str(wire_indices)+", phase = "+str(self.phase)+")\n"

    def add_to_sim(self):
        wires = [self.window.canvas.placed_components["wires"].index(w) + 1 for w in self.connected_wires]
        self.window.interface.circuit.add_phaseshift(wires = wires, phase = self.phase)

class PauliGate(Component):
    def __init__(self, window):
        super().__init__(window)

        # Style
        self.shape_scale = 0.5
        self.shape_type = ["square"]

        # Properties
        self.create_property_box()

    @property
    def length(self):
        return 1

    def create_property_box(self):
        pass
    
    @property
    def placeable(self):
        if self.overlaps_a_component(self.potential_placement):
            return False
        if self.overlaps_a_wire(self.potential_placement):
            return True

class XGate(PauliGate):
    def __init__(self, window):
        super().__init__(window)
        
    def add_to_console(self):
        wire_indices = [self.get_wire_index(wire) for wire in self.connected_wires]
        self.window.console.code += "circuit.add_xgate(qubits = "+str(wire_indices)+")\n"

    def add_to_sim(self):
        wires = [self.window.canvas.placed_components["wires"].index(w) + 1 for w in self.connected_wires]
        self.window.interface.circuit.add_xgate(qubits = wires)

class YGate(PauliGate):
    def __init__(self, window):
        super().__init__(window)
        
    def add_to_console(self):
        wire_indices = [self.get_wire_index(wire) for wire in self.connected_wires]
        self.window.console.code += "circuit.add_ygate(qubits = "+str(wire_indices)+")\n"

    def add_to_sim(self):
        wires = [self.window.canvas.placed_components["wires"].index(w) + 1 for w in self.connected_wires]
        self.window.interface.circuit.add_ygate(qubits = wires)

class ZGate(PauliGate):
    def __init__(self, window):
        super().__init__(window)
        
    def add_to_console(self):
        wire_indices = [self.get_wire_index(wire) for wire in self.connected_wires]
        self.window.console.code += "circuit.add_zgate(qubits = "+str(wire_indices)+")\n"

    def add_to_sim(self):
        wires = [self.window.canvas.placed_components["wires"].index(w) + 1 for w in self.connected_wires]
        self.window.interface.circuit.add_zgate(qubits = wires)

class Hadamard(Component):
    def __init__(self, window):
        super().__init__(window)

        # Style
        self.shape_scale = 0.5
        self.shape_type = ["square"]

        # Properties
        self.create_property_box()

    @property
    def length(self):
        return 1

    def create_property_box(self):
        pass
    
    @property
    def placeable(self):
        if self.overlaps_a_component(self.potential_placement):
            return False
        if self.overlaps_a_wire(self.potential_placement):
            return True
        
    def add_to_console(self):
        wire_indices = [self.get_wire_index(wire) for wire in self.connected_wires]
        self.window.console.code += "circuit.add_hadamard(qubits = "+str(wire_indices)+")\n"

    def add_to_sim(self):
        wires = [self.window.canvas.placed_components["wires"].index(w) + 1 for w in self.connected_wires]
        self.window.interface.circuit.add_hadamard(qubits = wires)

class Qubit(Component):
    def __init__(self, window):
        super().__init__(window)

        # Style
        self.shape_scale = 0.75
        self.shape_type = ["square", None]

        # Properties
        self.initial_state = 0
        self.create_property_box()
        self.direction = "H"

    @property
    def length(self):
        return 2

    def create_property_box(self):
        self.property_box.add_property("initial_state", self.initial_state, QIntValidator(0, 1))

    def update_property(self, property_name):
        if property_name == "initial_state":
            self.initial_state = int(self.property_box.properties["initial_state"].text())
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

class CNOT(Component):
    def __init__(self, window):
        super().__init__(window)

        # Style
        self.shape_scale = 0.5
        self.shape_type = ["circle", "X"]

        # Properties
        self.create_property_box()
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
        if self.overlaps_a_wire_edge(self.potential_placement):
            return False
        if self.overlaps_a_wire(self.potential_placement):
            return True
        return False
    
    def add_to_console(self):
        wire_indices = [self.get_wire_index(wire) for wire in self.connected_wires]
        self.window.console.code += "circuit.add_cnot(qubits = "+str(wire_indices)+")\n"
    
    def add_to_sim(self):
        wires = [self.window.canvas.placed_components["wires"].index(w) + 1 for w in self.connected_wires]
        self.window.interface.circuit.add_cnot(qubits = wires)