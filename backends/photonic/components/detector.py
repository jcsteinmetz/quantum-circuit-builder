from backends.component import Component

class Detector(Component):
    def __init__(self, backend, *, wires, herald):

        self.backend = backend
        self.wires = wires
        self.reindexed_wires = [w-1 for w in self.wires]
        self.herald = herald

        self.validate_input()
    
    def validate_input(self):
        if len(self.wires) >= self.backend.n_wires:
            raise ValueError("No state remaining. All photons hit detectors.")
        if len(self.herald) != len(self.wires):
            raise ValueError("Mismatch between length of herald and number of detectors.")
