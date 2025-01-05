"""
Basic Fock state model for fixed photon number
"""

import numpy as np
from backends.backend import Backend
from backends.fock.beamsplitter import BeamSplitter
from backends.fock.switch import Switch
from backends.fock.loss import Loss
from backends.utils import calculate_hilbert_dimension, basis_to_rank, rank_to_basis

class Fock(Backend):
    def __init__(self, n_wires, n_photons):
        super().__init__(n_wires, n_photons)

        self.state = State(self.n_wires, self.n_photons)

        self.component_list = []

    def set_input_state(self, input_basis_element):
        self.state.set_density_matrix(input_basis_element)

    def run(self):
        for comp in self.component_list:
            comp.apply(self.state)
            self.state.eliminate_tolerance()

    def add_beamsplitter(self, **kwargs):
        comp = BeamSplitter(self.state, **kwargs)
        self.component_list.append(comp)

    def add_switch(self, **kwargs):
        comp = Switch(self.state, **kwargs)
        self.component_list.append(comp)

    def add_loss(self, **kwargs):
        comp = Loss(self.state, **kwargs)
        self.component_list.append(comp)

    def add_detector(self, **kwargs):
        raise NotImplementedError("Detectors are not implemented yet in the Fock backend.")
    
    @property
    def output_data(self):
        prob_vector = np.real(self.state.density_matrix.diagonal())
        table_length = np.count_nonzero(prob_vector)
        table_data = np.zeros((table_length, 2), dtype=object)
        for row, rank in enumerate(self.state.occupied_ranks):
            basis_element_string = str(rank_to_basis(self.n_wires, self.n_photons, rank))
            basis_element_string = basis_element_string.replace("(", "")
            basis_element_string = basis_element_string.replace(")", "")
            basis_element_string = basis_element_string.replace(" ", "")
            basis_element_string = basis_element_string.replace(",", "")
            table_data[row, 0] = "".join(basis_element_string)
            table_data[row, 1] = prob_vector[rank]

        for row in range(len(table_data[:, 1])):
            table_data[row, 1] = f'{float(f"{table_data[row, 1]:.4g}"):g}'
        return table_data
        
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
    
    def eliminate_tolerance(self, tol=1E-10):
        self.density_matrix[np.abs(self.density_matrix) < tol] = 0