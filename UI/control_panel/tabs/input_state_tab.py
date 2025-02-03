from PySide6.QtWidgets import QWidget, QTableWidget, QCheckBox, QLineEdit, QHBoxLayout, QVBoxLayout, QTableWidgetItem, QLabel
from PySide6.QtGui import QBrush, QColor
from PySide6.QtCore import Qt
import numpy as np

class InputStateTab(QWidget):
    def __init__(self, window):
        super().__init__()
        self.window = window

        self.title = "Input state"

        self.gram_table = QTableWidget()
        self.uniform_checkbox = QCheckBox("Uniform")
        self.uniform_textbox = QLineEdit("1")

        # Uniform layout
        uniform_layout = QHBoxLayout()
        uniform_layout.addWidget(self.uniform_checkbox)
        uniform_layout.addWidget(self.uniform_textbox)

        # Gram tab layout
        gram_tab_layout = QVBoxLayout()

        # Temporary incomplete message, until distinguishability is added
        # gram_tab_layout.addWidget(self.gram_table)
        # gram_tab_layout.addLayout(uniform_layout)
        under_construction_label = QLabel("Custom input states are not implemented yet for this backend.")
        under_construction_label.setWordWrap(True)
        gram_tab_layout.addWidget(under_construction_label)

        self.setLayout(gram_tab_layout)

        self.uniform_checkbox.stateChanged.connect(self.update_obbm)
        self.gram_table.itemChanged.connect(self.update_gram_matrix_colors)
        self.uniform_textbox.editingFinished.connect(self.update_obbm)

        self.green = (109, 191, 115)
        self.gray = (100, 100, 100)
        self.indist_color = self.green

    def set_gram_matrix(self):
        self.gram_table.setRowCount(self.window.canvas.n_photons)
        self.gram_table.setColumnCount(self.window.canvas.n_photons)
        self.gram_table.blockSignals(True) # stop colors from updating on items being added
        for row in range(self.window.canvas.n_photons):
            for col in range(self.window.canvas.n_photons):
                item_value = self.window.canvas.gram_matrix[row, col]
                formatted_value = str(item_value).rstrip("0").rstrip(".")
                item = QTableWidgetItem(formatted_value)
                if row == col:
                    item.setFlags(Qt.ItemIsSelectable | Qt.ItemIsEnabled)
                else:
                    item.setFlags(Qt.ItemIsSelectable | Qt.ItemIsEnabled | Qt.ItemIsEditable)
                item.setBackground(QBrush(QColor(*self.indist_color)))
                self.gram_table.setItem(row, col, item)
        
        for col in range(self.window.canvas.n_photons):
            self.gram_table.setColumnWidth(col, 40)

        self.gram_table.blockSignals(False)

        # Temporarily disable this tab until distinguishability is implemented
        self.lock_gram_matrix()

    def update_gram_matrix(self):
        if self.uniform_checkbox.isChecked():
            uniform_overlap = float(self.uniform_textbox.text())
            self.window.canvas.gram_matrix = np.eye(self.window.canvas.n_photons)*(1 - uniform_overlap) + uniform_overlap*np.ones((self.window.canvas.n_photons, self.window.canvas.n_photons))
        else:
            self.window.canvas.gram_matrix = np.ones((self.window.canvas.n_photons, self.window.canvas.n_photons))

        self.set_gram_matrix()

    def update_gram_matrix_colors(self, item):
        self.gram_table.blockSignals(True)
        try:
            item_value = float(item.text())
            if item_value > 1:
                item.setText("1")
                item_value = 1
            elif item_value < 0:
                item.setText("0")
                item_value = 0
        except ValueError:
            item.setText("1")
            item_value = 1

        # round trailing zeros
        formatted_value = str(item_value).rstrip("0").rstrip(".")
        item.setText(formatted_value)

        # gram matrix must be symmetrical
        row = self.gram_table.row(item)
        col = self.gram_table.column(item)
        symmetrical_item = self.gram_table.item(col, row)
        symmetrical_item.setText(item.text())

        self.window.canvas.gram_matrix[row, col] = float(item_value)
        self.window.canvas.gram_matrix[col, row] = float(item_value)
        self.window.console.refresh()

        self.gram_table.blockSignals(False)

        # scale color with value, decaying faster when closer to 1
        red = self.indist_color[0]*item_value**4
        green = self.indist_color[1]*item_value**4
        blue = self.indist_color[2]*item_value**4
        item.setBackground(QBrush(QColor(red, green, blue)))
        symmetrical_item.setBackground(QBrush(QColor(red, green, blue)))

        self.window.mark_unsaved_changes()

    def update_obbm(self):
        if self.uniform_checkbox.isChecked():
            self.uniform_textbox.setReadOnly(False)
            self.indist_color = self.gray
            for row in range(self.gram_table.rowCount()):
                for col in range(self.gram_table.columnCount()):
                    item = self.gram_table.item(row, col)
                    if row != col:
                        item.setText(self.uniform_textbox.text())
                        item.setFlags(Qt.ItemIsSelectable | Qt.ItemIsEnabled)
                    else:
                        item.setFlags(Qt.ItemIsSelectable | Qt.ItemIsEnabled)
        else:
            self.uniform_textbox.setReadOnly(True)
            self.indist_color = self.green
            for row in range(self.gram_table.rowCount()):
                for col in range(self.gram_table.columnCount()):
                    item = self.gram_table.item(row, col)
                    if row == col:
                        item.setFlags(Qt.ItemIsSelectable | Qt.ItemIsEnabled)
                    else:
                        item.setFlags(Qt.ItemIsSelectable | Qt.ItemIsEnabled | Qt.ItemIsEditable)
                        
    def lock_gram_matrix(self):
        self.uniform_checkbox.setEnabled(False)
        self.uniform_textbox.setEnabled(False)

        self.indist_color = self.gray
        for row in range(self.gram_table.rowCount()):
            for col in range(self.gram_table.columnCount()):
                item = self.gram_table.item(row, col)

                item.setFlags(Qt.ItemIsSelectable | Qt.ItemIsEnabled)

                item.setText("1")
                item_value = 1

                self.window.canvas.gram_matrix[row, col] = float(item_value)

    def unlock_gram_matrix(self):
        self.uniform_checkbox.setEnabled(True)
        self.uniform_textbox.setEnabled(True)

        self.indist_color = self.green

        self.set_gram_matrix()