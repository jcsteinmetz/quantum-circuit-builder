from PySide6.QtWidgets import QApplication, QMainWindow, QWidget, QHBoxLayout, QToolBar, QStyle
from PySide6.QtGui import QIcon, QAction, QCursor
from PySide6.QtCore import Qt
from canvas import Canvas
from components import Grab, NormalCursor, Wire, BeamSplitter

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        # Create central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # Create layout for central widget
        layout = QHBoxLayout()
        central_widget.setLayout(layout)

        # Create toolbar
        self.toolbar = QToolBar("Main Toolbar")
        self.addToolBar(self.toolbar)

        # Create actions with icons
        clear_icon = self.style().standardIcon(QStyle.StandardPixmap.SP_DialogDiscardButton)
        quit_icon = self.style().standardIcon(QStyle.StandardPixmap.SP_DialogCloseButton)

        self.normal_action = QAction("Normal", self)
        self.grab_action = QAction("Grab", self)
        self.wire_action = QAction("Wire", self)
        self.beamsplitter_action = QAction("Beam splitter", self)
        self.clear_action = QAction(clear_icon, "Clear", self)
        self.quit_action = QAction(quit_icon, "Quit", self)

        # Add actions to the toolbar
        self.toolbar.addAction(self.normal_action)
        self.toolbar.addAction(self.grab_action)
        self.toolbar.addAction(self.wire_action)
        self.toolbar.addAction(self.beamsplitter_action)
        self.toolbar.addSeparator()  # Add a separator line for better organization
        self.toolbar.addAction(self.clear_action)
        self.toolbar.addAction(self.quit_action)

        # Connect actions to slots
        self.normal_action.triggered.connect(self.normal_action_triggered)
        self.grab_action.triggered.connect(self.grab_action_triggered)
        self.wire_action.triggered.connect(self.wire_action_triggered)
        self.beamsplitter_action.triggered.connect(self.beamsplitter_action_triggered)
        self.clear_action.triggered.connect(self.clear_action_triggered)
        self.quit_action.triggered.connect(self.quit_action_triggered)

        # Create canvas widget
        style_choice = "darkmode"
        self.canvas = Canvas(style_choice)

        # Add widgets to the layout
        layout.addWidget(self.canvas)

        self.setWindowTitle("Circuit Builder")
        self.resize(800, 600)

    def normal_action_triggered(self):
        self.canvas.active_tool = NormalCursor(self.canvas)
        self.canvas.update()
    
    def grab_action_triggered(self):
        self.canvas.active_tool = Grab(self.canvas)
        self.canvas.update()

    def wire_action_triggered(self):
        self.canvas.active_tool = Wire(self.canvas)
        self.canvas.update()

    def beamsplitter_action_triggered(self):
        self.canvas.active_tool = BeamSplitter(self.canvas)
        self.canvas.update()

    def clear_action_triggered(self):
        for comp in self.canvas.placed_components[:]:
            comp.delete()
        self.canvas.update()

    def quit_action_triggered(self):
        QApplication.instance().quit()

if __name__ == "__main__":
    app = QApplication([])
    window = MainWindow()
    window.show()
    app.exec()
