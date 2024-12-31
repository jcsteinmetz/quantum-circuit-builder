from PySide6.QtWidgets import QToolBar
from PySide6.QtGui import QAction, QActionGroup
from component import Select, Grab, Wire

class ToolBar(QToolBar):
    def __init__(self, window):
        super().__init__()
        self.window = window

        # Tools (name of tool class, tool icon)
        tools = {
            "Select": (Select, None),
            "Grab": (Grab, None),
            "Wire": (Wire, None)
        }

        # Buttons
        self.add_tools(tools)

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

    def set_active_tool(self, tool_type):
        self.window.canvas.active_tool = tool_type(self.window)