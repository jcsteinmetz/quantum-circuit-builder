from PySide6.QtWidgets import QRubberBand
from PySide6.QtCore import QObject, QEvent, Qt, QRect, QSize, QPoint
from PySide6.QtGui import QMouseEvent, QWheelEvent
from copy import copy
from component import Select, Grab

class EventHandler(QObject):
    def __init__(self, canvas):
        super().__init__()
        self.canvas = canvas
        self.mouse_position = None
        self.previous_mouse_position = None
        self.canvas.installEventFilter(self)
        self.dragging_enabled = False
        self.mouse_pressed_position = None
        self.rubberBand = QRubberBand(QRubberBand.Rectangle, self.canvas)
        self.rubber_band_origin = None

    def eventFilter(self, obj, event):
        if obj == self.canvas:
            handlers = {
                QEvent.MouseButtonPress: self.handle_mouse_press,
                QEvent.MouseMove: self.handle_mouse_move,
                QEvent.MouseButtonRelease: self.handle_mouse_release,
                QEvent.Enter: self.handle_enter,
                QEvent.Leave: self.handle_leave,
                QEvent.Wheel: self.handle_wheel
            }
            handler = handlers.get(event.type())
            if handler:
                handler(event)
        return super().eventFilter(obj, event)
    
    def handle_mouse_press(self, event: QMouseEvent):
        if event.button() == Qt.LeftButton:
            if isinstance(self.canvas.active_tool, Select):
                self.rubber_band_origin = event.pos()
                self.rubberBand.setGeometry(QRect(self.rubber_band_origin, QSize()))
                self.rubberBand.show()

            elif isinstance(self.canvas.active_tool, Grab):
                self.dragging_enabled = True
                self.previous_mouse_position = event.position().toTuple()
                self.canvas.active_tool.set_dragging_cursor()

            elif self.canvas.active_tool.placeable:
                self.canvas.active_tool.place()

            self.mouse_pressed_position = event.position().toTuple()

        self.canvas.update()

    def handle_mouse_move(self, event: QMouseEvent):
        if self.rubber_band_origin and isinstance(self.canvas.active_tool, Select):
            rect = QRect(self.rubber_band_origin, event.pos()).normalized()
            self.rubberBand.setGeometry(rect)
        if self.dragging_enabled:
            delta_x = event.position().toTuple()[0] - self.mouse_position[0]
            delta_y = event.position().toTuple()[1] - self.mouse_position[1]
            delta = (delta_x, delta_y)
            self.canvas.drag(delta)
        
        self.previous_mouse_position = copy(self.mouse_position)
        self.mouse_position = event.position().toTuple()

        self.canvas.update()

    def handle_mouse_release(self, event: QMouseEvent):
        if event.button() == Qt.LeftButton:
            self.rubberBand.hide()
            selected_rect = self.rubberBand.geometry()
            for comp_list in self.canvas.placed_components.values():
                for comp in comp_list:
                    if hasattr(comp, "end_position"):
                        if selected_rect.contains(QPoint(*comp.position)) and selected_rect.contains(QPoint(*comp.end_position)):
                            comp.set_selected(True)
                        else:
                            comp.set_selected(False)
                    else:
                        if selected_rect.contains(QPoint(*comp.position)):
                            comp.set_selected(True)
                        else:
                            comp.set_selected(False)
                
                if self.mouse_position == self.mouse_pressed_position:
                    for comp_list in self.canvas.placed_components.values():
                        for comp in comp_list:
                            if isinstance(self.canvas.active_tool, Select) and comp.contains(event.position().toTuple()):
                                comp.property_manager.draw(comp.position)
                                comp.set_selected(True)
                            else:
                                comp.set_selected(False)
            
            if self.dragging_enabled:
                self.canvas.active_tool.set_cursor()
                self.previous_mouse_position = None
                self.dragging_enabled = False

        self.canvas.update()
        self.mouse_pressed_position = None

    def handle_enter(self, event):
        self.mouse_position = event.position().toTuple()
        self.canvas.active_tool.set_cursor()
        self.canvas.enablePreview()
        self.canvas.update()

    def handle_leave(self, event):
        self.mouse_position = None
        self.previous_mouse_position = None
        self.canvas.setCursor(Qt.ArrowCursor)
        self.canvas.disablePreview()
        self.canvas.update()

    def handle_wheel(self, event: QWheelEvent):
        zoom_delta = event.angleDelta().y() / 120
        self.canvas.zoom(zoom_delta)
        self.canvas.update()