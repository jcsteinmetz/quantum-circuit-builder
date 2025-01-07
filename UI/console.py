from PySide6.QtWidgets import QTextEdit

class Console(QTextEdit):
    def __init__(self, window):
        super().__init__()
        self.window = window
        self.setReadOnly(True)
        self.code = ""
        self.setPlainText(self.code)

    def refresh(self):
        self.code = ""

        self.code += "circuit = "+str(self.window.interface.backend.__name__)+"(n_wires = "+str(self.window.canvas.n_wires)+", n_photons = "+str(self.window.canvas.n_photons)+")\n"

        for comp in self.window.canvas.placed_components["components"]:
            comp.add_to_console()

        for comp in self.window.canvas.placed_components["detectors"]:
            comp.add_to_console()

        self.code += "circuit.run(input_state = "+str(self.window.interface.input_fock_state)+")\n"

        self.setPlainText(self.code)