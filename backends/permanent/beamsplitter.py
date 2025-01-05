"""
Contains the beam splitter class in Fock space.
"""

import numpy as np
import scipy
from backends.permanent.component import Component
from backends.utils import degrees_to_radians, spin_y_matrix

class BeamSplitter(Component):
    """
    Beam splitter in Fock space.

    Attributes:
    wires (list): list of wires connected to the beam splitter (1-indexed)
    theta (float): beam splitter angle in degrees, where 90 is a balanced splitter
    """
    def __init__(self, circuit, *, wires, theta = 90):
        super().__init__(circuit)

        if len(wires) != 2:
            raise ValueError("Beam splitter requires exactly 2 wires.")
        
        if not 0 <= theta <= 180:
            raise ValueError("Beam splitter angle must be in the range [0, 180].")

        self.wires = wires
        self.reindexed_wires = [wire - 1 for wire in self.wires]
        self.theta = degrees_to_radians(theta)

    def unitary(self):
        unitary = np.eye(self.circuit.n_wires, dtype=complex)
        wire0 = self.reindexed_wires[0]
        wire1 = self.reindexed_wires[1]
        two_wire_unitary = self.two_wire_unitary()
        unitary[wire0, wire0] = two_wire_unitary[0, 0]
        unitary[wire0, wire1] = two_wire_unitary[0, 1]
        unitary[wire1, wire0] = two_wire_unitary[1, 0]
        unitary[wire1, wire1] = two_wire_unitary[1, 1]
        return unitary

    def two_wire_unitary(self):
        """Unitary operator in the space of the two wires connected by the beam splitter."""
        return scipy.linalg.expm(1j*(self.theta/2)*spin_y_matrix(2))