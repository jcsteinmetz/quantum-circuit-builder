"""
Basic Fock state model for fixed photon number
"""

import numpy as np
import math
import scipy
from backends.backend import Backend
from backends.components.beamsplitter import BeamSplitter
from backends.components.switch import Switch
from backends.components.loss import Loss
from backends.components.detector import Detector
from backends.components.phaseshift import PhaseShift
from backends.utils import basis_to_rank, rank_to_basis, calculate_hilbert_dimension, spin_y_matrix

class Fock(Backend):
    def __init__(self, n_wires, n_photons):
        super().__init__(n_wires, n_photons)

        self.density_matrix = np.zeros((self.hilbert_dimension, self.hilbert_dimension))

    def set_input_state(self, input_basis_element):
        self.set_density_matrix(input_basis_element)

    def run(self):
        for comp in self.component_list:
            comp.apply()
            self.eliminate_tolerance()

    def add_beamsplitter(self, **kwargs):
        comp = FockBeamSplitter(self, **kwargs)
        self.add_component(comp)

    def add_switch(self, **kwargs):
        comp = FockSwitch(self, **kwargs)
        self.add_component(comp)

    def add_phaseshift(self, **kwargs):
        comp = FockPhaseShift(self, **kwargs)
        self.add_component(comp)

    def add_loss(self, **kwargs):
        comp = FockLoss(self, **kwargs)
        self.add_component(comp)

    def add_detector(self, **kwargs):
        comp = FockDetector(self, **kwargs)
        self.add_component(comp)
    
    @property
    def output_data(self):
        prob_vector = np.real(self.density_matrix.diagonal())
        table_length = np.count_nonzero(prob_vector)
        table_data = np.zeros((table_length, 2), dtype=object)
        for row, rank in enumerate(self.occupied_ranks):
            basis_element_string = str(rank_to_basis(self.n_wires, self.n_photons, rank))
            basis_element_string = basis_element_string.replace("(", "")
            basis_element_string = basis_element_string.replace(")", "")
            basis_element_string = basis_element_string.replace(" ", "")
            basis_element_string = basis_element_string.replace(",", "")
            table_data[row, 0] = "".join(basis_element_string)
            table_data[row, 1] = prob_vector[rank]

        for row in range(len(table_data[:, 1])):
            table_data[row, 1] = f'{float(f"{table_data[row, 1]:.4g}"):g}'
        return table_data
    
    @property
    def occupied_ranks(self):
        return [rank for rank in range(self.hilbert_dimension) if self.density_matrix[rank, rank] != 0]
    
    def set_density_matrix(self, input_basis_element):
        input_basis_rank = basis_to_rank(input_basis_element)
        self.density_matrix[:] = 0
        self.density_matrix[input_basis_rank, input_basis_rank] = 1
        
    def eliminate_tolerance(self, tol=1E-10):
        self.density_matrix[np.abs(self.density_matrix) < tol] = 0

class FockBeamSplitter(BeamSplitter):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.photon_count_per_rank = {}

        self.two_wire_unitaries = {n_photons: self.two_wire_unitary(n_photons) for n_photons in range(self.backend.n_photons+1)}

    def apply(self):
        unitary = self.unitary()
        self.backend.density_matrix = unitary @ self.backend.density_matrix @ np.conjugate(unitary).T

    def unitary(self):
        """Unitary operator in the full Fock space."""
        unitary = np.eye(self.backend.hilbert_dimension, dtype=complex)

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
        for rank in self.backend.occupied_ranks:
            basis_element = np.array(rank_to_basis(self.backend.n_wires, self.backend.n_photons, rank))
            photon_count_per_rank[rank] = int(sum(basis_element[self.reindexed_wires]))
        return photon_count_per_rank
    
    def connected_ranks(self, rank):
        """Finds all other ranks in the Fock space connected to the given rank by the beam splitting operation."""
        basis_element = np.array(rank_to_basis(self.backend.n_wires, self.backend.n_photons, rank))

        # Generate all possible combinations of occupation numbers within self.wires
        photons = self.photon_count_per_rank[rank]
        wire_hilbert = calculate_hilbert_dimension(2, photons)
        wire_combinations = [rank_to_basis(2, photons, rank) for rank in range(wire_hilbert) if sum(rank_to_basis(2, photons, rank)) == photons]

        # Shuffle the occupation numbers within self.wires, and return the ranks of the resulting basis elements
        connected_ranks = []
        for combination in wire_combinations:
            basis_element[self.reindexed_wires] = combination
            connected_ranks.append(basis_to_rank(tuple(basis_element)))
        return connected_ranks
    
