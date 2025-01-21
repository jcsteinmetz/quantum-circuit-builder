from backends.backend import PhotonicBackend
import strawberryfields as sf
from strawberryfields.ops import Fock, Vac, BSgate, Interferometer, LossChannel, MeasureFock, Rgate
import numpy as np
from abc import abstractmethod
from backends.component import Component
from backends.utils import tuple_to_str, degrees_to_radians

class SFBackend(PhotonicBackend):
    def __init__(self, n_wires, n_photons):
        super().__init__(n_wires, n_photons)

        # Register components
        self.register_component("beamsplitter", SFBeamSplitter)
        self.register_component("switch", SFSwitch)
        self.register_component("phaseshift", SFPhaseShift)
        self.register_component("loss", SFLoss)
        self.register_component("detector", SFDetector)

        self.eng = sf.Engine("fock", backend_options={"cutoff_dim": self.n_photons+1})
        self.circuit = sf.Program(self.n_wires)
        self.output_probabilities = None

    def run(self):
        for comp in self.component_list:
            comp.apply()

        results = self.eng.run(self.circuit)

        self.output_probabilities = np.real(np.copy(results.state.all_fock_probs()))
        self.eliminate_tolerance()

    def set_input_state(self, input_basis_element):
        super().set_input_state(input_basis_element)
        with self.circuit.context as q:
            for wire, n_photons in enumerate(input_basis_element):
                if n_photons == 0:
                    Vac | q[wire]
                else:
                    Fock(n_photons) | q[wire]
    
    @property
    def occupied_ranks(self):
        return np.nonzero(self.probabilities)[0]
    
    @property
    def nonzero_probabilities(self):
        return self.probabilities[self.occupied_ranks]
    
    @property
    def basis_strings(self):
        return [tuple_to_str(self.rank_to_basis(rank)) for rank in self.occupied_ranks]
    
    @property
    def probabilities(self):
        """
        Strawberry Fields stores density matrix elements in a multidimensional array, where the
        indices are occupation numbers for each wire. For example, output_probabilities[0, 3] is
        the probability of having zero photons in the first wire, and three photons in the second
        wire. This array can also change shape depending on which Fock states have nonzero amplitude.
        
        This function converts these probabilities into the correct format, a vector in
        ascending order by total photon number, sorted in lexicographical order within each number
        sector.
        """
        prob_vector = []

        idx = np.indices(self.output_probabilities.shape)
        idx_sum = np.sum(idx, axis=0)

        # Loop through fixed number sectors
        for n in range(self.n_photons+1):
            # Find probabilities with indices that add to the current photon number
            sector_mask = (idx_sum == n)
            sector_indices = np.argwhere(sector_mask)
            sector_probabilities = self.output_probabilities[tuple(sector_indices.T)]

            prob_vector.extend(sector_probabilities[::-1]) # strawberry fields uses reverse lex order

        return np.array(prob_vector)

    def eliminate_tolerance(self, tol=1E-10):
        self.output_probabilities[np.abs(self.output_probabilities) < tol] = 0

class SFComponent(Component):
    def __init__(self, backend, wires):
        self.wires = wires
        self.reindexed_wires = [w - 1 for w in wires]

        super().__init__(backend)

    @abstractmethod
    def apply(self):
        raise NotImplementedError

class SFBeamSplitter(SFComponent):
    def __init__(self, backend, *, wires, theta=90):
        self.theta = degrees_to_radians(theta)

        super().__init__(backend, wires)

    def validate(self):
        self.validate_beamsplitter(self.wires, self.theta)

    def apply(self):
        with self.backend.circuit.context as q:
            BSgate(self.theta/2, 0) | (q[self.reindexed_wires[0]], q[self.reindexed_wires[1]])

class SFSwitch(SFComponent):
    def __init__(self, backend, *, wires):
        super().__init__(backend, wires)

    def validate(self):
        self.validate_switch(self.wires)

    def apply(self):
        with self.backend.circuit.context as q:
            Interferometer(np.array([[0, 1], [1, 0]])) | (q[self.reindexed_wires[0]], q[self.reindexed_wires[1]])

class SFPhaseShift(SFComponent):
    def __init__(self, backend, *, wires, phase = 180):

        self.phase = degrees_to_radians(phase)

        super().__init__(backend, wires)

    def validate(self):
        self.validate_phaseshift(self.wires, self.phase)

    def apply(self):
        with self.backend.circuit.context as q:
            Rgate(self.phase) | q[self.reindexed_wires[0]]

class SFLoss(SFComponent):
    def __init__(self, backend, *, wires, eta = 1):

        self.eta = eta

        super().__init__(backend, wires)

    def validate(self):
        self.validate_loss(self.wires, self.eta)

    def apply(self):
        with self.backend.circuit.context as q:
            LossChannel(self.eta) | (q[self.reindexed_wires[0]])

class SFDetector(SFComponent):
    def __init__(self, backend, *, wires, herald):

        self.herald = herald

        super().__init__(backend, wires)

    def validate(self):
        self.validate_detector(self.wires, self.herald)

    def apply(self):
        with self.backend.circuit.context as q:
            for wire, herald in zip(self.reindexed_wires, self.herald):
                MeasureFock(select=herald) | q[wire]