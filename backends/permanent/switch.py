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
        unitary = None
        return unitary