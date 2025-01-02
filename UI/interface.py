import sys
sys.path.append('./backends/fock')

from circuit import Circuit

class Interface:
    def __init__(self, window):
        self.window = window
        self.circuit = None
        self.backend = None

    def build_circuit(self):
        self.circuit = Circuit(self.window.canvas.n_wires, self.window.canvas.n_photons)

        for comp in self.window.canvas.placed_components["components"]:
            comp.add_to_sim()

        self.add_detectors()

        # return self.circuit
    
    def add_detectors(self):
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