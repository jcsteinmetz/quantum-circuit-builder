import math
import numpy as np

class State:
    def __init__(self, circuit):
        self.circuit = circuit

        self.density_matrix = np.zeros((self.hilbert_dimension, self.hilbert_dimension))

    @property
    def hilbert_dimension(self):
        return math.comb(self.circuit.n_photons + self.circuit.n_wires - 1, self.circuit.n_photons)
    
    def apply_component(self, comp):
        self.density_matrix = comp.unitary() @ self.density_matrix @ np.conjugate(comp.unitary()).T