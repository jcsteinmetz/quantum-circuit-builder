import numpy as np
import perceval as pcvl
from perceval.components import BS, PS, PERM, LC
from backends.backend import Backend
from backends.components.beamsplitter import BeamSplitter
from backends.components.switch import Switch
from backends.components.phaseshift import PhaseShift
from backends.components.loss import Loss
from backends.components.detector import Detector

class Quandela(Backend):
    def __init__(self, n_wires, n_photons):
        super().__init__(n_wires, n_photons)

        self.circuit = pcvl.Processor("Naive", self.n_wires)

        self.output_dict = {}

        self.sampler = pcvl.algorithm.Sampler(self.circuit)

    def run(self):
        for comp in self.component_list:
            comp.apply()

        self.output_dict = self.sampler.probs()["results"]

    def set_input_state(self, input_basis_element):
        self.circuit.min_detected_photons_filter(-1) # this should really be zero, but the current version of Perceval seems to have a mistake
        self.circuit.with_input(pcvl.BasicState(list(input_basis_element)))

    @property
    def output_data(self):

        table_length = len(self.output_dict)
        table_data = np.zeros((table_length, 2), dtype=object)

        row = 0
        for key, value in self.output_dict.items():
            # Remove Perceval's formatting
            basis_element_string = str(key)
            basis_element_string = basis_element_string.replace("|", "")
            basis_element_string = basis_element_string.replace(">", "")
            basis_element_string = basis_element_string.replace(",", "")
            table_data[row, 0] = basis_element_string
            table_data[row, 1] = value
            row += 1

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

class QuandelaBeamSplitter(BeamSplitter):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def apply(self):
        self.backend.circuit.add(tuple(self.reindexed_wires), BS.H(self.theta))

        # Perceval automatically switches wire indices during a beam splitter
        self.backend.circuit.add(tuple(self.reindexed_wires), PERM([1, 0]))

class QuandelaSwitch(Switch):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def apply(self):
        self.backend.circuit.add(tuple(self.reindexed_wires), PERM([1, 0]))

class QuandelaPhaseShift(PhaseShift):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def apply(self):
        self.backend.circuit.add(self.reindexed_wire, PS(phi = self.phase))

class QuandelaLoss(Loss):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def apply(self):
        for wire in range(self.backend.n_wires):
            if wire == self.reindexed_wire:
                self.backend.circuit.add(wire, LC(1 - self.eta))
            else:
                self.backend.circuit.add(wire, LC(0)) # perceval seems to have a problem with applying loss to only 1 wire

class QuandelaDetector(Detector):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def apply(self):
        for w, h in zip(self.reindexed_wires, self.herald):
            self.backend.circuit.add_herald(w, h)
