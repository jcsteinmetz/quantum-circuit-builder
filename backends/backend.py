from abc import ABC, abstractmethod

class Backend(ABC):
    def __init__(self, n_wires, n_photons):

        if n_wires < 1:
            raise ValueError("No wires in the circuit.")

        self.n_wires = n_wires
        self.n_photons = n_photons

    @abstractmethod
    def run(self):
        raise NotImplementedError

    @abstractmethod
    def add_beamsplitter(self, **kwargs):
        raise NotImplementedError
    
    @abstractmethod
    def add_switch(self, **kwargs):
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