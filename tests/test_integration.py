import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import pytest
import numpy as np
from backends import FockBackend, PermanentBackend, MrMustardBackend, PercevalBackend, MPBackend, QiskitBackend

photonic_backends = [FockBackend, PermanentBackend, MrMustardBackend, PercevalBackend]

# PHOTONIC CIRCUIT TESTS

def test_hom():
    for backend in photonic_backends:
        circuit = backend(n_wires = 2, n_photons = 2)
        circuit.set_input_state((1, 1))
        circuit.add_beamsplitter(wires = [1, 2])
        circuit.run()
        output_data = circuit.get_output_data()

        # test labels
        assert np.all(output_data[:, 0] == ["20", "02"])

        # test probabilities
        probs = [float(p) for p in output_data[:, 1]]
        assert np.all(np.isclose(probs, [0.5, 0.5], atol=1e-10))

def test_unbalanced_hom():
    for backend in photonic_backends:
        circuit = backend(n_wires = 2, n_photons = 2)
        circuit.set_input_state((1, 1))
        circuit.add_beamsplitter(wires = [1, 2], theta = 135)
        circuit.run()
        output_data = circuit.get_output_data()

        # test labels
        assert np.all(output_data[:, 0] == ["20", "11", "02"])

        # test probabilities
        probs = [float(p) for p in output_data[:, 1]]
        assert np.all(np.isclose(probs, [0.25, 0.5, 0.25], atol=1e-10))

def test_mzi():
    for backend in photonic_backends:
        circuit = backend(n_wires = 2, n_photons = 1)
        circuit.set_input_state((1, 0))
        circuit.add_beamsplitter(wires = [1, 2])
        circuit.add_phaseshift(wires = [1])
        circuit.add_beamsplitter(wires = [1, 2])
        circuit.run()

        output_data = circuit.get_output_data()

        # test labels
        assert np.all(output_data[:, 0] == ["10"])

        # test probabilities
        probs = [float(p) for p in output_data[:, 1]]
        assert np.all(np.isclose(probs, [1], atol=1e-10))