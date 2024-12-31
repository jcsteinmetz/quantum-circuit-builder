import time
from state import State

class Circuit:
    def __init__(self, n_wires, n_photons):

        self.n_wires = n_wires
        self.n_photons = n_photons

        if self.n_wires < 1:
            raise ValueError("No wires in the circuit.")

        self.state = State(self)

        self.component_list = []

    def run(self):
        print("WAITING")
        time.sleep(5)