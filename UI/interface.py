import numpy as np
from backends.fock.fock import Fock
from backends.permanent.permanent import Permanent

class Interface:
    def __init__(self, window):
        self.window = window
        self.circuit = None
        self.backend = None

    def build_circuit(self):
        if self.backend == "fock":
            self.circuit = Fock(self.window.canvas.n_wires, self.window.canvas.n_photons)
        elif self.backend == "permanent":
            self.circuit = Permanent(self.window.canvas.n_wires, self.window.canvas.n_photons)
        elif self.backend == None:
            raise ValueError("Please select a backend.")
        else:
            raise ValueError("Invalid backend choice.")
        
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