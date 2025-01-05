import numpy as np
from backends.fock.component import Component
from backends.utils import rank_to_basis, basis_to_rank

class Loss(Component):
    def __init__(self, state, *, wire, eta = 1):
        super().__init__(state)

        if not isinstance(wire, int):
            raise ValueError("Loss requires exactly 1 wire.")
        
        self.state = state
        self.wire = wire
        self.reindexed_wire = wire - 1
        self.eta = eta

    def apply(self, state):
        state.density_matrix = sum([kraus @ state.density_matrix @ np.conjugate(kraus).T for kraus in self.kraus_operators().values()])

    def kraus_operators(self):
        kraus_operators = {}
        for lost_photons in range(self.state.n_photons + 1):
            kraus_operators[lost_photons] = np.zeros((self.state.hilbert_dimension, self.state.hilbert_dimension))

            for rank in self.state.occupied_ranks:
                basis_element = rank_to_basis(self.state.n_wires, self.state.n_photons, rank)
                photons_in_wire = basis_element[self.reindexed_wire]

                if lost_photons <= photons_in_wire:
                    new_basis_element = [n if wire != self.reindexed_wire else n - lost_photons for wire, n in enumerate(basis_element)]
                    new_rank = basis_to_rank(new_basis_element)

                    kraus_operators[lost_photons][new_rank, rank] = self.eta**((photons_in_wire - lost_photons)/2)*(1 - self.eta)**(lost_photons / 2)
        return kraus_operators