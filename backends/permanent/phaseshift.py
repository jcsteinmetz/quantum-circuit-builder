import numpy as np
from backends.permanent.component import Component
from backends.utils import degrees_to_radians

class PhaseShift(Component):
    """
    Phase shift in the permanent backend.

    Attributes:
    wire (int): wire experiencing the phase shift (1-indexed)
    phase (float): phase shift angle
    """
    def __init__(self, state, *, wire, phase = 180):
        super().__init__(state)

        if not isinstance(wire, int):
            raise ValueError("Phase shift requires exactly 1 wire.")
        
        if not 0 <= phase <= 360:
            raise ValueError("Phase must be between 0 and 360.")
        
        self.wire = wire
        self.reindexed_wire = self.wire - 1

        self.phase = degrees_to_radians(phase)

    def apply(self, circuit):
        unitary = self.unitary()
        circuit.circuit_unitary = unitary @ circuit.circuit_unitary

    def unitary(self):
        unitary = np.eye(self.circuit.n_wires, dtype=complex)
        unitary[self.reindexed_wire, self.reindexed_wire] = np.exp(1j*self.phase)
        return unitary