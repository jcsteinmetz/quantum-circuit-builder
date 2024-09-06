from PySide6.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QButtonGroup
from PySide6.QtCore import Qt, QPoint, QPointF
from PySide6.QtGui import QPainter, QColor, QWheelEvent, QMouseEvent
import numpy as np

class GridCanvas(QWidget):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.grid_size = 100  # Size of each grid cell
        self.zoom_factor = 1.0  # Initial zoom factor
        self.status = "grab"  # Track which button is toggled
        self.last_mouse_pos = None  # Track the last mouse position for dragging
        self.offset = QPointF(0, 0)  # Offset for grid dragging
        self.update_cursor()
        self.show_floating_image = False  # Track if square should be shown
        self.floating_image_pos = None  # Position of the square
        self.setMouseTracking(True)

    def update_cursor(self):
        if self.status == "grab":
            self.setCursor(Qt.SizeAllCursor)
        elif self.status == "input":
            self.setCursor(Qt.BlankCursor)
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

        # Draw a floating image if needed
        if self.show_floating_image:
            self.draw_floating_image()

    def draw_floating_image(self):
        painter = QPainter(self)
        if self.status == "input":
            painter.setBrush(QColor(0, 0, 255, 100))  # Semi-transparent blue color
            painter.drawRect(self.floating_image_pos.x() - 50*self.zoom_factor, self.floating_image_pos.y() - 50*self.zoom_factor, 100*self.zoom_factor, 100*self.zoom_factor)  # 100x100 square
        if self.status == "output":
            painter.setBrush(QColor(0, 0, 255, 100))  # Semi-transparent blue color
            painter.drawRect(self.floating_image_pos.x() - 50*self.zoom_factor, self.floating_image_pos.y() - 50*self.zoom_factor, 100*self.zoom_factor, 100*self.zoom_factor)  # 100x100 square


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
        if event.button() == Qt.LeftButton and self.status == "grab":
            self.last_mouse_pos = event.position()

    def mouseMoveEvent(self, event: QMouseEvent):
        # Handle grid dragging when "Grab" is active
        if self.status == "grab" and self.last_mouse_pos:
            delta = event.position() - self.last_mouse_pos
            self.offset -= delta  # Move the grid by the delta
            self.last_mouse_pos = event.position()  # Update the last mouse position
            self.update()  # Redraw the grid with the new offset

        # Update the floating image's position if "Input" mode is active
        if self.show_floating_image:
            mouse_pos = event.position()
            # Calculate the grid-aligned position
            zoomed_grid_size = self.grid_size * self.zoom_factor

            # Calculate the nearest grid point by rounding to the nearest grid cell
            x = round((mouse_pos.x() + self.offset.x()) / zoomed_grid_size) * zoomed_grid_size - self.offset.x()
            y = round((mouse_pos.y() + self.offset.y()) / zoomed_grid_size) * zoomed_grid_size - self.offset.y()

            self.floating_image_pos = QPointF(x, y)
            self.update()  # Redraw to show the square at the new position

    def mouseReleaseEvent(self, event: QMouseEvent):
        # Stop dragging when the mouse button is released
        if event.button() == Qt.LeftButton and self.status == "grab":
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
        self.canvas.update()
        print("Grab selected")
        self.canvas.status = "grab"  # Enable grab mode
        self.canvas.update_cursor()  # Update cursor
        self.canvas.show_floating_image = False  # Hide the floating image
    
    def input_action(self, checked):
        print("Input selected")
        self.canvas.status = "input"  # Disable grab mode for wire placement
        self.canvas.update_cursor()  # Update cursor
        self.canvas.show_floating_image = True  # Show the floating image

    def output_action(self):
        self.canvas.update()
        print("Output selected")
        self.canvas.status = "output"  # Disable grab mode for wire placement
        self.canvas.update_cursor()  # Update cursor
        self.canvas.show_floating_image = True  # Hide the floating image

    def wire_action(self):
        self.canvas.update()
        print("Wire selected")
        self.canvas.status = "wire"  # Disable grab mode for wire placement
        self.canvas.update_cursor()  # Update cursor
        self.canvas.show_floating_image = False  # Hide the floating image

    def beamsplitter_action(self):
        self.canvas.update()
        print("Beam splitter selected")
        self.canvas.status = "beamsplitter"  # Disable grab mode for beam splitter
        self.canvas.update_cursor()  # Update cursor
        self.canvas.show_floating_image = False  # Hide the floating image

if __name__ == "__main__":
    app = QApplication([])
    window = MainWindow()
    window.show()
    app.exec()
