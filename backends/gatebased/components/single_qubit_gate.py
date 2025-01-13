import numpy as np
from backends.component import Component
from backends.utils import insert_gate

class SingleQubitGate(Component):
    def __init__(self, backend, *, qubit):
        self.backend = backend
        self.targeted_qubit = qubit
        self.reindexed_targeted_qubit = qubit - 1

    def validate_input(self):
        if self.reindexed_qubit < 0 or self.reindexed_qubit >= self.backend.n_qubits:
            raise ValueError("Invalid qubit choice.")
        
    def unitary(self):
        return insert_gate(self.single_qubit_unitary, self.reindexed_targeted_qubit, self.backend.n_qubits)

    def apply(self):
        unitary = self.unitary()
        self.backend.density_matrix = unitary @ self.backend.density_matrix @ np.conjugate(unitary).T