import numpy as np
from backends.fock.component import Component

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
        """Switch operator in the full Fock space."""
        hilbert = self.circuit.state.hilbert_dimension
        unitary = np.zeros((hilbert, hilbert), dtype=complex)

        for rank in self.circuit.state.occupied_ranks:
            switched_basis_element = list(self.circuit.state.basis_element(rank))
            i, j = self.reindexed_wires
            switched_basis_element[i], switched_basis_element[j] = switched_basis_element[j], switched_basis_element[i]
            switched_basis_element = tuple(switched_basis_element)
            switched_rank = self.circuit.state.basis_rank(switched_basis_element)
            unitary[switched_rank, rank] = 1

        return unitary