from backends.component import Component

class PauliGate(Component):
    def __init__(self, backend, *, qubit):

        self.targeted_qubit = qubit
        self.reindexed_targeted_qubit = qubit - 1

        super().__init__(backend)
    
    def validate_input(self):
        pass