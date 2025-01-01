"""
Contains the ToolBar class.
"""

from copy import copy
from PySide6.QtWidgets import QSizePolicy, QWidget, QToolBar, QApplication, QComboBox, QStyle
from PySide6.QtGui import QAction, QActionGroup
from component import Wire, BeamSplitter, Switch, Loss, Detector
from canvas_tools import Select, Grab

class ToolBar(QToolBar):
    """
    Class containing all toolbar buttons and dropdowns and their corresponding actions.
    """
    def __init__(self, window):
        super().__init__()

        self.window = window

        # Tools (name of tool class, tool icon)
        tools = {
            "Select": (Select, None),
            "Grab": (Grab, None),
            "Wire": (Wire, None),
            "Beam splitter": (BeamSplitter, None),
            "Switch": (Switch, None),
            "Loss": (Loss, None),
            "Detector": (Detector, None)
        }

        backend_options = {
            "Select backend": None,
            "Fock backend": "fock",
            "Symbolic backend": "sym"
        }
        
        # Button icons
        open_icon = self.style().standardIcon(QStyle.StandardPixmap.SP_DialogOpenButton)
        save_icon = self.style().standardIcon(QStyle.StandardPixmap.SP_DialogSaveButton)
        undo_icon = self.style().standardIcon(QStyle.StandardPixmap.SP_ArrowBack)
        redo_icon = self.style().standardIcon(QStyle.StandardPixmap.SP_ArrowForward)
        recenter_icon = None
        run_icon = self.style().standardIcon(QStyle.StandardPixmap.SP_MediaPlay)
        delete_icon = self.style().standardIcon(QStyle.StandardPixmap.SP_DialogCancelButton)
        darkmode_icon = None
        clear_icon = self.style().standardIcon(QStyle.StandardPixmap.SP_DialogDiscardButton)
        quit_icon = self.style().standardIcon(QStyle.StandardPixmap.SP_DialogCloseButton)

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

            self.addAction(action)
            action_group.addAction(action)
            action.triggered.connect(lambda checked, t=tool_type: self.set_active_tool(t))

    def add_dropdown(self, dropdown_trigger, options):
        """
        Add a dropdown menu to the toolbar.
        """
        dropdown = QComboBox()
        dropdown.addItems(options.keys())
        dropdown.currentIndexChanged.connect(lambda index: dropdown_trigger(options[dropdown.currentText()]))
        self.addWidget(dropdown)

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
        self.window.interface.backend = backend_choice
        if backend_choice == "fock":
            self.window.control_panel.gram_matrix_tab.lock_gram_matrix()
        else:
            self.window.control_panel.gram_matrix_tab.unlock_gram_matrix()

    def darkmode_trigger(self):
        new_style = None
        if self.window.canvas.style_choice == "basic":
            new_style = "darkmode"
        elif self.window.canvas.style_choice == "darkmode":
            new_style = "basic"
        self.window.canvas.style_choice = new_style
        self.window.canvas.set_style()
        for comp_list in self.window.canvas.placed_components.values():
            for comp in comp_list:
                comp.set_style()

        # Recreate active tool so it updates the style
        self.window.canvas.active_tool = self.window.canvas.active_tool.__class__(self.window)
        self.window.canvas.repaint()

    def recenter_trigger(self):
        self.window.canvas.drag(copy(self.window.canvas.grid.offset))
        self.window.canvas.repaint()

    def delete_trigger(self):
        for comp_list in self.window.canvas.placed_components.values():
            for comp in comp_list[:]:
                if comp.is_selected:
                    comp.delete()
        self.window.control_panel.components_tab.refresh()
        self.window.canvas.repaint()

    def clear_trigger(self):
        self.window.clear()

    def save_trigger(self):
        pass

    def open_trigger(self):
        pass

    def quit_trigger(self):
        """
        Quits the application
        """
        QApplication.instance().quit()