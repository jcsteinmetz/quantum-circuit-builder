"""
Basic matrix product model
"""

import numpy as np
from backends.gatebased.components.single_qubit_gate import SingleQubitGate
from backends.utils import bloch_to_rho, pauli
from backends.gatebased.backend import Backend

class MatrixProduct(Backend):
    def __init__(self, n_qubits):
        super().__init__(n_qubits)

        self.density_matrix = None

    def set_input_state(self, input_basis_element):
        self.set_density_matrix(input_basis_element)

    def run(self):
        for comp in self.component_list:
            comp.apply()
            self.eliminate_tolerance()

    def add_Xgate(self, **kwargs):
        comp = MatrixProductXGate(self, **kwargs)
        self.add_component(comp)

    def add_Ygate(self, **kwargs):
        comp = MatrixProductYGate(self, **kwargs)
        self.add_component(comp)

    def add_Zgate(self, **kwargs):
        comp = MatrixProductZGate(self, **kwargs)
        self.add_component(comp)

    def add_hadamard(self, **kwargs):
        comp = MatrixProductHadamard(self, **kwargs)
        self.add_component(comp)

    @property
    def occupied_ranks(self):
        return [rank for rank in range(self.hilbert_dimension) if self.density_matrix[rank, rank] != 0]
    
    @property
    def output_data(self):
        prob_vector = np.real(self.density_matrix.diagonal())
        table_length = np.count_nonzero(prob_vector)
        table_data = np.zeros((table_length, 2), dtype=object)
        for row, rank in enumerate(self.occupied_ranks):
            basis_element_string = str(bin(rank)[2:].zfill(self.n_qubits))
            basis_element_string = basis_element_string.replace("(", "")
            basis_element_string = basis_element_string.replace(")", "")
            basis_element_string = basis_element_string.replace(" ", "")
            basis_element_string = basis_element_string.replace(",", "")
            table_data[row, 0] = "".join(basis_element_string)
            table_data[row, 1] = prob_vector[rank]

        return table_data

    def set_density_matrix(self, input_basis_element):
        for qubit_state in input_basis_element:
            if qubit_state not in [0, 1]:
                raise ValueError("Input state must consist of 0s and 1s.")

        input_z = [1 if qubit_state == 0 else -1 for qubit_state in input_basis_element]
        self.density_matrix = bloch_to_rho([0, 0, input_z[0]])
        for qubit in range(1, self.n_qubits):
            self.density_matrix = np.kron(self.density_matrix, bloch_to_rho([0, 0, input_z[qubit]]))
        
    def eliminate_tolerance(self, tol=1E-10):
        self.density_matrix[np.abs(self.density_matrix) < tol] = 0

class MatrixProductXGate(SingleQubitGate):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.single_qubit_unitary = pauli([1, 0, 0])

class MatrixProductYGate(SingleQubitGate):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.single_qubit_unitary = pauli([0, 1, 0])

class MatrixProductZGate(SingleQubitGate):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.single_qubit_unitary = pauli([0, 0, 1])

class MatrixProductHadamard(SingleQubitGate):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.single_qubit_unitary = (1/np.sqrt(2))*np.array([[1, 1], [1, -1]], dtype=complex)