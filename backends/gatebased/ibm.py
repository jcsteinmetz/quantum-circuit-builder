from qiskit import QuantumCircuit, transpile
from qiskit_aer.aerprovider import AerSimulator
import numpy as np
from backends.backend import GateBasedBackend
from backends.gatebased.components import SingleQubitGate, TwoQubitGate
from backends.utils import bloch_to_rho

class IBM(GateBasedBackend):
    def __init__(self, n_qubits):
        super().__init__(n_qubits)
        self.circuit = QuantumCircuit(self.n_qubits)
        self.density_matrix = None

    def set_input_state(self, input_basis_element):
        self.set_density_matrix(input_basis_element)

    def set_density_matrix(self, input_basis_element):
        for qubit_state in input_basis_element:
            if qubit_state not in [0, 1]:
                raise ValueError("Input state must consist of 0s and 1s.")

        input_z = [1 if qubit_state == 0 else -1 for qubit_state in input_basis_element]
        self.density_matrix = bloch_to_rho([0, 0, input_z[0]])
        for qubit in reversed(range(1, self.n_qubits)): # qiskit uses a reversed tensor product space
            self.density_matrix = np.kron(self.density_matrix, bloch_to_rho([0, 0, input_z[qubit]]))

        self.circuit.set_density_matrix(self.density_matrix)

    def run(self):
        # add the components
        for comp in self.component_list:
            comp.apply()

        # choose a qiskit backend
        simulator = AerSimulator(method='density_matrix')
        self.circuit = transpile(self.circuit, simulator)
        self.circuit.save_state()

        result = simulator.run(self.circuit).result()
        self.density_matrix = result.data().get('density_matrix')

    def add_Xgate(self, **kwargs):
        comp = IBMXGate(self, **kwargs)
        self.add_component(comp)

    def add_Ygate(self, **kwargs):
        comp = IBMYGate(self, **kwargs)
        self.add_component(comp)

    def add_Zgate(self, **kwargs):
        comp = IBMZGate(self, **kwargs)
        self.add_component(comp)

    def add_hadamard(self, **kwargs):
        comp = IBMHadamard(self, **kwargs)
        self.add_component(comp)

    def add_CNOT(self, **kwargs):
        comp = IBMCNOT(self, **kwargs)
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
            binary = bin(rank)[2:].zfill(self.n_qubits)
            basis_element_string = str(binary[::-1]) # qiskit uses a reversed tensor product space
            basis_element_string = basis_element_string.replace("(", "")
            basis_element_string = basis_element_string.replace(")", "")
            basis_element_string = basis_element_string.replace(" ", "")
            basis_element_string = basis_element_string.replace(",", "")
            table_data[row, 0] = "".join(basis_element_string)
            table_data[row, 1] = prob_vector[rank]

        return table_data

class IBMXGate(SingleQubitGate):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def apply(self):
        self.backend.circuit.x(self.reindexed_targeted_qubit)

class IBMYGate(SingleQubitGate):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def apply(self):
        self.backend.circuit.y(self.reindexed_targeted_qubit)

class IBMZGate(SingleQubitGate):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def apply(self):
        self.backend.circuit.z(self.reindexed_targeted_qubit)

class IBMHadamard(SingleQubitGate):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def apply(self):
        self.backend.circuit.h(self.reindexed_targeted_qubit)

class IBMCNOT(TwoQubitGate):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def apply(self):
        self.backend.circuit.cx(self.reindexed_targeted_qubits[0], self.reindexed_targeted_qubits[1])