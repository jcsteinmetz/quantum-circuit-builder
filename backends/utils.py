import itertools
import math
import numpy as np

def rank_to_basis(n_wires, n_photons, rank):
    pool = itertools.combinations_with_replacement(range(n_wires), n_photons)
    mode_list = list(next(itertools.islice(pool, rank, None)))
    element = [0]*n_wires
    for mode in mode_list:
        element[mode] += 1
    return tuple(element)

def calculate_hilbert_dimension(n_wires, n_photons):
    return math.comb(n_photons + n_wires - 1, n_photons)

def spin_y_matrix(size):
    spin_y_matrix = np.zeros((size, size), dtype=complex)
    for a in range(size):
        for b in range(size):
            spin_y_matrix[a, b] = 1j*(int(a == (b+1)) - int((a+1) == b)) * np.sqrt(((size + 1)/2)*(a+b+1) - (a+1)*(b+1))
    return spin_y_matrix

def degrees_to_radians(deg):
    return (np.pi/180)*deg