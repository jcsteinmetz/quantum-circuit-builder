from backends.backend import PhotonicBackend
from mrmustard.lab import Fock, BSgate, MZgate, Attenuator, Rgate
import mrmustard.math as math
# from mrmustard import settings
import numpy as np
from abc import abstractmethod
from backends.component import Component
from backends.utils import tuple_to_str, degrees_to_radians, eliminate_tolerance

math.change_backend("tensorflow")

class MrMustardBackend(PhotonicBackend):
    def __init__(self, n_wires, n_photons):
        super().__init__(n_wires, n_photons)

        # Register components
        self.register_component("beamsplitter", MrMustardBeamSplitter)
        self.register_component("switch", MrMustardSwitch)
        self.register_component("phaseshift", MrMustardPhaseShift)
        self.register_component("loss", MrMustardLoss)
        self.register_component("detector", MrMustardDetector)

        self.state = None
        self.ket = None
        self.output_probabilities = None

    def run(self):
        for comp in self.component_list:
            comp.apply()

    def set_input_state(self, input_basis_element):
        self.state = Fock(list(input_basis_element), cutoffs = [self.hilbert_dimension]*self.n_wires)

    @property
    def _occupied_ranks(self):
        occ = np.nonzero(self._probabilities)[0]
        return occ
    
    @property
    def _nonzero_probabilities(self):
        return self._probabilities[self._occupied_ranks]
    
    @property
    def _basis_strings(self):
        return [tuple_to_str(self.rank_to_basis(rank)) for rank in self._occupied_ranks]
    
    @property
    def _probabilities(self):
        if self.ket is None:
            self.ket = self.state.ket()

        probs = np.zeros(self.hilbert_dimension)
        for rank in range(self.hilbert_dimension):
            basis_element = self.rank_to_basis(rank)
            if all(0 <= idx < dim_size for idx, dim_size in zip(basis_element, self.ket.shape)):
                probs[rank] = np.abs(self.ket[basis_element])**2

        return eliminate_tolerance(probs)
        

class MrMustardComponent(Component):
    def __init__(self, backend, wires):
        self.wires = wires
        self.reindexed_wires = [w - 1 for w in wires]

        super().__init__(backend)

    @abstractmethod
    def apply(self):
        raise NotImplementedError


class MrMustardBeamSplitter(MrMustardComponent):
    def __init__(self, backend, *, wires, theta=90):
        self.theta = degrees_to_radians(theta)

        super().__init__(backend, wires)

    def validate(self):
        self.validate_beamsplitter(self.wires, self.theta)

    def apply(self):
        self.backend.state = self.backend.state >> BSgate(theta = self.theta/2, modes = self.reindexed_wires)


class MrMustardSwitch(MrMustardComponent):
    def __init__(self, backend, *, wires):
        super().__init__(backend, wires)

    def validate(self):
        self.validate_switch(self.wires)

    def apply(self):
        self.backend.state = self.backend.state >> MZgate(modes = self.reindexed_wires)


class MrMustardPhaseShift(MrMustardComponent):
    def __init__(self, backend, *, wires, phase = 180):

        self.phase = degrees_to_radians(phase)

        super().__init__(backend, wires)

    def validate(self):
        self.validate_phaseshift(self.wires, self.phase)

    def apply(self):
        self.backend.state = self.backend.state >> Rgate(angle = self.phase, modes = self.reindexed_wires)


class MrMustardLoss(MrMustardComponent):
    def __init__(self, backend, *, wires, eta = 1):

        self.eta = eta

        super().__init__(backend, wires)

    def validate(self):
        self.validate_loss(self.wires, self.eta)

    def apply(self):
        raise ValueError("Loss is not implemented yet in the Mr Mustard backend.")
        # self.backend.state = self.backend.state >> Attenuator(self.eta, nbar = 0, modes = self.reindexed_wires)


class MrMustardDetector(MrMustardComponent):
    def __init__(self, backend, *, wires, herald):

        self.herald = herald

        super().__init__(backend, wires)

    def validate(self):
        self.validate_detector(self.wires, self.herald)

    def apply(self):
        self.backend.ket = self.backend.state.ket()

        # post select on herald
        for idx, wire in enumerate(self.wires):
            for n in range(self.backend.n_photons + 1):
                if n != self.herald[idx]:
                    self.backend.ket[(slice(None),) * wire + (n,)] = 0
