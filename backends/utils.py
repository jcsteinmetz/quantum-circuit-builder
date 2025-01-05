import itertools
import math
import numpy as np

def rank_to_basis(n_wires, n_photons, rank):
    pool = itertools.combinations_with_replacement(range(n_wires), 0)
    for n_i in range(1, n_photons+1):
        pool = itertools.chain(pool, itertools.combinations_with_replacement(range(n_wires), n_i))
    mode_list = next(itertools.islice(pool, rank, None))
    mode_list = list(mode_list)
    element = [0]*n_wires
    for mode in mode_list:
        element[mode] += 1
    return tuple(element)

def basis_to_rank(element):
    n_photons = int(sum(element))
    n_wires = len(element)
    rank = int(sum(math.comb(n_p + n_wires - 1, n_p) for n_p in range(n_photons)))
    for remaining_modes, used_photons in zip(reversed(range(1, n_wires)), itertools.accumulate(element)):
        remaining_photons = n_photons - used_photons
        rank += sum(math.comb(n_pp + remaining_modes - 1, n_pp) for n_pp in range(int(remaining_photons)))
    return rank

def calculate_hilbert_dimension(n_wires, n_photons):
    return sum(math.comb(n + n_wires - 1, n) for n in range(n_photons + 1))

def spin_y_matrix(size):
    spin_y_matrix = np.zeros((size, size), dtype=complex)
    for a in range(size):
        for b in range(size):
            spin_y_matrix[a, b] = 1j*(int(a == (b+1)) - int((a+1) == b)) * np.sqrt(((size + 1)/2)*(a+b+1) - (a+1)*(b+1))
    return spin_y_matrix

def degrees_to_radians(deg):
    return (np.pi/180)*deg