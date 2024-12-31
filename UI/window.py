from copy import deepcopy
from PySide6.QtWidgets import QMainWindow, QWidget, QSplitter, QVBoxLayout, QLabel
from PySide6.QtCore import Qt
from canvas import Canvas
from console import Console
from control_panel.control_panel import ControlPanel
from toolbar import ToolBar

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.unsaved_changes = False
        self.undo_stack = []
        self.redo_stack = []

        # Main widgets
        self.control_panel = ControlPanel(self)
        self.console_label = QLabel("Console")
        self.console = Console(self)
        self.canvas = Canvas(self)
        toolbar = ToolBar(self)

        # Create central widget layout
        splitter = QSplitter(Qt.Horizontal)
        left_widget = self.qvbox_widget([self.control_panel, self.console_label, self.console])
        right_widget = self.qvbox_widget([self.canvas])
        splitter.addWidget(left_widget)
        splitter.addWidget(right_widget)
        splitter.setSizes([100, 700])

        central_widget = self.qvbox_widget([toolbar, splitter])
        self.setCentralWidget(central_widget)
        self.setWindowState(Qt.WindowMaximized)
        self.resize(800, 600)

        # Prevent focus from being on a widget
        self.setFocus()

        self.update_undo_stack()

    def mark_unsaved_changes(self):
        self.update_undo_stack()
        self.unsaved_changes = True

    def update_undo_stack(self):
        if len(self.undo_stack) >= 50:
            self.undo_stack.pop(0)
            current_state = (
                deepcopy(self.canvas.placed_components),
                deepcopy(self.canvas.grid.offset),
                deepcopy(self.canvas.grid.size)
            )
            self.undo_stack.append(current_state)

    def undo(self):
        if len(self.undo_stack) > 1:
            current_state = self.undo_stack.pop()
            self.redo_stack.append(current_state)
            (
                self.canvas.placed_components,
                self.canvas.grid.offset,
                self.canvas.grid.size
            ) = self.undo_stack[-1]

        # Set unserializable attributes
        for comp_list in self.canvas.placed_components.values():
            for comp in comp_list:
                comp.set_unserializable_attributes(self)

        # Recreate circuit
        self.control_panel.components_tab.refresh()
        self.canvas.deselect_all()
        self.canvas.update()

    def redo(self):
        if self.redo_stack:
            (
                self.canvas.placed_components,
                self.canvas.grid.offset,
                self.canvas.grid.size
            ) = self.redo_stack.pop()

        # Set unserializable attributes
        for comp_list in self.canvas.placed_components.values():
            for comp in comp_list:
                comp.set_unserializable_attributes(self)

        # Recreate circuit
        self.control_panel.components_tab.refresh()
        self.canvas.deselect_all()
        self.canvas.update()


    def qvbox_widget(self, widgets):
        layout = QVBoxLayout()
        for w in widgets:
            layout.addWidget(w)
        compound_widget = QWidget()
        compound_widget.setLayout(layout)
        return compound_widget
    
    def clear(self):
        for comp_list in self.canvas.placed_components.values():
            for comp in comp_list[:]:
                comp.delete()
        self.control_panel.components_tab.clear_components()
        self.canvas.repaint()
