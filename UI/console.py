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

        self.code += "circuit = "+str(self.window.interface.chosen_backend.__name__)+"(n_wires = "+str(self.window.canvas.n_wires)+", n_photons = "+str(self.window.canvas.n_photons)+")\n"

        for comp in self.window.canvas.placed_components["components"]:
            comp.add_to_console()

        self.add_detectors()

        self.code += "circuit.run(input_state = "+str(self.window.interface.input_fock_state)+")\n"

        self.setPlainText(self.code)

    def add_detectors(self):
        """Add the code for all detectors at once at the end."""
        wires = []
        herald = []
        if self.window.canvas.placed_components["detectors"]:
            for comp in self.window.canvas.placed_components["detectors"]:
                for w, wire in enumerate(self.window.canvas.placed_components["wires"]):
                    if comp.node_positions[0] == wire.node_positions[1]:
                        wires.append(w+1)
                        herald.append(comp.herald)
            self.code += "circuit.add_detector(wires = "+str(wires)+", herald = "+str(herald)+")\n"