from PySide6.QtWidgets import QTabWidget
from control_panel.tabs.components_tab import ComponentsTab
from control_panel.tabs.gram_matrix_tab import GramMatrixTab
from control_panel.tabs.output_tab import OutputTab

class ControlPanel(QTabWidget):
    def __init__(self, window):
        super().__init__()

        self.window = window

        # Tabs
        self.components_tab = ComponentsTab(window)
        self.addTab(self.components_tab, "Components")

        self.gram_matrix_tab = GramMatrixTab(window)
        self.addTab(self.gram_matrix_tab, "Gram matrix")
        
        self.output_tab = OutputTab(window)
        self.addTab(self.output_tab, "Output")
