from PySide6.QtWidgets import QTreeWidget, QTreeWidgetItem

class ComponentsTab(QTreeWidget):
    def __init__(self, window):
        super().__init__()
        self.window = window
        self.setColumnCount(2)
        self.setColumnWidth(0, 150)
        self.setHeaderLabels(["Property", "Value"])
        self.component_types = []
        self.itemClicked.connect(self.on_item_clicked)

    def on_item_clicked(self, item, column):
        comp_to_select = self.find_component_from_item(item)
        for comp in self.window.canvas.all_placed_components():
            if comp == comp_to_select:
                comp.toggle_selection(True)
            else:
                comp.toggle_selection(False)
        self.window.canvas.repaint()

    @property
    def unique_component_types(self):
        return list(set(self.component_types))
    
    def clear_components(self):
        self.clear()
        self.component_types = []

    def find_component_from_item(self, item):
        for comp in self.window.canvas.all_placed_components():
            parent_index, child_index = self.find_item_from_component(comp)
            if self.topLevelItem(parent_index).child(child_index) == item:
                return comp
                
    def find_item_from_component(self, comp):
        # Get component name
        parent_name = type(comp).__name__
        child_name = comp.name

        # Find component in tree
        parent_index = None
        child_index = None
        for i in range(self.topLevelItemCount()):
            test_parent = self.topLevelItem(i)
            if test_parent.text(0) == parent_name:
                parent_index = i
        if parent_index is not None:
            parent_item = self.topLevelItem(parent_index)
            for i in range(parent_item.childCount()):
                test_child = parent_item.child(i)
                if test_child.text(0) == child_name:
                    child_index = i
        
        return parent_index, child_index

    def toggle_selection(self, comp, selected):
        parent_index, child_index = self.find_item_from_component(comp)
        item = self.topLevelItem(parent_index).child(child_index)
        item.setSelected(selected)

    def save_expansion_state(self, item, state):
        key = item.text(0)
        state[key] = item.isExpanded()
        for i in range(item.childCount()):
            self.save_expansion_state(item.child(i), state)

    def restore_expansion_state(self, item, state):
        key = item.text(0)
        item.setExpanded(state.get(key, False))
        for i in range(item.childCount()):
            self.restore_expansion_state(item.child(i), state)
        
    def refresh(self):
        state = {}
        for i in range(self.topLevelItemCount()):
            self.save_expansion_state(self.topLevelItem(i), state)

        self.clear_components()
        for comp in self.window.canvas.all_placed_components():
            self.add_component(comp)
        
        for i in range(self.topLevelItemCount()):
            self.restore_expansion_state(self.topLevelItem(i), state)

    def add_component(self, comp):
        comp_type = type(comp).__name__
        parent_item = None

        # Find the parent item in the tree
        if comp_type not in self.unique_component_types:
            parent_item = QTreeWidgetItem([comp_type])
            self.addTopLevelItem(parent_item)
        else:
            for i in range(self.topLevelItemCount()):
                test_parent_item = self.topLevelItem(i)
                if test_parent_item.text(0) == comp_type:
                    parent_item = test_parent_item

        # Add the new child item
        child_item = QTreeWidgetItem([f"{comp_type[0]}{self.component_types.count(comp_type)+1}"])
        parent_item.addChild(child_item)

        # Add its properties
        for key, prop in comp.property_manager.properties.items():
            grandchild_item = QTreeWidgetItem([key, prop.text()])
            child_item.addChild(grandchild_item)

        self.component_types.append(comp_type)

    def update_property(self, component, property_name, property_value):
        # find component in tree
        parent_index, child_index = self.find_item_from_component(component)
        parent_item = self.topLevelItem(parent_index)
        child_item = parent_item.child(child_index)

        # find the property to update
        grandchild_item = None
        for i in range(child_item.childCount()):
            test_grandchild = child_item.child(i)
            if test_grandchild.text(0) == property_name:
                grandchild_item = test_grandchild

        # update the property
        if grandchild_item:
            grandchild_item.setText(1, str(property_value))

        self.window.mark_unsaved_changes()