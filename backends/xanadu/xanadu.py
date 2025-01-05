from backends.backend import Backend
import strawberryfields as sf
from strawberryfields.ops import Fock, Vac, BSgate, Interferometer, LossChannel
import numpy as np
from backends.utils import degrees_to_radians, calculate_hilbert_dimension, rank_to_basis

class Xanadu(Backend):
    def __init__(self, n_wires, n_photons):
        super().__init__(n_wires, n_photons)

        self.hilbert_dimension = calculate_hilbert_dimension(self.n_wires, self.n_photons)
        self.eng = sf.Engine("fock", backend_options={"cutoff_dim": self.hilbert_dimension})
        self.state = State(self.n_wires, self.n_photons)

        self.component_list = []

    def run(self):
        for comp in self.component_list:
            comp.apply()

        results = self.eng.run(self.state.prog)
        self.state.output_probabilities = np.real(np.copy(results.state.all_fock_probs()))
        self.state.eliminate_tolerance()

    def set_input_state(self, input_basis_label):
        self.state.set_program_input(input_basis_label)

    @property
    def output_data(self):
        probs_for_n_photons = np.zeros((self.hilbert_dimension))

        # Get the indices for the array
        indices = np.indices(self.state.output_probabilities.shape)

        # Iterate over all indices and apply the condition
        count = 0
        for idx in zip(*indices.reshape(self.state.output_probabilities.ndim, -1)):  # Reshape to get all index combinations
            if sum(idx) == self.n_photons:  # Check if sum of indices equals the target
                probs_for_n_photons[count] = self.state.output_probabilities[idx]  # Add the corresponding element
                count += 1
        prob_vector = probs_for_n_photons[::-1] # xanadu uses reverse lex order

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
            print(table_data[row, 1])
            print(f"{table_data[row, 1]:.4g}")
            table_data[row, 1] = f'{float(f"{table_data[row, 1]:.4g}"):g}'
        return table_data
    
    def add_beamsplitter(self, **kwargs):
        comp = BeamSplitter(self.state.prog, **kwargs)
        self.component_list.append(comp)
    
    def add_switch(self, **kwargs):
        comp = Switch(self.state.prog, **kwargs)
        self.component_list.append(comp)
    
    def add_loss(self, **kwargs):
        comp = Loss(self.state.prog, **kwargs)
        self.component_list.append(comp)
    
    def add_detector(self, **kwargs):
        raise NotImplementedError("Detectors are not implemented yet for the Strawberry Fields backend.")

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
    def __init__(self, prog, *, wires, eta = 1):
        self.prog = prog
        self.wires = wires
        self.eta = eta
        self.reindexed_wires = [wire - 1 for wire in self.wires]

    def apply(self):
        with self.prog.context as q:
            LossChannel(self.eta) | (q[self.reindexed_wires[0]])