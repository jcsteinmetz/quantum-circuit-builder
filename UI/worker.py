from PySide6.QtWidgets import QProgressBar, QWidget, QVBoxLayout
from PySide6.QtCore import QThread, Signal, Slot, QTimer

class ProgressBar(QWidget):
    """
    Progress bar that appears underneath the console as a visual indicator that the application is currently running.
    """
    def __init__(self, window):
        super().__init__()
        self.window = window

        # Create widgets
        self.progress_bar = self.create_progress_bar()
        
        self.timer = QTimer(self)

        layout = QVBoxLayout()
        layout.addWidget(self.progress_bar)
        self.setLayout(layout)
        self.hide()

    def create_progress_bar(self):
        progress_bar = QProgressBar()
        progress_bar.setRange(0, 100)
        progress_bar.setValue(0)
        return progress_bar
    
class WorkerThread(QThread):
    finished = Signal()
    error_occurred = Signal(str)

    def __init__(self, window, parent=None):
        super().__init__(parent)
        self.window = window
        self.finished.connect(self.on_task_finished)
        self.error_occurred.connect(self.print_error)

        self.error_flag = 0

    def print_error(self, message):
        self.window.control_panel.output_tab.print_exception(message)
        self.error_flag = 1

    def run(self):
        self.error_flag = 0
        try:
            self.window.interface.build_circuit()
            self.window.interface.run_circuit()
        except Exception as e:
            self.error_occurred.emit(str(e))

    @Slot()
    def start_task(self):
        for comp in self.window.canvas.all_placed_components():
            comp.property_box.hide()
        self.window.running = True
        self.window.update_title()

        self.window.progress_bar.show()
        self.window.progress_bar.progress_bar.setRange(0, 0)
        self.window.progress_bar.timer.start(15000)
        self.start()

    @Slot()
    def on_task_finished(self):
        self.hide_progress_bar()

        self.window.control_panel.setCurrentWidget(self.window.control_panel.output_tab)
        self.window.running = False
        self.window.update_title()

        if not self.error_flag:
            self.window.control_panel.output_tab.print_output()

    def hide_progress_bar(self):
        self.window.progress_bar.progress_bar.setRange(0, 100)
        self.window.progress_bar.progress_bar.setValue(100)
        self.window.progress_bar.timer.stop()
        self.window.progress_bar.hide()
