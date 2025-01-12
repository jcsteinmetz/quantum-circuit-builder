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

def calculate_fock_hilbert_dimension(n_wires, n_photons):
    return sum(math.comb(n + n_wires - 1, n) for n in range(n_photons + 1))

def spin_y_matrix(size):
    spin_y_matrix = np.zeros((size, size), dtype=complex)
    for a in range(size):
        for b in range(size):
            spin_y_matrix[a, b] = 1j*(int(a == (b+1)) - int((a+1) == b)) * np.sqrt(((size + 1)/2)*(a+b+1) - (a+1)*(b+1))
    return spin_y_matrix

def degrees_to_radians(deg):
    return (np.pi/180)*deg

def bloch_to_rho(bloch):
    return 0.5*np.array([[1 + bloch[2], bloch[0] - 1j*bloch[1]], [bloch[0] - 1j*bloch[1], 1 - bloch[2]]], dtype=complex)

def pauli(direction):
    return direction[0]*pauli_x() + direction[1]*pauli_y() + direction[2]*pauli_z()

def pauli_x():
    return np.array([[0, 1], [1, 0]], dtype=complex)

def pauli_y():
    return np.array([[0, -1j], [1j, 0]], dtype=complex)

def pauli_z():
    return np.array([[1, 0], [0, -1]], dtype=complex)