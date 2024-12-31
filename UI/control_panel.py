from PySide6.QtWidgets import QTabWidget
from components_tab import ComponentsTab
from output_tab import OutputTab

class ControlPanel(QTabWidget):
    def __init__(self, window):
        super().__init__()

        self.window = window

        # Tabs
        self.components_tab = ComponentsTab(window)
        self.addTab(self.components_tab, "Components")
        
        self.output_tab = OutputTab(window)
        self.addTab(self.output_tab, "Output")