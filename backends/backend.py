"""
Contains backend templates.
"""

from abc import ABC, abstractmethod
from backends.utils import fock_hilbert_dimension, fill_table, rank_to_fock_basis, fock_basis_to_rank

class BaseBackend(ABC):
    """Base class for simulator backends."""
    _component_registry = {}

    def __init__(self):
        self.component_list = []

    @classmethod
    def register_component(cls, component_type, component_class):
        """Connect a component type with its class in a particular backend."""
        cls._component_registry[component_type] = component_class

    def add_component_by_type(self, component_type, **kwargs):
        """Add an arbitrary component to the simulation."""
        component_type = self._component_registry[component_type]
        component = component_type(self, **kwargs)
        self.component_list.append(component)

    def get_output_data(self):
        """Returns a 2-column array containing basis elements and their probabilities."""
        return fill_table(self.basis_strings, self.nonzero_probabilities)

    @abstractmethod
    def rank_to_basis(self, rank):
        """Returns a basis element given its rank (its position in the ordered list of elements)."""
        raise NotImplementedError

    @abstractmethod
    def basis_to_rank(self, basis_element):
        """Returns a basis element's position in the space."""
        raise NotImplementedError

    @property
    @abstractmethod
    def basis_strings(self):
        """String representations of nonzero basis elements, ex. '0101'."""
        raise NotImplementedError
    
    @property
    @abstractmethod
    def nonzero_probabilities(self):
        """Probabilities associated with nonzero basis elements, in the same order as basis_strings."""
        raise NotImplementedError

    @property
    @abstractmethod
    def hilbert_dimension(self):
        """Dimension of the Hilbert space."""
        pass

    @abstractmethod
    def set_input_state(self, input_basis_element):
        """
        Assign an input state to the simulation.

        input_basis_element (list): a single basis element, ex. [0, 1, 0, 1].
        """
        self.validate_input_state(input_basis_element)

    @abstractmethod
    def run(self):
        """Run the simulation."""
        raise NotImplementedError
    
    @abstractmethod
    def validate_input_state(self, input_basis_element):
        pass


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
    
    def validate_input_state(self, input_basis_element):
        if not isinstance(input_basis_element, tuple):
            raise TypeError("Input state must be a tuple.")
        if len(input_basis_element) != self.n_wires:
            raise ValueError(f"Input state must contain exactly {self.n_wires} elements.")
        if not all(isinstance(occupation_number, int) for occupation_number in input_basis_element):
            raise TypeError("All elements in input state must be integers.")
        if not all(0 <= occupation_number <= self.n_photons for occupation_number in input_basis_element):
            raise ValueError(f"Occupation numbers must be between 0 and {self.n_photons}.")
    
    def rank_to_basis(self, rank):
        """Returns a Fock basis element given its rank in the space."""
        return rank_to_fock_basis(self.n_wires, self.n_photons, rank)
    
    def basis_to_rank(self, basis_element):
        """Returns a Fock basis element's rank."""
        return fock_basis_to_rank(basis_element)
    
    # Add components

    def add_beamsplitter(self, **kwargs):
        self.add_component_by_type("beamsplitter", **kwargs)

    def add_switch(self, **kwargs):
        self.add_component_by_type("switch", **kwargs)

    def add_phaseshift(self, **kwargs):
        self.add_component_by_type("phaseshift", **kwargs)

    def add_loss(self, **kwargs):
        self.add_component_by_type("loss", **kwargs)

    def add_detector(self, **kwargs):
        self.add_component_by_type("detector", **kwargs)


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
    
    def validate_input_state(self, input_basis_element):
        if not isinstance(input_basis_element, tuple):
            raise TypeError("Input state must be a tuple.")
        if len(input_basis_element) != self.n_qubits:
            raise ValueError(f"Input state must contain exactly {self.n_qubits} elements.")
        if not all(isinstance(qubit_state, int) for qubit_state in input_basis_element):
            raise TypeError("All elements in input state must be integers.")
        if not all(qubit_state in [0, 1] for qubit_state in input_basis_element):
            raise ValueError("Each qubit's state must be either 0 or 1.")
    
    def rank_to_basis(self, rank):
        """Returns a computational basis element given its rank in the space by converting decimal to binary."""
        return bin(rank)[2:].zfill(self.n_qubits)
    
    def basis_to_rank(self, basis_element):
        pass
    
    # Add components

    def add_xgate(self, **kwargs):
        self.add_component_by_type("xgate", **kwargs)

    def add_ygate(self, **kwargs):
        self.add_component_by_type("ygate", **kwargs)

    def add_zgate(self, **kwargs):
        self.add_component_by_type("zgate", **kwargs)

    def add_hadamard(self, **kwargs):
        self.add_component_by_type("hadamard", **kwargs)

    def add_cnot(self, **kwargs):
        self.add_component_by_type("cnot", **kwargs)