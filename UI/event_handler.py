from PySide6.QtCore import QObject, QEvent, Qt
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
                pass

            elif isinstance(self.canvas.active_tool, Grab):
                self.dragging_enabled = True
                self.previous_mouse_position = event.position().toTuple()
                self.canvas.active_tool.set_dragging_cursor()

            elif self.canvas.active_tool.placeable:
                self.canvas.active_tool.place()

            self.mouse_pressed_position = event.position().toTuple()

        self.canvas.update()

    def handle_mouse_move(self, event: QMouseEvent):
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

    def handle_wheel(self, event):
        zoom_delta = event.angleDelta().y() / 120
        self.canvas.zoom(zoom_delta)
        self.canvas.update()