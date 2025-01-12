"""
Placeholder backend
"""

from backends.backend import Backend

class Placeholder(Backend):
    def __init__(self, n_wires, n_photons):
        super().__init__(n_wires, n_photons)

    def set_input_state(self, input_basis_element):
        pass

    def run(self):
        raise NotImplementedError("This backend is a placeholder and doesn't do anything.")

    def add_beamsplitter(self, **kwargs):
        pass

    def add_switch(self, **kwargs):
        pass

    def add_phaseshift(self, **kwargs):
        pass

    def add_loss(self, **kwargs):
        pass

    def add_detector(self, **kwargs):
        pass