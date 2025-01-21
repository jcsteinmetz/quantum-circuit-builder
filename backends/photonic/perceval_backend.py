import perceval as pcvl
from abc import abstractmethod
from perceval.components import BS, PS, PERM, LC
from backends.backend import PhotonicBackend
from backends.component import Component
from backends.utils import tuple_to_str, degrees_to_radians

class PercevalBackend(PhotonicBackend):
    def __init__(self, n_wires, n_photons):
        super().__init__(n_wires, n_photons)

        # Register components
        self.register_component("beamsplitter", PercevalBeamSplitter)
        self.register_component("switch", PercevalSwitch)
        self.register_component("phaseshift", PercevalPhaseShift)
        self.register_component("loss", PercevalLoss)
        self.register_component("detector", PercevalDetector)

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

    @property
    def probabilities(self):
        pass
    
    @property
    def occupied_ranks(self):
        pass
    
    @property
    def nonzero_probabilities(self):
        return self.output_dict.values()
    
    @property
    def basis_strings(self):
        return [tuple_to_str(key) for key in self.output_dict.keys()]
    
class PercevalComponent(Component):
    def __init__(self, backend, wires):
        super().__init__(backend)

        self.wires = wires
        self.reindexed_wires = [w - 1 for w in wires]

    @abstractmethod
    def apply(self):
        raise NotImplementedError

class PercevalBeamSplitter(PercevalComponent):
    def __init__(self, backend, *, wires, theta=90):
        super().__init__(backend, wires)

        self.theta = degrees_to_radians(theta)

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

class PercevalSwitch(PercevalComponent):
    def __init__(self, backend, *, wires):
        super().__init__(backend, wires)

    def apply(self):
        self.backend.circuit.add(tuple(self.reindexed_wires), PERM([1, 0]))

class PercevalPhaseShift(PercevalComponent):
    def __init__(self, backend, *, wires, phase = 180):
        super().__init__(backend, wires)

        self.phase = degrees_to_radians(phase)

    def apply(self):
        self.backend.circuit.add(self.reindexed_wires, PS(phi = self.phase))

class PercevalLoss(PercevalComponent):
    def __init__(self, backend, *, wires, eta = 1):
        super().__init__(backend, wires)

        self.eta = eta

    def apply(self):
        for wire in range(self.backend.n_wires):
            if wire in self.reindexed_wires:
                self.backend.circuit.add(wire, LC(1 - self.eta))
            else:
                self.backend.circuit.add(wire, LC(0)) # perceval seems to have a problem with applying loss to only 1 wire

class PercevalDetector(PercevalComponent):
    def __init__(self, backend, *, wires, herald):
        super().__init__(backend, wires)

        self.herald = herald

    def apply(self):
        for w, h in zip(self.reindexed_wires, self.herald):
            self.backend.circuit.add_herald(w, h)
