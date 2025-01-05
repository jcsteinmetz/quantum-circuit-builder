"""
Basic Fock state model for fixed photon number
"""

import numpy as np
from backends.backend import Backend
from backends.fock.beamsplitter import BeamSplitter
from backends.fock.switch import Switch
from backends.utils import calculate_hilbert_dimension, basis_to_rank

class Fock(Backend):
    def __init__(self, n_wires, n_photons):
        super().__init__(n_wires, n_photons)

        self.state = State(self.n_wires, self.n_photons)

        self.component_list = []

    def set_input_state(self, input_basis_element):
        self.state.set_density_matrix(input_basis_element)

    def run(self):
        for comp in self.component_list:
            self.state.apply_component(comp)
            self.state.eliminate_tolerance()

    def add_beamsplitter(self, **kwargs):
        comp = BeamSplitter(self.state, **kwargs)
        self.component_list.append(comp)

    def add_switch(self, **kwargs):
        comp = Switch(self.state, **kwargs)
        self.component_list.append(comp)

    def add_loss(self, **kwargs):
        raise NotImplementedError("Loss is not implemented yet in the Fock backend.")

    def add_detector(self, **kwargs):
        raise NotImplementedError("Detectors are not implemented yet in the Fock backend.")
    
    @property
    def output_data(self):
        return self.state.density_matrix
        
class State:
    def __init__(self, n_wires, n_photons):
        self.n_wires = n_wires
        self.n_photons = n_photons

        self.hilbert_dimension = calculate_hilbert_dimension(self.n_wires, self.n_photons)

        self.density_matrix = np.zeros((self.hilbert_dimension, self.hilbert_dimension))

    @property
    def occupied_ranks(self):
        return [rank for rank in range(self.hilbert_dimension) if self.density_matrix[rank, rank] != 0]
    
    def set_density_matrix(self, input_basis_element):
        input_basis_rank = basis_to_rank(input_basis_element)
        self.density_matrix[:] = 0
        self.density_matrix[input_basis_rank, input_basis_rank] = 1
    
    def apply_component(self, comp):
        unitary = comp.unitary()
        self.density_matrix = unitary @ self.density_matrix @ np.conjugate(unitary).T
    
    def eliminate_tolerance(self, tol=1E-10):
        self.density_matrix[np.abs(self.density_matrix) < tol] = 0