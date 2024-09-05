from PySide6.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QPushButton
from PySide6.QtCore import Qt, QEvent
from PySide6.QtGui import QPainter, QColor, QWheelEvent

class GridCanvas(QWidget):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.grid_size = 100  # Size of each grid cell
        self.zoom_factor = 1.0  # Initial zoom factor

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setPen(QColor(200, 200, 200))  # Light gray color for grid lines

        # Apply zoom factor to grid size
        zoomed_grid_size = self.grid_size * self.zoom_factor

        # Draw vertical grid lines around cursor position
        for x in range(0, self.width(), int(zoomed_grid_size)):
            painter.drawLine(x, 0, x, self.height())

        # Draw horizontal grid lines around cursor position
        for y in range(0, self.height(), int(zoomed_grid_size)):
            painter.drawLine(0, y, self.width(), y)

    def wheelEvent(self, event: QWheelEvent):
        # Zoom in or out based on the wheel movement
        zoom_delta = event.angleDelta().y() / 120  # Standardized wheel delta value
        zoom_step = 0.1  # Amount of zoom per step
        new_zoom_factor = self.zoom_factor + (zoom_step * zoom_delta)
        
        # Ensure the zoom factor is within reasonable bounds
        if 0.1 <= new_zoom_factor <= 5.0:
            self.zoom_factor = new_zoom_factor
            self.update()  # Trigger a redraw with the new zoom factor

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

        # Create canvas widget
        canvas = GridCanvas()
        canvas.setStyleSheet("background-color: white;")  # Set background color to white

        # Add widgets to the layout
        layout.addWidget(self.control_panel)
        layout.addWidget(canvas)

        self.setWindowTitle("Circuit builder")
        self.resize(800, 600)

        # Install event filter to detect clicks anywhere
        self.installEventFilter(self)

if __name__ == "__main__":
    app = QApplication([])
    window = MainWindow()
    window.show()
    app.exec()