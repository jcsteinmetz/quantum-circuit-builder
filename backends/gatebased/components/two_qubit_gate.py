import numpy as np
from abc import abstractmethod
from backends.component import Component

class TwoQubitGate(Component):
    def __init__(self, backend, *, qubits):
        self.backend = backend
        self.targeted_qubits = qubits
        self.reindexed_targeted_qubits = [qubit - 1 for qubit in qubits]

    def validate_input(self):
        if any(self.reindexed_qubits < 0) or any(self.reindexed_qubits >= self.backend.n_qubits):
            raise ValueError("Invalid choice of qubits.")
        if len(self.reindexed_qubits) != 2:
            raise ValueError("The number of qubits must be 2.")
    
    @abstractmethod
    def unitary(self):
        pass

    def apply(self):
        unitary = self.unitary()
        self.backend.density_matrix = unitary @ self.backend.density_matrix @ np.conjugate(unitary).T