from backends.backend import Backend
import strawberryfields as sf
from strawberryfields.ops import Fock, Vac, BSgate
import numpy as np
from backends.utils import degrees_to_radians

class Xanadu(Backend):
    def __init__(self, n_wires, n_photons):
        super().__init__(n_wires, n_photons)

        self.eng = sf.Engine("fock", backend_options={"cutoff_dim": 10})
        self.state = State(self.n_wires, self.n_photons)

        self.component_list = []

    def run(self):
        for comp in self.component_list:
            comp.apply()

        results = self.eng.run(self.state.prog)
        self.state.output_probabilities = results.state.all_fock_probs()

    def set_input_state(self, input_basis_label):
        self.state.set_program_input(input_basis_label)

    @property
    def output_data(self):
        return self.state.output_probabilities
    
    def add_beamsplitter(self, **kwargs):
        comp = BeamSplitter(self.state.prog, **kwargs)
        self.component_list.append(comp)
    
    def add_switch(self, **kwargs):
        raise NotImplementedError
    
    def add_loss(self, **kwargs):
        raise NotImplementedError
    
    def add_detector(self, **kwargs):
        raise NotImplementedError

class State:
    def __init__(self, n_wires, n_photons):
        self.n_wires = n_wires
        self.n_photons = n_photons

        self.prog = sf.Program(self.n_wires)

        self.output_probabilities = None

    def set_program_input(self, input_basis_element):
        with self.prog.context as q:
            for wire, n_photons in enumerate(input_basis_element):
                if n_photons == 0:
                    Vac | q[wire]
                else:
                    Fock(n_photons) | q[wire]

class BeamSplitter:
    def __init__(self, prog, *, wires, theta = 90):
        self.prog = prog
        self.wires = wires
        self.theta = degrees_to_radians(theta) / 2 # to match Xanadu's convention
        self.reindexed_wires = [wire - 1 for wire in self.wires]

    def apply(self):
        with self.prog.context as q:
            BSgate(self.theta, np.pi/2) | (q[self.reindexed_wires[0]], q[self.reindexed_wires[1]])