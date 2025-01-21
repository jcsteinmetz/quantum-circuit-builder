"""
Basic matrix product model
"""

import numpy as np
from abc import abstractmethod
from backends.utils import insert_gate, pauli_x, pauli_y, pauli_z, computational_basis_to_rho, tuple_to_str
from backends.backend import GateBasedBackend
from backends.component import Component

class MPBackend(GateBasedBackend):
    def __init__(self, n_qubits):
        super().__init__(n_qubits)

        # Register components
        self.register_component("xgate", MPXGate)
        self.register_component("ygate", MPYGate)
        self.register_component("zgate", MPZGate)
        self.register_component("hadamard", MPHadamard)
        self.register_component("cnot", MPCNOT)

        self.density_matrix = None

    def set_input_state(self, input_basis_element):
        self.density_matrix = self.create_density_matrix(input_basis_element)
        
    def create_density_matrix(self, input_basis_element):
        density_matrix = computational_basis_to_rho(input_basis_element[0])
        for qubit in range(1, self.n_qubits):
            density_matrix = np.kron(density_matrix, computational_basis_to_rho(input_basis_element[qubit]))
        return density_matrix

    def run(self):
        for comp in self.component_list:
            comp.apply()
            self.eliminate_tolerance()

    @property
    def probabilities(self):
        return np.real(self.density_matrix.diagonal())
    
    @property
    def occupied_ranks(self):
        return np.nonzero(self.probabilities)[0]
    
    @property
    def nonzero_probabilities(self):
        return self.probabilities[self.occupied_ranks]
    
    @property
    def basis_strings(self):
        return [tuple_to_str(self.rank_to_basis(rank)) for rank in self.occupied_ranks]
        
    def eliminate_tolerance(self, tol=1E-10):
        self.density_matrix[np.abs(self.density_matrix) < tol] = 0

class MPComponent(Component):
    def __init__(self, backend, qubits):
        super().__init__(backend)

        self.targeted_qubits = qubits
        self.reindexed_targeted_qubits = [q - 1 for q in qubits]

    def apply(self):
        unitary = self.unitary()
        self.backend.density_matrix = unitary @ self.backend.density_matrix @ np.conjugate(unitary).T

    @abstractmethod
    def unitary(self):
        raise NotImplementedError

class MPXGate(MPComponent):
    def __init__(self, backend, *, qubits):
        super().__init__(backend, qubits)

    @property
    def single_qubit_unitary(self):
        return pauli_x()

    def unitary(self):
        return insert_gate(self.single_qubit_unitary, self.reindexed_targeted_qubits[0], self.backend.n_qubits)

class MPYGate(MPComponent):
    def __init__(self, backend, *, qubits):
        super().__init__(backend, qubits)

    @property
    def single_qubit_unitary(self):
        return pauli_y()

    def unitary(self):
        return insert_gate(self.single_qubit_unitary, self.reindexed_targeted_qubits[0], self.backend.n_qubits)

class MPZGate(MPComponent):
    def __init__(self, backend, *, qubits):
        super().__init__(backend, qubits)

    @property
    def single_qubit_unitary(self):
        return pauli_z()

    def unitary(self):
        return insert_gate(self.single_qubit_unitary, self.reindexed_targeted_qubits[0], self.backend.n_qubits)

class MPHadamard(MPComponent):
    def __init__(self, backend, *, qubits):
        super().__init__(backend, qubits)

    @property
    def single_qubit_unitary(self):
        return (1/np.sqrt(2))*np.array([[1, 1], [1, -1]], dtype=complex)

    def unitary(self):
        return insert_gate(self.single_qubit_unitary, self.reindexed_targeted_qubits[0], self.backend.n_qubits)

class MPCNOT(MPComponent):
    def __init__(self, backend, *, qubits):
        super().__init__(backend, qubits)

    def unitary(self):
        control_qubit = self.reindexed_targeted_qubits[0]
        target_qubit = self.reindexed_targeted_qubits[1]

        control_is_zero = np.array([[1, 0], [0, 0]], dtype=complex)
        control_is_one = np.array([[0, 0], [0, 1]], dtype=complex)

        # Operation conditioned on the control qubit being zero
        project_control_onto_zero = insert_gate(control_is_zero, control_qubit, self.backend.n_qubits)

        # Operation conditioned on the control qubit being one
        project_control_onto_one = insert_gate(control_is_one, control_qubit, self.backend.n_qubits)
        flip_target = insert_gate(pauli_x(), target_qubit, self.backend.n_qubits)

        return project_control_onto_zero + project_control_onto_one @ flip_target