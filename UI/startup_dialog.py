from PySide6.QtWidgets import (
    QApplication, QFileDialog, QLineEdit, QRadioButton, QGroupBox, QDialog,
    QVBoxLayout, QHBoxLayout, QListWidget, QStackedWidget, QWidget, QLabel, QPushButton
)
from PySide6.QtGui import QPixmap
from PySide6.QtCore import Qt
import os

class StartupDialog(QDialog):
    """
    Dialog that appears immediately on starting the application. Contains options for 
    creating new circuits and opening .circ files.
    """
    NEW_CIRCUIT = "New circuit"
    OPEN = "Open"
    WIDTH = 600
    HEIGHT = 200
    NAV_WIDTH = 150

    def __init__(self):
        super().__init__()
        self.setup_ui()

    def setup_ui(self):
        self.setWindowTitle("Choose a circuit")
        self.set_geometry()
        main_layout = QVBoxLayout(self)

        # Initialize confirm button first so it can be passed to pages
        self.confirm_button = self.create_confirm_button()
        confirm_layout = QHBoxLayout()
        confirm_layout.addStretch()
        confirm_layout.addWidget(self.confirm_button)

        # Initialize content and navigation
        self.content = self.create_content_widget()
        self.navigation = self.create_navigation_widget([self.NEW_CIRCUIT, self.OPEN])

        # Layouts for navigation and content
        nav_content_layout = QHBoxLayout()
        nav_content_layout.addWidget(self.navigation)
        nav_content_layout.addWidget(self.content)

        # Assemble layouts
        main_layout.addLayout(nav_content_layout)
        main_layout.addLayout(confirm_layout)

        # Initial confirm button state
        self.update_confirm_button_state()

    def set_geometry(self):
        screen = QApplication.primaryScreen().geometry()
        self.setGeometry(
            (screen.width() - self.WIDTH) // 2,
            (screen.height() - self.HEIGHT) // 4,
            self.WIDTH, self.HEIGHT
        )

    def create_navigation_widget(self, items):
        """Create the navigation panel on the left hand side, which is used to choose between pages."""
        nav = QListWidget()
        nav.addItems(items)
        nav.setFixedWidth(self.NAV_WIDTH)
        nav.setCurrentRow(0)
        nav.currentRowChanged.connect(self.content.setCurrentIndex)
        nav.currentRowChanged.connect(self.update_confirm_button_state)
        return nav

    def create_content_widget(self):
        """Create the main content area which displays the current page."""
        content = QStackedWidget()

        # Create individual pages
        self.new_circuit_page = NewCircuitPage()
        self.open_circuit_page = OpenCircuitPage()

        # Add pages to the stack
        content.addWidget(self.new_circuit_page)
        content.addWidget(self.open_circuit_page)

        # Associate confirm button with pages
        self.new_circuit_page.set_confirm_button(self.confirm_button)
        self.open_circuit_page.set_confirm_button(self.confirm_button)

        return content

    def create_confirm_button(self):
        button = QPushButton("Confirm")
        button.clicked.connect(self.on_confirm_clicked)
        return button

    def on_confirm_clicked(self):
        """
        Determines the action to take when the confirm button is clicked. The action
        varies depending on which page is currently selected.
        """
        if self.current_page == self.NEW_CIRCUIT:
            self.new_circuit_page.on_confirm_clicked()
            self.accept()
        elif self.current_page == self.OPEN:
            self.open_circuit_page.on_confirm_clicked()
            self.accept()

    @property
    def current_page(self):
        return self.navigation.currentItem().text()

    def update_confirm_button_state(self):
        if self.current_page == self.NEW_CIRCUIT:
            self.new_circuit_page.update_confirm_button_state()
        elif self.current_page == self.OPEN:
            self.open_circuit_page.update_confirm_button_state()

    def get_selected_data(self):
        """
        Return the selected data (simulation type and/or file path).
        This method is called after the dialog is accepted.
        """
        if self.current_page == self.NEW_CIRCUIT:
            return self.new_circuit_page.simulation_type, None
        elif self.current_page == self.OPEN:
            return None, self.open_circuit_page.file_path_input.text().strip()


class BasePage(QWidget):
    """Base class for pages in the dialog."""
    def __init__(self, parent=None):
        super().__init__(parent)

    def set_confirm_button(self, button: QPushButton):
        """Associate a confirmation button with the page."""
        self.confirm_button = button


class NewCircuitPage(BasePage):
    """Create a new circuit by selecting a type of simulation and clicking the confirm button."""

    SIMULATION_TYPES = ["Photonic simulation", "Gate-based simulation"]

    def __init__(self):
        super().__init__()
        self.simulation_type = "photonic"
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.addWidget(self.create_simulation_groupbox())

    def create_simulation_groupbox(self):
        """Group box for choosing a simulation method. Different methods have different component types and backends."""
        group_box = QGroupBox("Choose a simulation type")
        group_layout = QVBoxLayout(group_box)

        for sim_type in self.SIMULATION_TYPES:
            button = QRadioButton(sim_type)
            button.toggled.connect(lambda checked, sim_type=sim_type: self.on_simulation_type_changed(sim_type) if checked else None)
            group_layout.addWidget(button)

        # Select the first type by default
        group_layout.itemAt(0).widget().setChecked(True)
        return group_box

    def on_simulation_type_changed(self, sim_type):
        self.simulation_type = sim_type.split()[0].lower()

    def update_confirm_button_state(self):
        """The confirmation button on this page is always unlocked."""
        if hasattr(self, 'confirm_button'):
            self.confirm_button.setEnabled(True)

    def on_confirm_clicked(self):
        pass


class OpenCircuitPage(BasePage):
    """Open a circuit from a .circ file."""

    def __init__(self):
        super().__init__()
        self.file_path_to_open = None
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("Enter file path or select a file:"))
        layout.addLayout(self.create_file_input_layout())

    def create_file_input_layout(self):
        """Creates a widget where the user can choose a file to open by either entering the file path or using a dialog."""
        layout = QHBoxLayout()

        self.file_path_input = QLineEdit()
        self.file_path_input.setPlaceholderText("Enter file path here...")
        self.file_path_input.textChanged.connect(self.update_confirm_button_state)
        layout.addWidget(self.file_path_input)

        browse_button = QPushButton("Browse")
        browse_button.clicked.connect(self.open_file_dialog)
        layout.addWidget(browse_button)

        return layout

    def open_file_dialog(self):
        """Open the file selection dialog."""
        current_path = os.path.dirname(os.path.abspath(__file__))
        file, _ = QFileDialog.getOpenFileName(
            self, "Open circuit", current_path, "Circ Files (*.circ);;All Files (*)"
        )
        if file:
            self.file_path_input.setText(file)

    def update_confirm_button_state(self):
        """Unlock the confirmation button if a valid file is chosen."""
        if hasattr(self, 'confirm_button'):
            file_path = self.file_path_input.text().strip()
            self.confirm_button.setEnabled(bool(file_path and os.path.exists(file_path)))

    def on_confirm_clicked(self):
        self.file_path_to_open = self.file_path_input.text().strip()
