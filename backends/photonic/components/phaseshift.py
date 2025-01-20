from backends.component import Component
from backends.utils import degrees_to_radians

class PhaseShift(Component):
    def __init__(self, backend, *, wires, phase = 180):

        self.wires = wires
        self.reindexed_wires = [w - 1 for w in wires]

        self.phase = degrees_to_radians(phase)

        super().__init__(backend)
    
    def validate_input(self):
        if not 0 <= self.phase <= 360:
            raise ValueError("Phase must be between 0 and 360.")