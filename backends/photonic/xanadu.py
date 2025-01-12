from backends.backend import Backend
import strawberryfields as sf
from strawberryfields.ops import Fock, Vac, BSgate, Interferometer, LossChannel, MeasureFock, Rgate
import numpy as np
import math
from backends.utils import rank_to_basis
from backends.photonic.components.beamsplitter import BeamSplitter
from backends.photonic.components.switch import Switch
from backends.photonic.components.phaseshift import PhaseShift
from backends.photonic.components.loss import Loss
from backends.photonic.components.detector import Detector

class Xanadu(Backend):
    def __init__(self, n_wires, n_photons):
        super().__init__(n_wires, n_photons)

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
        with self.circuit.context as q:
            for wire, n_photons in enumerate(input_basis_element):
                if n_photons == 0:
                    Vac | q[wire]
                else:
                    Fock(n_photons) | q[wire]

    @property
    def output_data(self):
        prob_vector = []

        # Get the indices for the array
        indices = np.indices(self.output_probabilities.shape)

        # Iterate over all indices and apply the condition
        for n in range(self.n_photons+1):
            sub_prob_vector = np.zeros((math.comb(n + self.n_wires - 1, n)))
            count = 0
            for idx in zip(*indices.reshape(self.output_probabilities.ndim, -1)):  # Reshape to get all index combinations
                if sum(idx) == n:  # Check if sum of indices equals the target
                    sub_prob_vector[count] = self.output_probabilities[idx]  # Add the corresponding element
                    count += 1
            sub_prob_vector = sub_prob_vector[::-1] # xanadu uses reverse lex order
            prob_vector.extend(sub_prob_vector)
        prob_vector = np.array(prob_vector)

        table_length = np.count_nonzero(prob_vector)
        table_data = np.zeros((table_length, 2), dtype=object)
        for row, rank in enumerate(np.nonzero(prob_vector)[0]):
            basis_element_string = str(rank_to_basis(self.n_wires, self.n_photons, rank))
            basis_element_string = basis_element_string.replace("(", "")
            basis_element_string = basis_element_string.replace(")", "")
            basis_element_string = basis_element_string.replace(" ", "")
            basis_element_string = basis_element_string.replace(",", "")
            table_data[row, 0] = "".join(basis_element_string)
            table_data[row, 1] = prob_vector[rank]

        return table_data
    
    def add_beamsplitter(self, **kwargs):
        comp = XanaduBeamSplitter(self, **kwargs)
        self.add_component(comp)
    
    def add_switch(self, **kwargs):
        comp = XanaduSwitch(self, **kwargs)
        self.add_component(comp)

    def add_phaseshift(self, **kwargs):
        comp = XanaduPhaseShift(self, **kwargs)
        self.add_component(comp)
    
    def add_loss(self, **kwargs):
        comp = XanaduLoss(self, **kwargs)
        self.add_component(comp)
    
    def add_detector(self, **kwargs):
        comp = XanaduDetector(self, **kwargs)
        self.add_component(comp)

    def eliminate_tolerance(self, tol=1E-10):
        self.output_probabilities[np.abs(self.output_probabilities) < tol] = 0

class XanaduBeamSplitter(BeamSplitter):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def apply(self):
        with self.backend.circuit.context as q:
            BSgate(self.theta/2, 0) | (q[self.reindexed_wires[0]], q[self.reindexed_wires[1]])

class XanaduSwitch(Switch):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def apply(self):
        with self.backend.circuit.context as q:
            Interferometer(np.array([[0, 1], [1, 0]])) | (q[self.reindexed_wires[0]], q[self.reindexed_wires[1]])

class XanaduLoss(Loss):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def apply(self):
        with self.backend.circuit.context as q:
            LossChannel(self.eta) | (q[self.reindexed_wire])

class XanaduDetector(Detector):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def apply(self):
        with self.backend.circuit.context as q:
            for wire, herald in zip(self.reindexed_wires, self.herald):
                MeasureFock(select=herald) | q[wire]

class XanaduPhaseShift(PhaseShift):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def apply(self):
        with self.backend.circuit.context as q:
            Rgate(self.phase) | q[self.reindexed_wire]