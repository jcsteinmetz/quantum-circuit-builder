from backends.component import Component

class Switch(Component):
    
    def __init__(self, backend, *, wires):
        
        self.wires = wires
        self.reindexed_wires = [wire - 1 for wire in self.wires]

        super().__init__(backend)
    
    def validate_input(self):
        if len(self.wires) != 2:
            raise ValueError("Switch requires exactly 2 wires.")