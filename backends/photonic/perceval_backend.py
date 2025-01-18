import numpy as np
import perceval as pcvl
from perceval.components import BS, PS, PERM, LC
from backends.backend import PhotonicBackend
from backends.photonic.components import BeamSplitter, Switch, PhaseShift, Loss, Detector
from backends.utils import tuple_to_str

class PercevalBackend(PhotonicBackend):
    def __init__(self, n_wires, n_photons):
        super().__init__(n_wires, n_photons)

        # Register components
        self.component_registry["beamsplitter"] = PercevalBeamSplitter
        self.component_registry["switch"] = PercevalSwitch
        self.component_registry["phaseshift"] = PercevalPhaseShift
        self.component_registry["loss"] = PercevalLoss
        self.component_registry["detector"] = PercevalDetector

        self.circuit = pcvl.Processor("SLOS", self.n_wires)

        self.output_dict = {}

        self.sampler = pcvl.algorithm.Sampler(self.circuit)

    def run(self):
        for comp in self.component_list:
            comp.apply()

        self.output_dict = self.sampler.probs()["results"]

    def set_input_state(self, input_basis_element):
        self.circuit.min_detected_photons_filter(-1) # this should really be zero, but the current version of Perceval seems to have a mistake
        self.circuit.with_input(pcvl.BasicState(list(input_basis_element)))

    def get_output_data(self):

        table_length = len(self.output_dict)
        table_data = np.zeros((table_length, 2), dtype=object)

        row = 0
        for key, value in self.output_dict.items():
            table_data[row, 0] = tuple_to_str(key)
            table_data[row, 1] = value
            row += 1

        return table_data

    def add_beamsplitter(self, **kwargs):
        comp = PercevalBeamSplitter(self, **kwargs)
        self.add_component(comp)
    
    def add_switch(self, **kwargs):
        comp = PercevalSwitch(self, **kwargs)
        self.add_component(comp)

    def add_phaseshift(self, **kwargs):
        comp = PercevalPhaseShift(self, **kwargs)
        self.add_component(comp)
    
    def add_loss(self, **kwargs):
        comp = PercevalLoss(self, **kwargs)
        self.add_component(comp)
    
    def add_detector(self, **kwargs):
        comp = PercevalDetector(self, **kwargs)
        self.add_component(comp)

class PercevalBeamSplitter(BeamSplitter):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def apply(self):
        # Perceval can only do beam splitters and switches on consecutive wires (it claims it can handle non-consecutive wires but it doesn't seem to work)
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

class PercevalSwitch(Switch):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def apply(self):
        self.backend.circuit.add(tuple(self.reindexed_wires), PERM([1, 0]))

class PercevalPhaseShift(PhaseShift):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def apply(self):
        self.backend.circuit.add(self.reindexed_wire, PS(phi = self.phase))

class PercevalLoss(Loss):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def apply(self):
        for wire in range(self.backend.n_wires):
            if wire == self.reindexed_wire:
                self.backend.circuit.add(wire, LC(1 - self.eta))
            else:
                self.backend.circuit.add(wire, LC(0)) # perceval seems to have a problem with applying loss to only 1 wire

class PercevalDetector(Detector):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def apply(self):
        for w, h in zip(self.reindexed_wires, self.herald):
            self.backend.circuit.add_herald(w, h)
