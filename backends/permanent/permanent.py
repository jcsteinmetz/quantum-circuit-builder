"""
Basic simulation based on matrix permanents
"""

import itertools
import math
import numpy as np
from backends.permanent.state import State
from backends.backend import Backend
from backends.permanent.beamsplitter import BeamSplitter
from backends.permanent.switch import Switch
from backends.utils import calculate_hilbert_dimension, rank_to_basis

class Permanent(Backend):
    def __init__(self, n_wires, n_photons):

        self.n_wires = n_wires
        self.n_photons = n_photons

        self.state = State(self)
        self.input_basis_element = ()

        if self.n_wires < 1:
            raise ValueError("No wires in the circuit.")

        self.component_list = []

    def set_input_state(self, input_basis_element):
        self.input_basis_element = input_basis_element

    def run(self):
        circuit_unitary = np.eye(self.n_wires)
        for comp in self.component_list:
            unitary = comp.unitary()
            circuit_unitary = unitary @ circuit_unitary

        for rank in range(self.hilbert_dimension):
            output_basis_element = self.basis_element(rank)
            self.state.output_probabilities[rank] = self.output_probability(circuit_unitary, output_basis_element)
        self.state.eliminate_tolerance()

    def output_probability(self, circuit_unitary, output_basis_element):
        circuit_submatrix = self.submatrix(circuit_unitary, output_basis_element)
        return (self.matrix_permanent(circuit_submatrix))**2/np.prod([math.factorial(n) for n in output_basis_element])

    def submatrix(self, circuit_unitary, output_basis_element):
        UT = np.zeros((self.n_wires, self.n_photons))
        used_photons = 0
        for j, tj in enumerate(self.input_basis_element):
            for n in range(used_photons, used_photons + tj):
                UT[:, n] = circuit_unitary[:, j]
            used_photons += tj

        used_photons = 0
        UST = np.zeros((2, 2))
        for i, si in enumerate(output_basis_element):
            for n in range(used_photons, used_photons + si):
                UST[n, :] = UT[i, :]
            used_photons += si

        return UST

    def basis_element(self, rank):
        return rank_to_basis(self.n_wires, self.n_photons, rank)
    
    def basis_rank(self, element):
        n_photons = int(sum(element))
        rank = 0
        for remaining_modes, used_photons in zip(reversed(range(1, self.n_wires)), itertools.accumulate(element)):
            remaining_photons = n_photons - used_photons
            rank += sum(math.comb(n_pp + remaining_modes - 1, n_pp) for n_pp in range(int(remaining_photons)))
        return rank

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
    
    @property
    def hilbert_dimension(self):
        return calculate_hilbert_dimension(self.n_wires, self.n_photons)
        
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