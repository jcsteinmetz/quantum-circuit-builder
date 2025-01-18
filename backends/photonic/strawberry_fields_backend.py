from backends.backend import PhotonicBackend
import strawberryfields as sf
from strawberryfields.ops import Fock, Vac, BSgate, Interferometer, LossChannel, MeasureFock, Rgate
import numpy as np
from backends.utils import rank_to_basis, tuple_to_str, fock_hilbert_dimension_fixed_number
from backends.photonic.components import BeamSplitter, Switch, PhaseShift, Loss, Detector

class SFBeamSplitter(BeamSplitter):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def apply(self):
        with self.backend.circuit.context as q:
            BSgate(self.theta/2, 0) | (q[self.reindexed_wires[0]], q[self.reindexed_wires[1]])

class SFSwitch(Switch):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def apply(self):
        with self.backend.circuit.context as q:
            Interferometer(np.array([[0, 1], [1, 0]])) | (q[self.reindexed_wires[0]], q[self.reindexed_wires[1]])

class SFLoss(Loss):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def apply(self):
        with self.backend.circuit.context as q:
            LossChannel(self.eta) | (q[self.reindexed_wire])

class SFDetector(Detector):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def apply(self):
        with self.backend.circuit.context as q:
            for wire, herald in zip(self.reindexed_wires, self.herald):
                MeasureFock(select=herald) | q[wire]

class SFPhaseShift(PhaseShift):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def apply(self):
        with self.backend.circuit.context as q:
            Rgate(self.phase) | q[self.reindexed_wire]


class SFBackend(PhotonicBackend):

    component_registry = {
        "beamsplitter": SFBeamSplitter,
        "phaseshift": SFPhaseShift,
        "switch": SFSwitch,
        "loss": SFLoss,
        "detector": SFDetector,
    }
    
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

    def get_output_data(self):
        prob_vector = self.get_prob_vector()

        table_length = np.count_nonzero(prob_vector)
        table_data = np.zeros((table_length, 2), dtype=object)
        for row, rank in enumerate(np.nonzero(prob_vector)[0]):
            basis_element = rank_to_basis(self.n_wires, self.n_photons, rank)
            table_data[row, 0] = tuple_to_str(basis_element)
            table_data[row, 1] = prob_vector[rank]

        return table_data
    
    def get_prob_vector(self):
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

        # Loop through fixed number sectors
        for n in range(self.n_photons+1):
            # List of probabilities in the current number sector
            sector_hilbert_dimension = fock_hilbert_dimension_fixed_number(self.n_wires, n)
            sector_probabilities = np.zeros((sector_hilbert_dimension))

            sector_index = 0
            # Iterate through every combination of indices
            for idx in np.ndindex(self.output_probabilities.shape):
    
                 # Check if sum of indices equals the current sector's occupation number
                if sum(idx) == n:
                    sector_probabilities[sector_index] = self.output_probabilities[idx]  # Add the corresponding element
                    sector_index += 1

            prob_vector.extend(sector_probabilities[::-1]) # strawberry fields uses reverse lex order

        return np.array(prob_vector)

    def eliminate_tolerance(self, tol=1E-10):
        self.output_probabilities[np.abs(self.output_probabilities) < tol] = 0