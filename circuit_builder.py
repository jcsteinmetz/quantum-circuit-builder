from PySide6.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QButtonGroup
from PySide6.QtCore import Qt, QPoint, QPointF
from PySide6.QtGui import QPainter, QColor, QWheelEvent, QMouseEvent
import numpy as np

class GridCanvas(QWidget):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.grid_size = 100  # Size of each grid cell
        self.zoom_factor = 1.0  # Initial zoom factor
        self.is_grabbed = True  # Track if grab mode is enabled
        self.last_mouse_pos = None  # Track the last mouse position for dragging
        self.offset = QPointF(0, 0)  # Offset for grid dragging
        self.update_cursor()

    def update_cursor(self):
        if self.is_grabbed:
            self.setCursor(Qt.SizeAllCursor)
        else:
            self.setCursor(Qt.ArrowCursor)

    def paintEvent(self, event):
        painter = QPainter(self)

        # Fill the canvas with the background color
        painter.fillRect(self.rect(), QColor(255, 255, 255))

        painter.setPen(QColor(200, 200, 200))  # Light gray color for grid lines

        # Apply zoom factor to grid size
        zoomed_grid_size = self.grid_size * self.zoom_factor

        # Apply offset to shift the grid based on dragging
        x_offset = self.offset.x()
        y_offset = self.offset.y()

        # Draw vertical grid lines
        for x in np.arange(-x_offset % zoomed_grid_size, self.width(), zoomed_grid_size):
            painter.drawLine(x, 0, x, self.height())

        # Draw horizontal grid lines
        for y in np.arange(-y_offset % zoomed_grid_size, self.height(), zoomed_grid_size):
            painter.drawLine(0, y, self.width(), y)

    def wheelEvent(self, event: QWheelEvent):
        # Get the mouse position relative to the widget
        mouse_pos = event.position()

        # Convert the mouse position to the grid's coordinate system before zoom
        grid_pos_before_zoom = (mouse_pos + self.offset) / (self.grid_size * self.zoom_factor)

        # Calculate the zoom delta based on the wheel movement
        zoom_delta = event.angleDelta().y() / 120
        zoom_step = 0.1
        new_zoom_factor = self.zoom_factor + zoom_step * zoom_delta

        # Ensure the zoom factor is within reasonable bounds
        if 0.1 <= new_zoom_factor <= 5.0:

            grid_pos_after_zoom = (mouse_pos + self.offset) / (self.grid_size * new_zoom_factor)

            # Adjust the offset to keep the grid under the mouse stationary
            self.offset += (grid_pos_before_zoom - grid_pos_after_zoom) * self.grid_size * new_zoom_factor

            # Set the new zoom factor
            self.zoom_factor = new_zoom_factor

            # Trigger a redraw
            self.update()

    def mousePressEvent(self, event: QMouseEvent):
        # Start dragging if the left mouse button is pressed
        if event.button() == Qt.LeftButton and self.is_grabbed:
            self.last_mouse_pos = event.position()

    def mouseMoveEvent(self, event: QMouseEvent):
        # Handle grid dragging when "Grab" is active
        if self.is_grabbed and self.last_mouse_pos:
            delta = event.position() - self.last_mouse_pos
            self.offset -= delta  # Move the grid by the delta
            self.last_mouse_pos = event.position()  # Update the last mouse position
            self.update()  # Redraw the grid with the new offset

    def mouseReleaseEvent(self, event: QMouseEvent):
        # Stop dragging when the mouse button is released
        if event.button() == Qt.LeftButton and self.is_grabbed:
            self.last_mouse_pos = None

    def enterEvent(self, event):
        self.update_cursor()  # Update cursor on entering the widget

    def leaveEvent(self, event):
        self.setCursor(Qt.ArrowCursor)  # Reset cursor on leaving the widget

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

        # Create buttons and button group
        self.button_group = QButtonGroup()
        self.button_group.setExclusive(True)  # Ensure only one button is toggled at a time

        # Create button labels and actions
        button_labels = [("Grab", self.grab_action),
                         ("Input", self.input_action),
                         ("Output", self.output_action),
                         ("Wire", self.wire_action),
                         ("Beam splitter", self.beamsplitter_action)]

        # Create buttons and connect them to actions
        self.buttons = []
        for label, action in button_labels:
            button = QPushButton(label)
            button.setCheckable(True)
            self.button_group.addButton(button)
            control_panel_layout.addWidget(button)
            self.buttons.append(button)
            button.clicked.connect(action)  # Connect button to the corresponding action

        # Set the first button to be toggled by default
        if self.buttons:
            self.buttons[0].setChecked(True)

        # Create canvas widget
        self.canvas = GridCanvas()

        # Add widgets to the layout
        layout.addWidget(self.control_panel)
        layout.addWidget(self.canvas)

        self.setWindowTitle("Circuit Builder")
        self.resize(800, 600)

        # Install event filter to detect clicks anywhere
        self.installEventFilter(self)

    def grab_action(self):
        print("Grab selected")
        self.canvas.is_grabbed = True  # Enable grab mode
        self.canvas.update_cursor()  # Update cursor
    
    def input_action(self):
        print("Input selected")
        self.canvas.is_grabbed = False  # Disable grab mode for wire placement
        self.canvas.update_cursor()  # Update cursor

    def output_action(self):
        print("Output selected")
        self.canvas.is_grabbed = False  # Disable grab mode for wire placement
        self.canvas.update_cursor()  # Update cursor

    def wire_action(self):
        print("Wire selected")
        self.canvas.is_grabbed = False  # Disable grab mode for wire placement
        self.canvas.update_cursor()  # Update cursor

    def beamsplitter_action(self):
        print("Beam splitter selected")
        self.canvas.is_grabbed = False  # Disable grab mode for beam splitter
        self.canvas.update_cursor()  # Update cursor

if __name__ == "__main__":
    app = QApplication([])
    window = MainWindow()
    window.show()
    app.exec()
