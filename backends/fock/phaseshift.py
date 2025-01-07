import numpy as np
from backends.fock.component import Component
from backends.utils import rank_to_basis, degrees_to_radians

class PhaseShift(Component):
    """
    Phase shift in Fock space.

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

    def apply(self, state):
        unitary = self.unitary()
        state.density_matrix = unitary @ state.density_matrix @ np.conjugate(unitary).T

    def unitary(self):
        """Switch operator in the full Fock space."""
        hilbert = self.state.hilbert_dimension
        unitary = np.eye(hilbert, dtype=complex)

        if self.phase == 0 or self.phase == 2*np.pi:
            return unitary

        for rank in self.state.occupied_ranks:
            basis_element = rank_to_basis(self.state.n_wires, self.state.n_photons, rank)
            photons_in_wire = basis_element[self.reindexed_wire]

            if photons_in_wire == 0:
                continue

            unitary[rank, rank] = np.exp(1j*self.phase)

        return unitary