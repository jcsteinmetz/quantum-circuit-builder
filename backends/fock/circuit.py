"""
Basic Fock state model for fixed photon number
"""

from backends.fock.state import State
from backends.fock.beamsplitter import BeamSplitter

class Circuit:
    def __init__(self, n_wires, n_photons):

        self.n_wires = n_wires
        self.n_photons = n_photons

        if self.n_wires < 1:
            raise ValueError("No wires in the circuit.")

        self.state = State(self)

        self.component_list = []

    def run(self):
        for comp in self.component_list:
            self.state.apply_component(comp)

    def add_beamsplitter(self, **kwargs):
        comp = BeamSplitter(self, **kwargs)
        self.component_list.append(comp)
        