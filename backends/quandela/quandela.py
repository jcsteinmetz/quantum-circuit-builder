import numpy as np
import perceval as pcvl
from perceval.components import BS, PS, PERM
from backends.backend import Backend
from backends.utils import degrees_to_radians, calculate_hilbert_dimension, rank_to_basis

class Quandela(Backend):

    def __init__(self, n_wires, n_photons):
        super().__init__(n_wires, n_photons)

        self.hilbert_dimension = calculate_hilbert_dimension(self.n_wires, self.n_photons)
        self.circuit = pcvl.Circuit(self.n_wires)
        self.backend = pcvl.BackendFactory().get_backend("Naive")
        self.state = State(self)

        self.component_list = []

    def run(self):
        for comp in self.component_list:
            comp.apply()

        self.backend.set_circuit(self.circuit)
        self.backend.set_input_state(self.state.input_basis_element)

        for rank in range(self.hilbert_dimension):
            output_basis_element = pcvl.BasicState(rank_to_basis(self.n_wires, self.n_photons, rank))
            prob = np.abs(self.backend.prob_amplitude(output_basis_element))**2
            self.state.output_probabilities[rank] = prob
        self.state.eliminate_tolerance()

    def set_input_state(self, input_basis_element):
        self.state.input_basis_element = pcvl.BasicState(list(input_basis_element))

    @property
    def output_data(self):
        prob_vector = self.state.output_probabilities

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
        comp = BeamSplitter(self.circuit, **kwargs)
        self.component_list.append(comp)
    
    def add_switch(self, **kwargs):
        comp = Switch(self.circuit, **kwargs)
        self.component_list.append(comp)

    def add_phaseshift(self, **kwargs):
        comp = PhaseShift(self.circuit, **kwargs)
        self.component_list.append(comp)
    
    def add_loss(self, **kwargs):
        comp = Loss(self.circuit, **kwargs)
        self.component_list.append(comp)
    
    def add_detector(self, **kwargs):
        comp = Detector(self.circuit, **kwargs)
        self.component_list.append(comp)

class State:
    def __init__(self, circuit):
        self.input_basis_element = ()
        self.circuit = circuit
        self.output_probabilities = np.zeros((self.circuit.hilbert_dimension))

    def eliminate_tolerance(self, tol=1E-10):
        self.output_probabilities[np.abs(self.output_probabilities) < tol] = 0

class BeamSplitter:
    def __init__(self, circuit, *, wires, theta):
        self.circuit = circuit
        self.wires = wires
        self.reindexed_wires = [w-1 for w in self.wires]
        self.theta = degrees_to_radians(theta)

        # Perceval switches wire indices during a beam splitter
        self.switch = Switch

    def apply(self):
        self.circuit.add(tuple(self.reindexed_wires), BS.H(self.theta))
        self.circuit.add(tuple(self.reindexed_wires), PERM([1, 0]))

class Switch:
    def __init__(self, circuit, *, wires):
        self.circuit = circuit
        self.wires = wires
        self.reindexed_wires = [w-1 for w in self.wires]

    def apply(self):
        self.circuit.add(tuple(self.reindexed_wires), PERM([1, 0]))

class PhaseShift:
    def __init__(self, circuit, *, wire, phase = 180):
        self.circuit = circuit
        self.wire = wire
        self.reindexed_wire = self.wire - 1
        self.phase = degrees_to_radians(phase)

    def apply(self):
        self.circuit.add(self.wire, PS(phi = self.phase))

class Loss:
    def __init__(self, circuit, *, wire, eta):
        self.circuit = circuit
        self.wire = wire
        self.reindexed_wire = [w-1 for w in self.wire]
        self.eta = eta

    def apply(self):
        pass

class Detector:
    def __init__(self, circuit, *, wires, herald):
        self.circuit = circuit
        self.wires = wires
        self.reindexed_wires = [w-1 for w in self.wires]
        self.herald = herald

    def apply(self):
        pass
