from backends.component import Component
from backends.utils import degrees_to_radians

class PhaseShift(Component):
    def __init__(self, backend, *, wire, phase = 180):

        self.wire = wire
        self.reindexed_wire = self.wire - 1

        self.phase = degrees_to_radians(phase)

        super().__init__(backend)
    
    def validate_input(self):
        if not isinstance(self.wire, int):
            raise ValueError("Phase shift requires exactly 1 wire.")
        
        if not 0 <= self.phase <= 360:
            raise ValueError("Phase must be between 0 and 360.")