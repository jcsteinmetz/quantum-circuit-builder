from PySide6.QtWidgets import QFormLayout, QLineEdit, QFrame
from PySide6.QtGui import QValidator

class PropertiesManager(QFrame):
    def __init__(self, component, parent=None):
        super().__init__(parent)

        self.component = component
        self.properties = {}

        self.layout = QFormLayout()
        self.setLayout(self.layout)
        self.hide()

    @property
    def offset(self):
        return (-self.width()/2, -2* self.component.shape_scale * self.component.window.canvas.grid.size)
    
    def add_property(self, property_name, update_property, initial_value, validator: QValidator):
        line_edit = QLineEdit(str(initial_value))
        line_edit.setValidator(validator)
        line_edit.editingFinished.connect(update_property)
        line_edit.returnPressed.connect(line_edit.clearFocus)
        line_edit.editingFinished.connect(lambda: self.component.window.control_panel.components_tab.update_property(self.component, property_name, line_edit.text()))
        self.layout.addRow(property_name, line_edit)
        self.properties[property_name] = line_edit

    def draw(self, component_position):
        self.move(int(component_position[0] + self.offset[0]), int(component_position[1]+self.offset[1]))
        if not self.isVisible():
            self.show()

    def showEvent(self, event):
        if self.properties:
            first_property = next(iter(self.properties.values()))
            first_property.setFocus()
            first_property.selectAll()