class FockSwitch(Switch):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def apply(self):
        unitary = self.unitary()
        self.backend.density_matrix = unitary @ self.backend.density_matrix @ np.conjugate(unitary).T

    def unitary(self):
        """Switch operator in the full Fock space."""
        hilbert = self.backend.hilbert_dimension
        unitary = np.zeros((hilbert, hilbert), dtype=complex)

        for rank in self.backend.occupied_ranks:
            switched_basis_element = list(rank_to_basis(self.backend.n_wires, self.backend.n_photons, rank))
            i, j = self.reindexed_wires
            switched_basis_element[i], switched_basis_element[j] = switched_basis_element[j], switched_basis_element[i]
            switched_basis_element = tuple(switched_basis_element)
            switched_rank = basis_to_rank(switched_basis_element)
            unitary[switched_rank, rank] = 1

        return unitary
    
class FockPhaseShift(PhaseShift):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def apply(self):
        unitary = self.unitary()
        self.backend.density_matrix = unitary @ self.backend.density_matrix @ np.conjugate(unitary).T

    def unitary(self):
        """Switch operator in the full Fock space."""
        hilbert = self.backend.hilbert_dimension
        unitary = np.eye(hilbert, dtype=complex)

        if self.phase == 0 or self.phase == 2*np.pi:
            return unitary

        for rank in self.backend.occupied_ranks:
            basis_element = rank_to_basis(self.backend.n_wires, self.backend.n_photons, rank)
            photons_in_wire = basis_element[self.reindexed_wire]

            if photons_in_wire == 0:
                continue

            unitary[rank, rank] = np.exp(1j*self.phase)

        return unitary
    
class FockLoss(Loss):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def apply(self):
        self.backend.density_matrix = sum([kraus @ self.backend.density_matrix @ np.conjugate(kraus).T for kraus in self.kraus_operators().values()])

    def kraus_operators(self):
        kraus_operators = {}
        for lost_photons in range(self.backend.n_photons + 1):
            kraus_operators[lost_photons] = np.zeros((self.backend.hilbert_dimension, self.backend.hilbert_dimension))

            for rank in self.backend.occupied_ranks:
                basis_element = rank_to_basis(self.backend.n_wires, self.backend.n_photons, rank)
                photons_in_wire = basis_element[self.reindexed_wire]

                if lost_photons <= photons_in_wire:
                    new_basis_element = [n if wire != self.reindexed_wire else n - lost_photons for wire, n in enumerate(basis_element)]
                    new_rank = basis_to_rank(new_basis_element)

                    kraus_operators[lost_photons][new_rank, rank] = np.sqrt(math.comb(photons_in_wire, lost_photons))*self.eta**((photons_in_wire - lost_photons)/2)*(1 - self.eta)**(lost_photons / 2)
        return kraus_operators
    
class FockDetector(Detector):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def apply(self):
        reindexed_wires = [w-1 for w in self.wires]
        for rank in self.backend.occupied_ranks:
            basis_element = np.array(rank_to_basis(self.backend.n_wires, self.backend.n_photons, rank))
            keep = np.all(basis_element[reindexed_wires] == self.herald)
            if not keep:
                self.backend.density_matrix[rank, :] = 0
                self.backend.density_matrix[:, rank] = 0