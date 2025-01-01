from PySide6.QtWidgets import QTextEdit

class Console(QTextEdit):
    def __init__(self, window):
        super().__init__()
        self.window = window
        self.setReadOnly(True)
        self.code = "0 wires, 0 photons"
        self.setPlainText(self.code)

    def refresh(self):
        self.code = ""

        self.code += "wires: "+str(self.window.canvas.n_wires)+", photons: "+str(self.window.canvas.n_photons)+"\n"

        for comp in self.window.canvas.placed_components["components"]:
            comp.add_to_console()

        for comp in self.window.canvas.placed_components["detectors"]:
            comp.add_to_console()

        self.setPlainText(self.code)