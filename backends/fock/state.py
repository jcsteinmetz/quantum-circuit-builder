import math
import itertools
import numpy as np
from backends.utils import rank_to_basis, calculate_hilbert_dimension

class State:
    def __init__(self, circuit):
        self.circuit = circuit

        self.density_matrix = np.zeros((self.hilbert_dimension, self.hilbert_dimension))

    @property
    def output_data(self):
        return self.density_matrix

    @property
    def occupied_ranks(self):
        return [rank for rank in range(self.circuit.state.hilbert_dimension) if self.circuit.state.density_matrix[rank, rank] != 0]

    @property
    def hilbert_dimension(self):
        return calculate_hilbert_dimension(self.circuit.n_wires, self.circuit.n_photons)
    
    def apply_component(self, comp):
        unitary = comp.unitary()
        self.density_matrix = unitary @ self.density_matrix @ np.conjugate(unitary).T

    def basis_element(self, rank):
        return rank_to_basis(self.circuit.n_wires, self.circuit.n_photons, rank)
    
    def basis_rank(self, element):
        n_photons = int(sum(element))
        rank = 0
        for remaining_modes, used_photons in zip(reversed(range(1, self.circuit.n_wires)), itertools.accumulate(element)):
            remaining_photons = n_photons - used_photons
            rank += sum(math.comb(n_pp + remaining_modes - 1, n_pp) for n_pp in range(int(remaining_photons)))
        return rank
    
    def eliminate_tolerance(self, tol=1E-10):
        self.density_matrix[np.abs(self.density_matrix) < tol] = 0