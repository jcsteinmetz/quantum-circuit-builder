class Interface:
    """
    Class containing communications between the UI and the backend. Translates the list of drawn components
    into code that is run in the chosen backend.
    """
    def __init__(self, window):
        self.window = window
        self.circuit = None
        self.chosen_backend = None

    def build_circuit(self):
        """Creates a circuit in the chosen backend and adds all drawn components."""
        if self.window.simulation_type == "photonic":
            self.circuit = self.chosen_backend(self.window.canvas.n_wires, self.window.canvas.n_photons)
            self.circuit.set_input_state(self.input_fock_state)
        else:
            self.circuit = self.chosen_backend(self.window.canvas.n_wires)
            self.circuit.set_input_state(self.input_qubit_state)

        for comp in self.window.canvas.placed_components["components"]:
            comp.add_to_sim()

        self.add_detectors()
    
    def add_detectors(self):
        """Add all detectors at once at the end of the simulation."""
        wires = []
        herald = []
        if self.window.canvas.placed_components["detectors"]:
            for comp in self.window.canvas.placed_components["detectors"]:
                for w, wire in enumerate(self.window.canvas.placed_components["wires"]):
                    if comp.node_positions[0] == wire.node_positions[1]:
                        wires.append(w+1)
                        herald.append(comp.herald)
            self.circuit.add_detector(wires = wires, herald = herald)

    def run_circuit(self):
        self.circuit.run()

    @property
    def input_fock_state(self):
        """The Fock state at the beginning of the circuit, taken from the wires' properties entered by the user."""
        return tuple(wire.n_photons for wire in self.window.canvas.placed_components["wires"])
    
    @property
    def input_qubit_state(self):
        """The state of N qubits at the beginning of the circuit. Equivalent of input_fock_state but in a gate-based backend."""
        return tuple(qubit.initial_state for qubit in self.window.canvas.placed_components["wires"])