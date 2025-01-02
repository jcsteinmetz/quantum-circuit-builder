import numpy as np
from backends.fock.component import Component

class BeamSplitter(Component):
    def __init__(self, circuit, *, wires, theta = 90):
        super().__init__(circuit)

        self.wires = wires
        self.theta = theta

    def unitary(self):
        unitary = np.zeros((self.circuit.state.hilbert_dimension, self.circuit.state.hilbert_dimension))
        return unitary