"""
Basic Fock state model for fixed photon number
"""

import numpy as np
from backends.backend import Backend
from backends.fock.state import State
from backends.fock.beamsplitter import BeamSplitter
from backends.fock.switch import Switch

class Fock(Backend):
    def __init__(self, n_wires, n_photons):

        self.n_wires = n_wires
        self.n_photons = n_photons

        if self.n_wires < 1:
            raise ValueError("No wires in the circuit.")

        self.state = State(self)

        self.component_list = []

    def set_input_state(self, input_basis_element):
        input_basis_rank = self.state.basis_rank(input_basis_element)
        self.state.density_matrix = np.zeros((self.state.hilbert_dimension, self.state.hilbert_dimension))
        self.state.density_matrix[input_basis_rank, input_basis_rank] = 1

    def run(self):
        for comp in self.component_list:
            self.state.apply_component(comp)
            self.state.eliminate_tolerance()

    def add_beamsplitter(self, **kwargs):
        comp = BeamSplitter(self, **kwargs)
        self.component_list.append(comp)

    def add_switch(self, **kwargs):
        comp = Switch(self, **kwargs)
        self.component_list.append(comp)

    def add_loss(self, **kwargs):
        raise ValueError("Loss is not implemented in the Fock backend.")

    def add_detector(self, **kwargs):
        raise ValueError("Detectors are not implemented in the Fock backend.")
        