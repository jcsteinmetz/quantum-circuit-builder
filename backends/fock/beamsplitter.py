"""
Contains the beam splitter class in Fock space.
"""

import numpy as np
import scipy
from backends.fock.component import Component
from backends.utils import calculate_hilbert_dimension, spin_y_matrix, degrees_to_radians, rank_to_basis, basis_to_rank

class BeamSplitter(Component):
    """
    Beam splitter in Fock space.

    Attributes:
    wires (list): list of wires connected to the beam splitter (1-indexed)
    theta (float): beam splitter angle in degrees, where 90 is a balanced splitter
    """
    def __init__(self, state, *, wires, theta = 90):
        super().__init__(state)

        if len(wires) != 2:
            raise ValueError("Beam splitter requires exactly 2 wires.")
        
        if not 0 <= theta <= 180:
            raise ValueError("Beam splitter angle must be in the range [0, 180].")

        self.wires = wires
        self.reindexed_wires = [wire - 1 for wire in self.wires]
        self.theta = degrees_to_radians(theta)

        self.photon_count_per_rank = {}

        # self.two_wire_unitaries = {n_photons: self.two_wire_unitary(n_photons) for n_photons in set(self.photon_count_per_rank.values())}
        self.two_wire_unitaries = {n_photons: self.two_wire_unitary(n_photons) for n_photons in range(self.state.n_photons+1)}

    def unitary(self):
        """Unitary operator in the full Fock space."""
        unitary = np.eye(self.state.hilbert_dimension, dtype=complex)

        self.photon_count_per_rank = self.log_entering_photons()

        used_ranks = []
        for rank, photons in self.photon_count_per_rank.items():

            if photons == 0 or rank in used_ranks:
                continue

            # Find all ranks connected to the current rank by the beam splitter
            connected_ranks = self.connected_ranks(rank)

            # Insert the two-wire unitary into the full Fock space
            unitary[np.ix_(connected_ranks, connected_ranks)] = self.two_wire_unitaries[photons]

            # Track the ranks we have dealt with
            used_ranks.extend(connected_ranks)

        return unitary

    def two_wire_unitary(self, n):
        """Unitary operator in the space of the two wires connected by the beam splitter."""
        return scipy.linalg.expm(1j*(self.theta/2)*spin_y_matrix(n+1))
    
    def log_entering_photons(self):
        """Returns a dict containing the number of photons entering the beam splitter for each rank in the Fock space."""
        photon_count_per_rank = {}

        # For each rank, count the photons in self.wires
        for rank in self.state.occupied_ranks:
            basis_element = np.array(rank_to_basis(self.state.n_wires, self.state.n_photons, rank))
            photon_count_per_rank[rank] = int(sum(basis_element[self.reindexed_wires]))
        return photon_count_per_rank
    
    def connected_ranks(self, rank):
        """Finds all other ranks in the Fock space connected to the given rank by the beam splitting operation."""
        basis_element = np.array(rank_to_basis(self.state.n_wires, self.state.n_photons, rank))

        # Generate all possible combinations of occupation numbers within self.wires
        photons = self.photon_count_per_rank[rank]
        wire_combinations = [rank_to_basis(2, photons, rank) for rank in range(calculate_hilbert_dimension(2, photons))]

        # Shuffle the occupation numbers within self.wires, and return the ranks of the resulting basis elements
        connected_ranks = []
        for combination in wire_combinations:
            basis_element[self.reindexed_wires] = combination
            connected_ranks.append(basis_to_rank(tuple(basis_element)))
        return connected_ranks