from PySide6.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QButtonGroup
from canvas import Canvas
from components import Grab, NormalCursor, Wire

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        # Create central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # Create layout for central widget
        layout = QHBoxLayout()
        central_widget.setLayout(layout)

        # Create control panel widget
        self.control_panel = QWidget()
        control_panel_layout = QVBoxLayout()
        self.control_panel.setLayout(control_panel_layout)
        self.control_panel.setFixedWidth(150)  # Adjust width as needed

        # Create tool group
        self.tool_group = QButtonGroup()
        self.tool_group.setExclusive(True)  # Ensure only one button is toggled at a time

        # Create tool/button labels and actions
        tool_labels = [("Normal", self.normal_action),
                       ("Grab", self.grab_action),
                       ("Wire", self.wire_action)]

        button_labels = [("Clear", self.clear_action),
                         ("Quit", self.quit_action)]

        # Create tools/buttons and connect them to actions
        self.tools = []
        for label, action in tool_labels:
            tool = QPushButton(label)
            tool.setCheckable(True)
            self.tool_group.addButton(tool)
            control_panel_layout.addWidget(tool)
            self.tools.append(tool)
            tool.clicked.connect(action)  # Connect button to the corresponding action

        self.buttons = []
        for label, action in button_labels:
            button = QPushButton(label)
            control_panel_layout.addWidget(button)
            self.buttons.append(button)
            button.clicked.connect(action)

        # Set the first button to be toggled by default
        if self.tools:
            self.tools[0].setChecked(True)

        # Create canvas widget
        style_choice = "darkmode"
        self.canvas = Canvas(style_choice)

        # Add widgets to the layout
        layout.addWidget(self.control_panel)
        layout.addWidget(self.canvas)

        self.setWindowTitle("Circuit Builder")
        self.resize(800, 600)

    def normal_action(self):
        self.canvas.active_tool = NormalCursor(self.canvas)
        self.canvas.update()
    
    def grab_action(self):
        self.canvas.active_tool = Grab(self.canvas)
        self.canvas.update()

    def wire_action(self):
        # self.canvas.active_tool = WireStart(self.canvas)
        self.canvas.active_tool = Wire(self.canvas)
        self.canvas.update()

    def clear_action(self):
        for comp in self.canvas.placed_components[:]:
            comp.delete()
        self.canvas.update()

    def quit_action(self):
        QApplication.instance().quit()
