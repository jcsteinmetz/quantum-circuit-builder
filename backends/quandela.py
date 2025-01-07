import numpy as np
import perceval as pcvl
from perceval.components import BS, PS, PERM
from backends.backend import Backend
from backends.utils import degrees_to_radians, rank_to_basis
from backends.components.beamsplitter import BeamSplitter
from backends.components.switch import Switch
from backends.components.phaseshift import PhaseShift
from backends.components.loss import Loss
from backends.components.detector import Detector

class Quandela(Backend):
    def __init__(self, n_wires, n_photons):
        super().__init__(n_wires, n_photons)

        self.circuit = pcvl.Circuit(self.n_wires)
        self.naive_backend = pcvl.BackendFactory().get_backend("Naive")

        self.input_basis_element = ()

        self.output_probabilities = np.zeros((self.hilbert_dimension))

    def run(self):
        for comp in self.component_list:
            comp.apply()

        self.naive_backend.set_circuit(self.circuit)
        self.naive_backend.set_input_state(self.input_basis_element)

        for rank in range(self.hilbert_dimension):
            output_basis_element = pcvl.BasicState(rank_to_basis(self.n_wires, self.n_photons, rank))
            prob = np.abs(self.naive_backend.prob_amplitude(output_basis_element))**2
            self.output_probabilities[rank] = prob
        self.eliminate_tolerance()

    def set_input_state(self, input_basis_element):
        self.input_basis_element = pcvl.BasicState(list(input_basis_element))

    @property
    def output_data(self):
        prob_vector = self.output_probabilities

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

        for row in range(len(table_data[:, 1])):
            table_data[row, 1] = f'{float(f"{table_data[row, 1]:.4g}"):g}'
        return table_data

    def add_beamsplitter(self, **kwargs):
        comp = QuandelaBeamSplitter(self, **kwargs)
        self.add_component(comp)
    
    def add_switch(self, **kwargs):
        comp = QuandelaSwitch(self, **kwargs)
        self.add_component(comp)

    def add_phaseshift(self, **kwargs):
        comp = QuandelaPhaseShift(self, **kwargs)
        self.add_component(comp)
    
    def add_loss(self, **kwargs):
        comp = QuandelaLoss(self, **kwargs)
        self.add_component(comp)
    
    def add_detector(self, **kwargs):
        comp = QuandelaDetector(self, **kwargs)
        self.add_component(comp)

    def eliminate_tolerance(self, tol=1E-10):
        self.output_probabilities[np.abs(self.output_probabilities) < tol] = 0

class QuandelaBeamSplitter(BeamSplitter):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def apply(self):
        # Perceval can only do beam splitters and switches on consecutive wires
        all_wires = tuple(range(self.backend.n_wires))

        switched = False
        if self.reindexed_wires[0] + 1 != self.reindexed_wires[1]:
            permuted_wires = list(range(self.backend.n_wires))
            w0, w1 = self.reindexed_wires[0] + 1, self.reindexed_wires[1]
            permuted_wires[w0], permuted_wires[w1] = permuted_wires[w1], permuted_wires[w0]

            self.backend.circuit.add(all_wires, PERM(permuted_wires))

            switched = True

        self.backend.circuit.add((self.reindexed_wires[0], self.reindexed_wires[0]+1), BS.H(self.theta))

        # Perceval automatically switches wire indices during a beam splitter
        self.backend.circuit.add((self.reindexed_wires[0], self.reindexed_wires[0]+1), PERM([1, 0]))

        # Switch back
        if switched:
            self.backend.circuit.add(all_wires, PERM(permuted_wires))

class QuandelaSwitch(Switch):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def apply(self):
        self.backend.circuit.add(tuple(self.reindexed_wires), PERM([1, 0]))

class QuandelaPhaseShift(PhaseShift):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def apply(self):
        self.backend.circuit.add(self.wire, PS(phi = self.phase))

class QuandelaLoss(Loss):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def apply(self):
        raise ValueError("Loss is not implemented in the Perceval backend.")

class QuandelaDetector(Detector):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def apply(self):
        raise ValueError("Detectors are not implemented in the Perceval backend.")
