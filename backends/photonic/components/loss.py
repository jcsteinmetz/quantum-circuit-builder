from backends.component import Component

class Loss(Component):
    def __init__(self, backend, *, wires, eta = 1):
        
        self.wires = wires
        self.reindexed_wires = [w - 1 for w in wires]

        self.eta = eta

        super().__init__(backend)
    
    def validate_input(self):
        if not 0 <= self.eta <= 1:
            raise ValueError("Transmission must be between 0 and 1.")