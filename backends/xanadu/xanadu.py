from backends.backend import Backend
import strawberryfields as sf
from strawberryfields.ops import Fock, Vac, BSgate, Interferometer, LossChannel, MeasureFock, Rgate
import numpy as np
import math
from backends.utils import degrees_to_radians, calculate_hilbert_dimension, rank_to_basis

class Xanadu(Backend):
    def __init__(self, n_wires, n_photons):
        super().__init__(n_wires, n_photons)

        self.hilbert_dimension = calculate_hilbert_dimension(self.n_wires, self.n_photons)
        self.eng = sf.Engine("fock", backend_options={"cutoff_dim": self.n_photons+1})
        self.state = State(self.n_wires, self.n_photons)

        self.component_list = []

    def run(self):
        for comp in self.component_list:
            comp.apply()

        results = self.eng.run(self.state.prog)

        self.state.output_probabilities = np.real(np.copy(results.state.all_fock_probs()))
        self.state.eliminate_tolerance()

    def set_input_state(self, input_basis_element):
        self.state.set_program_input(input_basis_element)

    @property
    def output_data(self):
        prob_vector = []

        # Get the indices for the array
        indices = np.indices(self.state.output_probabilities.shape)

        # Iterate over all indices and apply the condition
        for n in range(self.n_photons+1):
            sub_prob_vector = np.zeros((math.comb(n + self.n_wires - 1, n)))
            count = 0
            for idx in zip(*indices.reshape(self.state.output_probabilities.ndim, -1)):  # Reshape to get all index combinations
                if sum(idx) == n:  # Check if sum of indices equals the target
                    sub_prob_vector[count] = self.state.output_probabilities[idx]  # Add the corresponding element
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

        for row in range(len(table_data[:, 1])):
            table_data[row, 1] = f'{float(f"{table_data[row, 1]:.4g}"):g}'
        return table_data
    
    def add_beamsplitter(self, **kwargs):
        comp = BeamSplitter(self.state.prog, **kwargs)
        self.component_list.append(comp)
    
    def add_switch(self, **kwargs):
        comp = Switch(self.state.prog, **kwargs)
        self.component_list.append(comp)

    def add_phaseshift(self, **kwargs):
        comp = PhaseShift(self.state.prog, **kwargs)
        self.component_list.append(comp)
    
    def add_loss(self, **kwargs):
        comp = Loss(self.state.prog, **kwargs)
        self.component_list.append(comp)
    
    def add_detector(self, **kwargs):
        comp = Detector(self.state.prog, **kwargs)
        self.component_list.append(comp)

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

    def eliminate_tolerance(self, tol=1E-10):
        self.output_probabilities[np.abs(self.output_probabilities) < tol] = 0

class BeamSplitter:
    def __init__(self, prog, *, wires, theta = 90):
        self.prog = prog
        self.wires = wires
        self.theta = degrees_to_radians(theta) / 2 # to match Xanadu's convention
        self.reindexed_wires = [wire - 1 for wire in self.wires]

    def apply(self):
        with self.prog.context as q:
            BSgate(self.theta, np.pi/2) | (q[self.reindexed_wires[0]], q[self.reindexed_wires[1]])

class Switch:
    def __init__(self, prog, *, wires):
        self.prog = prog
        self.wires = wires
        self.reindexed_wires = [wire - 1 for wire in self.wires]

    def apply(self):
        with self.prog.context as q:
            Interferometer(np.array([[0, 1], [1, 0]])) | (q[self.reindexed_wires[0]], q[self.reindexed_wires[1]])

class Loss:
    def __init__(self, prog, *, wire, eta = 1):
        self.prog = prog
        self.wire = wire
        self.eta = eta
        self.reindexed_wire = self.wire - 1

    def apply(self):
        with self.prog.context as q:
            LossChannel(self.eta) | (q[self.reindexed_wire])

class Detector:
    def __init__(self, prog, *, wires, herald):
        self.prog = prog
        self.wires = wires
        self.herald = herald
        self.reindexed_wires = [w - 1 for w in self.wires]

    def apply(self):
        with self.prog.context as q:
            for wire, herald in zip(self.reindexed_wires, self.herald):
                MeasureFock(select=herald) | q[wire]

class PhaseShift:
    def __init__(self, prog, *, wire, phase):

        if not isinstance(wire, int):
            raise ValueError("Phase shift requires exactly 1 wire.")
        
        if not 0 <= phase <= 360:
            raise ValueError("Phase must be between 0 and 360.")

        self.prog = prog
        self.wire = wire
        self.reindexed_wire = self.wire - 1

        self.phase = degrees_to_radians(phase)

    def apply(self):
        with self.prog.context as q:
            Rgate(self.phase) | q[self.reindexed_wire]