import numpy as np
from backends.permanent.component import Component

class Switch(Component):
    """
    Switch in Fock space.

    Attributes:
    wires (list): list of wires connected to the beam splitter (1-indexed)
    """
    def __init__(self, circuit, *, wires):
        super().__init__(circuit)

        if len(wires) != 2:
            raise ValueError("Switch requires exactly 2 wires.")
        
        self.wires = wires
        self.reindexed_wires = [wire - 1 for wire in self.wires]

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
        return np.array([[0, 1], [1, 0]])
