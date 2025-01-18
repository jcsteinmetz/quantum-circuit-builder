from abc import ABC, abstractmethod
from backends.utils import calculate_fock_hilbert_dimension

class PhotonicBackend(ABC):
    def __init__(self, n_wires, n_photons):

        if n_wires < 1:
            raise ValueError("No wires in the circuit.")

        self.n_wires = n_wires
        self.n_photons = n_photons

        self.hilbert_dimension = calculate_fock_hilbert_dimension(self.n_wires, self.n_photons)

        self.component_list = []

    @abstractmethod
    def run(self):
        raise NotImplementedError
    
    def add_component(self, comp):
        self.component_list.append(comp)

    @abstractmethod
    def add_beamsplitter(self, **kwargs):
        raise NotImplementedError
    
    @abstractmethod
    def add_switch(self, **kwargs):
        raise NotImplementedError
    
    @abstractmethod
    def add_phaseshift(self, **kwargs):
        raise NotImplementedError
    
    @abstractmethod
    def add_loss(self, **kwargs):
        raise NotImplementedError
    
    @abstractmethod
    def add_detector(self, **kwargs):
        raise NotImplementedError

    @abstractmethod
    def set_input_state(self, input_basis_element):
        pass

class GateBasedBackend(ABC):
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
    def add_CNOT(self, **kwargs):
        raise NotImplementedError

    @abstractmethod
    def set_input_state(self, input_basis_element):
        pass

    @property
    @abstractmethod
    def output_data(self):
        pass