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
    component_registry = {
        "beamsplitter": None,
        "switch": None,
        "phaseshift": None,
        "loss": None,
        "detector": None,
    }

    def __init__(self, n_wires, n_photons):
        super().__init__()

        if n_wires < 1:
            raise ValueError("No wires in the circuit.")

        self.n_wires = n_wires
        self.n_photons = n_photons

    @property
    def hilbert_dimension(self):
        return fock_hilbert_dimension(self.n_wires, self.n_photons)

    def add_beamsplitter(self, **kwargs):
        component_type = self.component_registry["beamsplitter"]
        comp = component_type(self, **kwargs)
        self.add_component(comp)

    def add_switch(self, **kwargs):
        component_type = self.component_registry["switch"]
        comp = component_type(self, **kwargs)
        self.add_component(comp)

    def add_phaseshift(self, **kwargs):
        component_type = self.component_registry["phaseshift"]
        comp = component_type(self, **kwargs)
        self.add_component(comp)

    def add_loss(self, **kwargs):
        component_type = self.component_registry["loss"]
        comp = component_type(self, **kwargs)
        self.add_component(comp)

    def add_detector(self, **kwargs):
        component_type = self.component_registry["detector"]
        comp = component_type(self, **kwargs)
        self.add_component(comp)


class GateBasedBackend(BaseBackend):
    """
    Template for gate-based backends, where operations are performed on qubits
    using logic gates. The basis states are computational states, i.e. lists of
    zeros and ones.
    """
    component_registry = {
        "Xgate": None,
        "Ygate": None,
        "Zgate": None,
        "hadamard": None,
        "CNOT": None,
    }
    def __init__(self, n_qubits):
        super().__init__()

        if n_qubits < 1:
            raise ValueError("No qubits in the circuit.")

        self.n_qubits = n_qubits

    @property
    def hilbert_dimension(self):
        return 2**self.n_qubits

    def add_Xgate(self, **kwargs):
        component_type = self.component_registry["xgate"]
        comp = component_type(self, **kwargs)
        self.add_component(comp)

    def add_Ygate(self, **kwargs):
        component_type = self.component_registry["ygate"]
        comp = component_type(self, **kwargs)
        self.add_component(comp)

    def add_Zgate(self, **kwargs):
        component_type = self.component_registry["zgate"]
        comp = component_type(self, **kwargs)
        self.add_component(comp)

    def add_hadamard(self, **kwargs):
        component_type = self.component_registry["hadamard"]
        comp = component_type(self, **kwargs)
        self.add_component(comp)

    def add_CNOT(self, **kwargs):
        component_type = self.component_registry["cnot"]
        comp = component_type(self, **kwargs)
        self.add_component(comp)