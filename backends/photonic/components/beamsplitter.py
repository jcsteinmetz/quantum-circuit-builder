from backends.photonic.components.component import Component
from backends.utils import degrees_to_radians

class BeamSplitter(Component):
    def __init__(self, backend, *, wires, theta=90):

        self.backend = backend
        self.wires = wires
        self.reindexed_wires = [w - 1 for w in wires]
        self.theta = degrees_to_radians(theta)

        self.validate_input()
    
    def validate_input(self):
        if len(self.wires) != 2:
            raise ValueError("Beam splitter requires exactly 2 wires.")
        
        if not 0 <= self.theta <= 180:
            raise ValueError("Beam splitter angle must be in the range [0, 180].")