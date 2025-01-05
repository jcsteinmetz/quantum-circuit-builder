import traceback
from PySide6.QtWidgets import QTextEdit, QTableWidget, QWidget, QStackedWidget, QVBoxLayout

class OutputTab(QWidget):
    def __init__(self, window):
        super().__init__()
        self.window = window

        # self.output_table = QTableWidget()
        # self.output_table.setColumnCount(2)
        # self.output_table.setHorizontalHeaderLabels(["Basis state", "Probability"])

        self.output_table = QTextEdit()
        self.output_table.setReadOnly(True)

        self.error_message = QTextEdit()
        self.error_message.setReadOnly(True)

        # Table/error widget
        self.stacked_widget = QStackedWidget()
        self.stacked_widget.addWidget(self.output_table)
        self.stacked_widget.addWidget(self.error_message)

        layout = QVBoxLayout(self)
        layout.addWidget(self.stacked_widget)

        self.output_data = None

    def print_output(self):
        try:
            self.output_data = self.window.interface.circuit.state.output_data
            self.output_table.setPlainText(str(self.output_data))
            self.stacked_widget.setCurrentIndex(0)
        except Exception as e:
            self.print_exception(e)

    def print_exception(self, e):
        self.stacked_widget.setCurrentIndex(1)
        self.error_message.setText("\u274C ERROR: "+str(e))