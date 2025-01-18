"""
Basic simulation based on matrix permanents
"""

import itertools
import scipy
import math
import numpy as np
from backends.backend import PhotonicBackend
from backends.photonic.components import BeamSplitter, Switch, PhaseShift, Loss, Detector
from backends.utils import rank_to_basis, spin_y_matrix, tuple_to_str, fill_table


class PermanentBackend(PhotonicBackend):
    def __init__(self, n_wires, n_photons):
        super().__init__(n_wires, n_photons)

        # Register components
        self.component_registry["beamsplitter"] = PermanentBeamSplitter
        self.component_registry["switch"] = PermanentSwitch
        self.component_registry["phaseshift"] = PermanentPhaseShift
        self.component_registry["loss"] = PermanentLoss
        self.component_registry["detector"] = PermanentDetector

        self.input_basis_element = ()
        self.output_probabilities = np.zeros(self.hilbert_dimension)

        self.circuit_unitary = np.eye(self.n_wires)

    def set_input_state(self, input_basis_element):
        self.input_basis_element = input_basis_element

    def run(self):
        for comp in self.component_list:
            if not isinstance(comp, PermanentDetector):
                comp.apply()

        for rank in range(self.hilbert_dimension):
            output_basis_element = rank_to_basis(self.n_wires, self.n_photons, rank)
            self.output_probabilities[rank] = self.output_probability(self.circuit_unitary, output_basis_element)

        for comp in self.component_list:
            if isinstance(comp, PermanentDetector):
                comp.apply()

        self.eliminate_tolerance()

    def output_probability(self, circuit_unitary, output_basis_element):
        circuit_submatrix = self.submatrix(circuit_unitary, output_basis_element)
        norm_input = np.prod([math.factorial(n) for n in self.input_basis_element])
        norm_output = np.prod([math.factorial(n) for n in output_basis_element])
        return np.abs(self.matrix_permanent(circuit_submatrix))**2/(norm_input * norm_output)

    def submatrix(self, circuit_unitary, output_basis_element):
        UT = np.zeros((self.n_wires, self.n_photons), dtype=complex)
        used_photons = 0
        for j, tj in enumerate(self.input_basis_element):
            for n in range(used_photons, used_photons + tj):
                UT[:, n] = circuit_unitary[:, j]
            used_photons += tj

        used_photons = 0
        UST = np.zeros((self.n_photons, self.n_photons), dtype=complex)
        for i, si in enumerate(output_basis_element):
            for n in range(used_photons, used_photons + si):
                UST[n, :] = UT[i, :]
            used_photons += si

        return UST

    def add_beamsplitter(self, **kwargs):
        comp = PermanentBeamSplitter(self, **kwargs)
        self.add_component(comp)

    def add_switch(self, **kwargs):
        comp = PermanentSwitch(self, **kwargs)
        self.add_component(comp)

    def add_phaseshift(self, **kwargs):
        comp = PermanentPhaseShift(self, **kwargs)
        self.add_component(comp)

    def add_loss(self, **kwargs):
        comp = PermanentLoss(self, **kwargs)
        self.add_component(comp)

    def add_detector(self, **kwargs):
        comp = PermanentDetector(self, **kwargs)
        self.add_component(comp)
        
    def matrix_permanent(self, matrix):
        n = len(matrix)
        perms = itertools.permutations(range(n))
        total = 0
        for perm in perms:
            product = 1
            for i in range(n):
                product *= matrix[i, perm[i]]
            total += product
        return total
    
    @property
    def probabilities(self):
        return self.output_probabilities
    
    @property
    def occupied_ranks(self):
        return np.nonzero(self.probabilities)[0]
    
    @property
    def nonzero_probabilities(self):
        return self.probabilities[self.occupied_ranks]
    
    @property
    def basis_strings(self):
        return [tuple_to_str(rank_to_basis(self.n_wires, self.n_photons, rank)) for rank in self.occupied_ranks]
    
    def eliminate_tolerance(self, tol=1E-10):
        self.output_probabilities[np.abs(self.output_probabilities) < tol] = 0

class PermanentBeamSplitter(BeamSplitter):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def apply(self):
        unitary = self.unitary()
        self.backend.circuit_unitary = unitary @ self.backend.circuit_unitary

    def unitary(self):
        unitary = np.eye(self.backend.n_wires, dtype=complex)
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


class PermanentSwitch(Switch):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def apply(self):
        unitary = self.unitary()
        self.backend.circuit_unitary = unitary @ self.backend.circuit_unitary

    def unitary(self):
        unitary = np.eye(self.backend.n_wires, dtype=complex)
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


class PermanentPhaseShift(PhaseShift):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def apply(self):
        unitary = self.unitary()
        self.backend.circuit_unitary = unitary @ self.backend.circuit_unitary

    def unitary(self):
        unitary = np.eye(self.backend.n_wires, dtype=complex)
        unitary[self.reindexed_wire, self.reindexed_wire] = np.exp(1j*self.phase)
        return unitary


class PermanentLoss(Loss):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def apply(self):
        raise ValueError("Loss is not implemented yet in the permanent backend.")


class PermanentDetector(Detector):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def apply(self):
        reindexed_wires = [w-1 for w in self.wires]
        for rank in range(self.backend.hilbert_dimension):
            basis_element = np.array(rank_to_basis(self.backend.n_wires, self.backend.n_photons, rank))
            keep = np.all(basis_element[reindexed_wires] == self.herald)
            if not keep:
                self.backend.output_probabilities[rank] = 0