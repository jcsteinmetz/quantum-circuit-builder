from PySide6.QtWidgets import QTextEdit

class Console(QTextEdit):
    """
    Console widget that displays the code being run for this simulation, as determined by the components
    drawn on the canvas.
    """
    def __init__(self, window):
        super().__init__()
        self.window = window
        self.setReadOnly(True)
        self.code = ""
        self.setPlainText(self.code)

    def refresh(self):
        """Refreshes the console by looking at the components drawn on the canvas."""
        self.code = ""

        if self.window.simulation_type == "photonic":
            self.code += "circuit = "+str(self.window.interface.chosen_backend.__name__)+"(n_wires = "+str(self.window.canvas.n_wires)+", n_photons = "+str(self.window.canvas.n_photons)+")\n"
            self.code += "circuit.set_input_state("+str(tuple(self.window.interface.input_fock_state))+")\n"
        else:
            self.code += "circuit = "+str(self.window.interface.chosen_backend.__name__)+"(n_qubits= "+str(self.window.canvas.n_wires)+")\n"
            self.code += "circuit.set_input_state("+str(tuple(self.window.interface.input_qubit_state))+")\n"

        for comp in self.window.canvas.placed_components["components"]:
            comp.add_to_console()

        self.add_detectors()

        self.code += "circuit.run()\n"

        self.setPlainText(self.code)

    def add_detectors(self):
        """Add the code for all detectors at once at the end."""
        wires = []
        herald = []
        placed_detectors = self.window.canvas.placed_components["detectors"]
        placed_wires = self.window.canvas.placed_components["wires"]

        if not placed_detectors:
            return

        for detector in placed_detectors:
            connected_wire = detector.connected_wires[0]
            connected_wire_index = placed_wires.index(connected_wire) + 1
            wires.append(connected_wire_index)
            herald.append(detector.herald)

        self.code += "circuit.add_detector(wires = "+str(wires)+", herald = "+str(herald)+")\n"