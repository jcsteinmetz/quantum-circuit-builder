from PySide6.QtWidgets import QFileDialog, QLabel, QMainWindow, QWidget, QVBoxLayout, QSplitter
from PySide6.QtGui import QIcon
from PySide6.QtCore import Qt
from canvas import Canvas
from console import Console
from control_panel.control_panel import ControlPanel
from toolbar import ToolBar
from copy import deepcopy
import os
import pickle
import numpy as np



class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.active_file = "Untitled.circ"
        self.unsaved_changes = False
        self.undo_stack = []
        self.redo_stack = []
        self.running = False

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

        # Window header
        self.update_title()

        # Prevent focus from being on a widget
        self.setFocus()

        self.update_undo_stack()

    def mark_unsaved_changes(self):
        self.update_undo_stack()
        self.unsaved_changes = True
        self.update_title()

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

        self.update_undo_stack()

    def update_title(self):
        title = "Circuit Builder v1.0 - "+self.active_file
        if self.unsaved_changes:
            title += " - Unsaved changes"
        if self.running:
            title += " - Running..."
        else:
            title += " - Ready"

        self.setWindowTitle(title)

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
        self.console.refresh()
        self.control_panel.components_tab.clear_components()
        self.canvas.repaint()

    def save_file(self):
        # Save to circ file
        current_path = os.path.dirname(os.path.abspath(__file__))
        file_path, _ = QFileDialog.getSaveFileName(self, "Save circuit", current_path, "Circ Files (*.circ);;All Files (*)")
        if file_path and not file_path.endswith(".circ"):
            file_path += ".circ"
        if file_path:
            save_data = (
                self.canvas.placed_components,
                self.canvas.grid.offset,
                self.canvas.grid.size
            )
            with open(file_path, "wb") as file:
                pickle.dump(save_data, file)
        
        self.active_file = file_path.split("/")[-1]
        self.unsaved_changes = False
        self.update_title

    def open_file(self):
        # File open dialog
        current_path = os.path.dirname(os.path.abspath(__file__))
        file_path, _ = QFileDialog.getOpenFileName(self, "Open circuit", current_path, "Circ Files (*.circ);;All Files (*)")

        # Open file
        if file_path:
            self.clear()
            with open(file_path, "rb") as file:
                load_data = pickle.load(file)

            (
                self.canvas.placed_components,
                self.canvas.grid.offset,
                self.canvas.grid.size
            ) = load_data

            # Set unserializable attributes
            for comp_list in self.canvas.placed_components.values():
                for comp in comp_list:
                    comp.set_unserializable_attributes(self)

            # Recreate circuit
            self.control_panel.components_tab.refresh()
            self.console.refresh()
            self.canvas.update()

            self.active_file = file_path.split("/")[-1]
            self.unsaved_changes = False
            self.update_title()
            self.update_undo_stack()