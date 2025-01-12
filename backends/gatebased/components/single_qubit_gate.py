import numpy as np
from backends.component import Component
from backends.utils import pauli

class SingleQubitGate(Component):
    def __init__(self, backend, *, qubit):
        self.backend = backend
        self.targeted_qubit = qubit
        self.reindexed_targeted_qubit = qubit - 1

    def validate_input(self):
        if self.reindexed_qubit < 0 or self.reindexed_qubit >= self.backend.n_qubits:
            raise ValueError("Invalid qubit choice.")
        
    def unitary(self):
        if self.reindexed_targeted_qubit == 0:
            unitary = self.single_qubit_unitary
        else:
            unitary = np.eye(2)

        for qubit in range(1, self.backend.n_qubits):
            if qubit == self.reindexed_targeted_qubit:
                unitary = np.kron(unitary, self.single_qubit_unitary)
            else:
                unitary = np.kron(unitary, np.eye(2))
        return unitary

    def apply(self):
        unitary = self.unitary()
        self.backend.density_matrix = unitary @ self.backend.density_matrix @ np.conjugate(unitary).T