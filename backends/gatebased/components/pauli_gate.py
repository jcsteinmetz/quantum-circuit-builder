from backends.component import Component

class PauliGate(Component):
    def __init__(self, backend, *, qubits):

        self.targeted_qubits = qubits
        self.reindexed_targeted_qubits = [q - 1 for q in qubits]

        super().__init__(backend)
    
    def validate_input(self):
        pass