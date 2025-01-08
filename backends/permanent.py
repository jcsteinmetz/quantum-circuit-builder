"""
Basic simulation based on matrix permanents
"""

import itertools
import scipy
import math
import numpy as np
from backends.backend import Backend
from backends.components.beamsplitter import BeamSplitter
from backends.components.switch import Switch
from backends.components.detector import Detector
from backends.components.phaseshift import PhaseShift
from backends.components.loss import Loss
from backends.utils import rank_to_basis, spin_y_matrix


class Permanent(Backend):
    def __init__(self, n_wires, n_photons):
        super().__init__(n_wires, n_photons)

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
    def output_data(self):
        prob_vector = self.output_probabilities

        table_length = np.count_nonzero(prob_vector)
        table_data = np.zeros((table_length, 2), dtype=object)
        for row, rank in enumerate(np.nonzero(prob_vector)[0]):
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