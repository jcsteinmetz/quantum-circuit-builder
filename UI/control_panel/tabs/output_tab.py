import numpy as np
from PySide6.QtWidgets import QTextEdit, QTableWidget, QTableWidgetItem, QWidget, QStackedWidget, QVBoxLayout
from PySide6.QtCore import Qt

class OutputTab(QWidget):
    def __init__(self, window):
        super().__init__()
        self.window = window

        self.output_table = QTableWidget()
        self.output_table.setColumnCount(2)
        self.output_table.setHorizontalHeaderLabels(["Basis state", "Probability"])
        self.table_data = None

        # self.output_table = QTextEdit()
        # self.output_table.setReadOnly(True)

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
            self.table_data = self.window.interface.circuit.output_data
            self.table_data = np.vstack((self.table_data, ["Total", sum(float(i) for i in self.table_data[:, 1])]))
            n_rows = np.shape(self.table_data)[0]
            n_cols = np.shape(self.table_data)[1]
            self.output_table.setRowCount(n_rows)
            self.output_table.setColumnCount(n_cols)

            for row in range(n_rows):
                for col in range(n_cols):
                    entry = self.table_data[row, col]

                    if col == 0 and row != n_rows - 1:
                        entry = "|"+entry+">"

                    item = QTableWidgetItem()
                    item.setTextAlignment(Qt.AlignCenter)
                    item.setText(entry)
                    self.output_table.setItem(row, col, item)

            self.stacked_widget.setCurrentIndex(0)

        except Exception as e:
            self.print_exception(e)

    def print_exception(self, e):
        self.stacked_widget.setCurrentIndex(1)
        self.error_message.setText("\u274C ERROR: "+str(e))