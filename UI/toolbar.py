"""
Contains the ToolBar class.
"""
import os
from functools import partial
from PySide6.QtWidgets import QFileDialog, QSizePolicy, QWidget, QToolBar, QApplication, QComboBox, QStyle
from PySide6.QtGui import QAction, QActionGroup, QIcon
from UI.component import Wire, BeamSplitter, Switch, Loss, Detector, PhaseShift, XGate, YGate, ZGate, Hadamard, Qubit, CNOT
from UI.canvas import Select, Grab
from backends import FockBackend, PermanentBackend, MrMustardBackend, PercevalBackend, MPBackend, QiskitBackend

class ToolBar(QToolBar):
    """
    Class containing all toolbar buttons and dropdowns and their corresponding actions.
    """
    def __init__(self, window):
        super().__init__()

        self.window = window

        self.setup_toolbar()

    def setup_toolbar(self):
        self.clear() # clear the toolbar in case it has previously been set up

        # Button icons
        open_icon = self.style().standardIcon(QStyle.StandardPixmap.SP_DialogOpenButton)
        save_icon = self.style().standardIcon(QStyle.StandardPixmap.SP_DialogSaveButton)
        undo_icon = self.style().standardIcon(QStyle.StandardPixmap.SP_ArrowBack)
        redo_icon = self.style().standardIcon(QStyle.StandardPixmap.SP_ArrowForward)
        recenter_icon = QIcon("assets/recenter.png")
        run_icon = self.style().standardIcon(QStyle.StandardPixmap.SP_MediaPlay)
        delete_icon = self.style().standardIcon(QStyle.StandardPixmap.SP_DialogCancelButton)
        darkmode_icon = QIcon("assets/darkmode.png")
        clear_icon = self.style().standardIcon(QStyle.StandardPixmap.SP_DialogDiscardButton)
        quit_icon = self.style().standardIcon(QStyle.StandardPixmap.SP_DialogCloseButton)

        # Tools (name of tool class, tool icon)
        if self.window.simulation_type == "photonic":
            tools = {
                "Select": (Select, QIcon("assets/select.png")),
                "Grab": (Grab, QIcon("assets/grab.png")),
                "Wire": (Wire, QIcon("assets/wire.png")),
                "Beam splitter": (BeamSplitter, QIcon("assets/beamsplitter.png")),
                "Switch": (Switch, QIcon("assets/switch.png")),
                "Phase shift": (PhaseShift, QIcon("assets/phaseshift.png")),
                "Loss": (Loss, QIcon("assets/loss.png")),
                "Detector": (Detector, QIcon("assets/detector.png"))
            }
            backend_options = {
                "Fock backend": FockBackend,
                "Permanent backend": PermanentBackend,
                "Mr Mustard": MrMustardBackend,
                "Perceval": PercevalBackend
            }
        else:
            tools = {
                "Select": (Select, QIcon("assets/select.png")),
                "Grab": (Grab, QIcon("assets/grab.png")),
                "Qubit": (Qubit, QIcon("assets/wire.png")),
                "X gate": (XGate, QIcon("assets/xgate.png")),
                "Y gate": (YGate, QIcon("assets/ygate.png")),
                "Z gate": (ZGate, QIcon("assets/zgate.png")),
                "Hadamard": (Hadamard, QIcon("assets/hadamard.png")),
                "CNOT": (CNOT, QIcon("assets/CNOT.png"))
            }
            backend_options = {
                "Matrix product backend": MPBackend,
                "Qiskit": QiskitBackend
            }

        # Buttons
        self.add_button("Open", self.open_trigger, open_icon)
        self.add_button("Save", self.save_trigger, save_icon)
        self.add_button("Undo", self.window.undo, undo_icon)
        self.add_button("Redo", self.window.redo, redo_icon)
        self.addSeparator()
        self.add_tools(tools)
        self.add_button("Delete", self.delete_trigger, delete_icon)
        self.addSeparator()
        self.add_dropdown(self.set_backend, backend_options)
        self.addSeparator()
        self.add_button("Re-center", self.recenter_trigger, recenter_icon)
        self.add_button("Run", self.window.worker_thread.start_task, run_icon)
        self.add_button("Dark mode", self.darkmode_trigger, darkmode_icon, checkable=True, checked=True)
        spacer = QWidget()
        spacer.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        self.addWidget(spacer)
        self.add_button("Clear", self.clear_trigger, clear_icon)
        self.add_button("Quit", self.quit_trigger, quit_icon)

    def add_tools(self, tools):
        """
        Add a list of tools to the toolbar. Only one tool can be selected at a time.
        """
        action_group = QActionGroup(self)
        action_group.setExclusive(True)

        for tool_name, tool_data in tools.items():
            tool_type = tool_data[0]
            tool_icon = tool_data[1]
            if tool_icon:
                action = QAction(tool_icon, tool_name, self)
            else:
                action = QAction(tool_name, self)
            action.setCheckable(True)
            if tool_type == Select:
                action.setChecked(True)

            action.setToolTip(tool_name)

            self.addAction(action)
            action_group.addAction(action)
            action.triggered.connect(partial(self.set_active_tool, tool_type))

    def on_tool_triggered(self, tool_type):
        self.set_active_tool(tool_type)

    def add_dropdown(self, dropdown_trigger, options):
        """
        Add a dropdown menu to the toolbar.
        """
        dropdown = QComboBox()
        dropdown.addItems(options.keys())
        dropdown.currentIndexChanged.connect(lambda index: dropdown_trigger(options[dropdown.currentText()]))
        self.addWidget(dropdown)

        # Trigger first option
        dropdown_trigger(options[dropdown.currentText()])

    def add_button(self, name, trigger, icon, checkable=False, checked=False):
        """
        Add a button to the toolbar. Buttons perform a one-time action when clicked.
        """
        if icon:
            action = QAction(icon, name, self)
        else:
            action = QAction(name, self)
        self.addAction(action)
        action.triggered.connect(trigger)
        action.setCheckable(checkable)
        action.setChecked(checked)

    def set_active_tool(self, tool_type):
        self.window.canvas.active_tool = tool_type(self.window)

    def set_backend(self, backend_choice):
        self.window.interface.chosen_backend = backend_choice
        self.window.console.refresh()

    def darkmode_trigger(self):
        self.window.style_manager.darkmode_toggle()

    def recenter_trigger(self):
        self.window.canvas.recenter()

    def delete_trigger(self):
        for comp in reversed(list(self.window.canvas.all_placed_components())):
            if comp.is_selected:
                comp.delete()
        self.window.control_panel.components_tab.refresh()
        self.window.canvas.repaint()

    def clear_trigger(self):
        self.window.clear()

    def save_trigger(self):
        current_path = os.path.dirname(os.path.abspath(__file__))
        file_path, _ = QFileDialog.getSaveFileName(self, "Save circuit", current_path, "Circ Files (*.circ);;All Files (*)")
        self.window.save_file(file_path)

    def open_trigger(self):
        # File open dialog
        current_path = os.path.dirname(os.path.abspath(__file__))
        file_path, _ = QFileDialog.getOpenFileName(self, "Open circuit", current_path, "Circ Files (*.circ);;All Files (*)")

        self.window.open_file(file_path)

    def quit_trigger(self):
        """
        Quits the application
        """
        QApplication.instance().quit()

    def clear(self):
        for action in self.actions():
            self.removeAction(action)