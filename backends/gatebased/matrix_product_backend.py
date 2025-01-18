"""
Basic matrix product model
"""

import numpy as np
from backends.utils import insert_gate, pauli_x, pauli_y, pauli_z, computational_basis_to_rho, tuple_to_str
from backends.backend import GateBasedBackend
from backends.gatebased.components import SingleQubitGate, TwoQubitGate

class MPBackend(GateBasedBackend):
    def __init__(self, n_qubits):
        super().__init__(n_qubits)

        # Register components
        self.component_registry["xgate"] = MPXGate
        self.component_registry["ygate"] = MPYGate
        self.component_registry["zgate"] = MPZGate
        self.component_registry["hadamard"] = MPHadamard
        self.component_registry["cnot"] = MPCNOT

        self.density_matrix = None

    def set_input_state(self, input_basis_element):
        self.set_density_matrix(input_basis_element)

    def run(self):
        for comp in self.component_list:
            comp.apply()
            self.eliminate_tolerance()

    @property
    def occupied_ranks(self):
        return [rank for rank in range(self.hilbert_dimension) if self.density_matrix[rank, rank] != 0]
    
    def get_output_data(self):
        prob_vector = np.real(self.density_matrix.diagonal())
        table_length = np.count_nonzero(prob_vector)
        table_data = np.zeros((table_length, 2), dtype=object)
        for row, rank in enumerate(self.occupied_ranks):
            basis_element = bin(rank)[2:].zfill(self.n_qubits)
            table_data[row, 0] = tuple_to_str(basis_element)
            table_data[row, 1] = prob_vector[rank]

        return table_data

    def set_density_matrix(self, input_basis_element):
        self.density_matrix = computational_basis_to_rho(input_basis_element[0])
        for qubit in range(1, self.n_qubits):
            self.density_matrix = np.kron(self.density_matrix, computational_basis_to_rho(input_basis_element[qubit]))
        
    def eliminate_tolerance(self, tol=1E-10):
        self.density_matrix[np.abs(self.density_matrix) < tol] = 0

class MPXGate(SingleQubitGate):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    @property
    def single_qubit_unitary(self):
        return pauli_x()

    def apply(self):
        unitary = self.unitary()
        self.backend.density_matrix = unitary @ self.backend.density_matrix @ np.conjugate(unitary).T

    def unitary(self):
        return insert_gate(self.single_qubit_unitary, self.reindexed_targeted_qubit, self.backend.n_qubits)

class MPYGate(SingleQubitGate):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    @property
    def single_qubit_unitary(self):
        return pauli_y()

    def apply(self):
        unitary = self.unitary()
        self.backend.density_matrix = unitary @ self.backend.density_matrix @ np.conjugate(unitary).T

    def unitary(self):
        return insert_gate(self.single_qubit_unitary, self.reindexed_targeted_qubit, self.backend.n_qubits)

class MPZGate(SingleQubitGate):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    @property
    def single_qubit_unitary(self):
        return pauli_z()

    def apply(self):
        unitary = self.unitary()
        self.backend.density_matrix = unitary @ self.backend.density_matrix @ np.conjugate(unitary).T

    def unitary(self):
        return insert_gate(self.single_qubit_unitary, self.reindexed_targeted_qubit, self.backend.n_qubits)

class MPHadamard(SingleQubitGate):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    @property
    def single_qubit_unitary(self):
        return (1/np.sqrt(2))*np.array([[1, 1], [1, -1]], dtype=complex)

    def apply(self):
        unitary = self.unitary()
        self.backend.density_matrix = unitary @ self.backend.density_matrix @ np.conjugate(unitary).T

    def unitary(self):
        return insert_gate(self.single_qubit_unitary, self.reindexed_targeted_qubit, self.backend.n_qubits)

class MPCNOT(TwoQubitGate):
    """
    CNOT gate is a sum of do_nothing when the control qubit is 0, and flip_target when the control qubit is 1.
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

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
    
    def apply(self):
        unitary = self.unitary()
        self.backend.density_matrix = unitary @ self.backend.density_matrix @ np.conjugate(unitary).T