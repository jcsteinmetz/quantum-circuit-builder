from backends.component import Component

class Loss(Component):
    def __init__(self, backend, *, wire, eta = 1):
        
        self.wire = wire
        self.reindexed_wire = self.wire - 1

        self.eta = eta

        super().__init__(backend)
    
    def validate_input(self):
        if not isinstance(self.wire, int):
            raise ValueError("Loss requires exactly 1 wire.")
        
        if not 0 <= self.eta <= 1:
            raise ValueError("Transmission must be between 0 and 1.")