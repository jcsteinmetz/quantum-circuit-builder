"""
Contains backend templates.
"""

from abc import ABC, abstractmethod
from backends.utils import fock_hilbert_dimension

class BaseBackend(ABC):
    """
    Base class for simulator backends.
    """
    def __init__(self):
        self.component_list = []

    def add_component(self, comp):
        """
        Add a component to the circuit.
        """
        self.component_list.append(comp)

    @property
    @abstractmethod
    def hilbert_dimension(self):
        pass

    @abstractmethod
    def set_input_state(self, input_basis_element):
        pass

    @abstractmethod
    def get_output_data(self):
        pass

    @abstractmethod
    def run(self):
        raise NotImplementedError


class PhotonicBackend(BaseBackend):
    """
    Template for photonic backends, where photons move through a circuit containing linear
    optical components. This allows dual-rail qubits, but also non-computational states.
    The basis states are Fock states, (n_1, n_2, ..., n_M), where each n_i is the occupation
    number for mode i.
    """
    def __init__(self, n_wires, n_photons):
        super().__init__()

        if n_wires < 1:
            raise ValueError("No wires in the circuit.")

        self.n_wires = n_wires
        self.n_photons = n_photons

    @property
    def hilbert_dimension(self):
        return fock_hilbert_dimension(self.n_wires, self.n_photons)

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


class GateBasedBackend(BaseBackend):
    """
    Template for gate-based backends, where operations are performed on qubits
    using logic gates. The basis states are computational states, i.e. lists of
    zeros and ones.
    """
    def __init__(self, n_qubits):
        super().__init__()

        if n_qubits < 1:
            raise ValueError("No qubits in the circuit.")

        self.n_qubits = n_qubits

    @property
    def hilbert_dimension(self):
        return 2**self.n_qubits

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