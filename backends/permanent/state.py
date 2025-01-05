import numpy as np

class State:
    def __init__(self, circuit):
        self.circuit = circuit
        self.output_probabilities = np.zeros(self.circuit.hilbert_dimension)

    @property
    def output_data(self):
        return self.output_probabilities
    
    def eliminate_tolerance(self, tol=1E-10):
        self.output_probabilities[np.abs(self.output_probabilities) < tol] = 0