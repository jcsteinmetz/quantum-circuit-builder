import numpy as np
from abc import abstractmethod
from backends.component import Component

class TwoQubitGate(Component):
    def __init__(self, backend, *, qubits):
        self.backend = backend
        self.targeted_qubits = qubits
        self.reindexed_targeted_qubits = [qubit - 1 for qubit in qubits]

    def validate_input(self):
        if any(self.reindexed_targeted_qubits < 0) or any(self.reindexed_targeted_qubits >= self.backend.n_qubits):
            raise ValueError("Invalid choice of qubits.")
        if len(self.reindexed_targeted_qubits) != 2:
            raise ValueError("The number of qubits must be 2.")