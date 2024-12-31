from PySide6.QtWidgets import QSizePolicy, QWidget, QToolBar, QApplication, QComboBox, QStyle
from PySide6.QtGui import QAction, QActionGroup
from component import Select, Grab, Wire, BeamSplitter, Switch, Loss, Detector
from copy import copy

class ToolBar(QToolBar):
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
        self.add_button("Undo", self.undo_trigger, undo_icon)
        self.add_button("Redo", self.redo_trigger, redo_icon)
        self.addSeparator()
        self.add_tools(tools)
        self.add_button("Delete", self.delete_trigger, delete_icon)
        self.addSeparator()

        self.add_button("Re-center", self.recenter_trigger, recenter_icon)
        
        self.add_button("Dark mode", self.darkmode_trigger, darkmode_icon, checkable=True, checked=True)
        spacer = QWidget()
        spacer.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        self.addWidget(spacer)
        self.add_button("Clear", self.clear_trigger, clear_icon)
        self.add_button("Quit", self.quit_trigger, quit_icon)

    def add_tools(self, tools):
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

    def add_button(self, name, trigger, icon, checkable=False, checked=False):
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

    def darkmode_trigger(self):
        pass

    def recenter_trigger(self):
        pass

    def delete_trigger(self):
        pass

    def clear_trigger(self):
        pass

    def save_trigger(self):
        pass

    def open_trigger(self):
        pass

    def undo_trigger(self):
        pass

    def redo_trigger(self):
        pass

    def quit_trigger(self):
        pass