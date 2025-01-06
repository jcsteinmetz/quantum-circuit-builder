from PySide6.QtWidgets import QFormLayout, QLineEdit, QFrame
from PySide6.QtGui import QValidator
from PySide6.QtCore import QEvent

class PropertyBox(QFrame):
    def __init__(self, component, parent=None):
        super().__init__(parent)

        self.component = component
        self.properties = {}

        self.default_value = None

        self.line_edit = None
        self.layout = QFormLayout()
        self.setLayout(self.layout)
        self.hide()

    @property
    def offset(self):
        """Offset the property box from the component position to avoid overlapping."""
        return (-self.width()/2, -2 * self.component.shape_scale * self.component.window.canvas.grid.size)
    
    def add_property(self, property_name, default_value, validator: QValidator):
        """"
        Add a new property to the property box.
        
        property_name: name of the new property
        default_value: value to show by default when the property appears
        validator: which QValidator to use on any new input to this property
        """
        self.default_value = default_value
        self.line_edit = QLineEdit(str(self.default_value))
        self.properties[property_name] = self.line_edit
        self.line_edit.setValidator(validator)
        self.line_edit.returnPressed.connect(self.line_edit.clearFocus)
        self.line_edit.editingFinished.connect(lambda: self.on_editing_finished(property_name))
        self.layout.addRow(property_name, self.line_edit)

    def on_editing_finished(self, property_name):
        self.component.update_property(property_name)
        self.component.window.control_panel.components_tab.update_property(self.component, property_name, self.line_edit.text())

    def showEvent(self, event):
        """Show the property box and default to editing the first property."""
        if self.properties:
            first_property = next(iter(self.properties.values()))
            first_property.setFocus()
            first_property.selectAll()

    def draw(self):
        self.move(int(self.component.node_positions[0][0] + self.offset[0]), int(self.component.node_positions[0][1]+self.offset[1]))

        # Property manager style
        style = self.component.window.style_manager.get_style("property_box_color")
        self.setStyleSheet(style)
        
        if not self.isVisible() and self.properties:
            self.show()
