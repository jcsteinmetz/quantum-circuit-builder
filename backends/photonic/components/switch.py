from backends.photonic.components.component import Component

class Switch(Component):
    
    def __init__(self, backend, *, wires):

        self.backend = backend
        
        self.wires = wires
        self.reindexed_wires = [wire - 1 for wire in self.wires]

        self.validate_input()
    
    def validate_input(self):
        if len(self.wires) != 2:
            raise ValueError("Switch requires exactly 2 wires.")