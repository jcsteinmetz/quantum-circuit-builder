from qiskit import QuantumCircuit, transpile
from qiskit_aer.aerprovider import AerSimulator
import numpy as np
from backends.backend import GateBasedBackend
from backends.gatebased.components import PauliGate, Hadamard, CNOT
from backends.utils import computational_basis_to_rho, tuple_to_str

class QiskitBackend(GateBasedBackend):
    def __init__(self, n_qubits):
        super().__init__(n_qubits)

        # Register components
        self.register_component("xgate", QiskitXGate)
        self.register_component("ygate", QiskitYGate)
        self.register_component("zgate", QiskitZGate)
        self.register_component("hadamard", QiskitHadamard)
        self.register_component("cnot", QiskitCNOT)

        self.circuit = QuantumCircuit(self.n_qubits)
        self.density_matrix = None

    def set_input_state(self, input_basis_element):
        self.density_matrix = computational_basis_to_rho(input_basis_element[0])
        for qubit in reversed(range(1, self.n_qubits)): # qiskit uses a reversed tensor product space
            self.density_matrix = np.kron(self.density_matrix, computational_basis_to_rho(input_basis_element[qubit]))

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
        return [tuple_to_str(self.rank_to_basis(rank)[::-1]) for rank in self.occupied_ranks] # qiskit uses a reversed tensor product space

class QiskitXGate(PauliGate):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def apply(self):
        self.backend.circuit.x(self.reindexed_targeted_qubit)

class QiskitYGate(PauliGate):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def apply(self):
        self.backend.circuit.y(self.reindexed_targeted_qubit)

class QiskitZGate(PauliGate):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def apply(self):
        self.backend.circuit.z(self.reindexed_targeted_qubit)

class QiskitHadamard(Hadamard):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def apply(self):
        self.backend.circuit.h(self.reindexed_targeted_qubit)

class QiskitCNOT(CNOT):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def apply(self):
        self.backend.circuit.cx(self.reindexed_targeted_qubits[0], self.reindexed_targeted_qubits[1])