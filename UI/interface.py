import numpy as np
from backends.fock import Fock
from backends.permanent import Permanent
from backends.xanadu import Xanadu

class Interface:
    def __init__(self, window):
        self.window = window
        self.circuit = None
        self.backend = Fock

    def build_circuit(self):
        self.circuit = self.backend(self.window.canvas.n_wires, self.window.canvas.n_photons)
        
        self.circuit.set_input_state(self.input_fock_state)

        for comp in self.window.canvas.placed_components["components"]:
            comp.add_to_sim()

        self.add_detectors()
    
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

    @property
    def input_fock_state(self):
        return tuple(wire.n_photons for wire in self.window.canvas.placed_components["wires"])