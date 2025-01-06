from backends.permanent.component import Component

class Detector(Component):
    def __init__(self, circuit, *, wires, herald):
        super().__init__(circuit)
        self.circuit = circuit
        self.wires = wires
        self.herald = herald

        if len(self.wires) >= self.circuit.n_wires:
            raise ValueError("No state remaining. All photons hit detectors.")
        if len(self.herald) != len(self.wires):
            raise ValueError("Mismatch between length of herald and number of detectors.")

    def apply(self, circuit):
        circuit.state.postselect(self.wires, self.herald)