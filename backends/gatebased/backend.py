from abc import ABC, abstractmethod

class Backend(ABC):
    def __init__(self, n_qubits):

        if n_qubits < 1:
            raise ValueError("No qubits in the circuit.")

        self.n_qubits = n_qubits

        self.hilbert_dimension = 2**self.n_qubits

        self.component_list = []

    @abstractmethod
    def run(self):
        raise NotImplementedError
    
    def add_component(self, comp):
        self.component_list.append(comp)

    @abstractmethod
    def add_Xgate(self, **kwargs):
        raise NotImplementedError
    
    @abstractmethod
    def add_Ygate(self, **kwargs):
        raise NotImplementedError
    
    @abstractmethod
    def add_Zgate(self, **kwargs):
        raise NotImplementedError
    
    @abstractmethod
    def add_hadamard(self, **kwargs):
        raise NotImplementedError

    @abstractmethod
    def set_input_state(self, input_basis_element):
        pass

