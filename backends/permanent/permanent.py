"""
Basic simulation based on matrix permanents
"""

import itertools
import math
import numpy as np
from backends.backend import Backend
from backends.permanent.beamsplitter import BeamSplitter
from backends.permanent.switch import Switch
from backends.utils import calculate_hilbert_dimension, rank_to_basis

class Permanent(Backend):
    def __init__(self, n_wires, n_photons):
        super().__init__(n_wires, n_photons)

        self.state = State(self.n_wires, self.n_photons)

        self.component_list = []

    def set_input_state(self, input_basis_element):
        self.state.input_basis_element = input_basis_element

    def run(self):
        circuit_unitary = np.eye(self.n_wires)
        for comp in self.component_list:
            unitary = comp.unitary()
            circuit_unitary = unitary @ circuit_unitary

        for rank in range(self.state.hilbert_dimension):
            output_basis_element = rank_to_basis(self.n_wires, self.n_photons, rank)
            self.state.output_probabilities[rank] = self.output_probability(circuit_unitary, output_basis_element)
        self.state.eliminate_tolerance()

    def output_probability(self, circuit_unitary, output_basis_element):
        circuit_submatrix = self.submatrix(circuit_unitary, output_basis_element)
        return (self.matrix_permanent(circuit_submatrix))**2/np.prod([math.factorial(n) for n in output_basis_element])

    def submatrix(self, circuit_unitary, output_basis_element):
        UT = np.zeros((self.n_wires, self.n_photons), dtype=complex)
        used_photons = 0
        for j, tj in enumerate(self.state.input_basis_element):
            for n in range(used_photons, used_photons + tj):
                UT[:, n] = circuit_unitary[:, j]
            used_photons += tj

        used_photons = 0
        UST = np.zeros((self.n_photons, self.n_photons), dtype=complex)
        for i, si in enumerate(output_basis_element):
            for n in range(used_photons, used_photons + si):
                UST[n, :] = UT[i, :]
            used_photons += si

        return UST

    def add_beamsplitter(self, **kwargs):
        comp = BeamSplitter(self, **kwargs)
        self.component_list.append(comp)

    def add_switch(self, **kwargs):
        comp = Switch(self, **kwargs)
        self.component_list.append(comp)

    def add_loss(self, **kwargs):
        raise ValueError("Loss is not implemented yet in the permanent backend.")

    def add_detector(self, **kwargs):
        raise ValueError("Detectors are not implemented yet in the permanent backend.")
        
    def matrix_permanent(self, matrix):
        n = len(matrix)
        perms = itertools.permutations(range(n))
        total = 0
        for perm in perms:
            product = 1
            for i in range(n):
                product *= matrix[i, perm[i]]
            total += product
        return total
    
    @property
    def output_data(self):
        return self.state.output_probabilities
    
class State:
    def __init__(self, n_wires, n_photons):
        self.n_wires = n_wires
        self.n_photons = n_photons

        self.hilbert_dimension = calculate_hilbert_dimension(self.n_wires, self.n_photons)

        self.input_basis_element = ()
        self.output_probabilities = np.zeros(self.hilbert_dimension)
    
    def eliminate_tolerance(self, tol=1E-10):
        self.output_probabilities[np.abs(self.output_probabilities) < tol] = 0