from PySide6.QtWidgets import QTabWidget
from UI.control_panel.tabs.components_tab import ComponentsTab
from UI.control_panel.tabs.input_state_tab import InputStateTab
from UI.control_panel.tabs.output_tab import OutputTab

class ControlPanel(QTabWidget):
    def __init__(self, window):
        super().__init__()

        self.window = window

        # Tabs
        self.components_tab = ComponentsTab(window)
        self.addTab(self.components_tab, "Components")

        self.input_state_tab = InputStateTab(window)
        self.addTab(self.input_state_tab, "Input state (disabled)")
        
        self.output_tab = OutputTab(window)
        self.addTab(self.output_tab, "Output")
