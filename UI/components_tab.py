from PySide6.QtWidgets import QTreeWidget, QTreeWidgetItem

class ComponentsTab(QTreeWidget):
    def __init__(self, window):
        super().__init__()
        self.window = window
        self.setColumnCount(2)
        self.setColumnWidth(0, 150)
        self.setHeaderLabels(["Property", "Value"])
        self.component_types = []
        # self.itemClicked.connect(self.on_item_clicked)

    def select_item(self, item):
        pass

    def deselect_item(self, item):
        pass