from PySide6.QtWidgets import QMainWindow, QWidget, QSplitter, QVBoxLayout
from PySide6.QtCore import Qt
from canvas import Canvas
from console import Console
from control_panel import ControlPanel
from toolbar import ToolBar

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        # Main widgets
        self.control_panel = ControlPanel(self)
        self.console = Console(self)
        self.canvas = Canvas(self)
        toolbar = ToolBar(self)

        # Create central widget layout
        splitter = QSplitter(Qt.Horizontal)
        left_widget = self.qvbox_widget([self.control_panel, self.console])
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

    def qvbox_widget(self, widgets):
        layout = QVBoxLayout()
        for w in widgets:
            layout.addWidget(w)
        compound_widget = QWidget()
        compound_widget.setLayout(layout)
        return compound_widget