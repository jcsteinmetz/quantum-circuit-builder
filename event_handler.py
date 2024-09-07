from PySide6.QtCore import Qt, QPointF, QObject, QEvent
from PySide6.QtGui import QColor, QWheelEvent, QMouseEvent
from components import WireStart

class EventHandler(QObject):
    def __init__(self, canvas):
        super().__init__()
        self.canvas = canvas
        self.last_mouse_pos = None
        self.canvas.installEventFilter(self)

    def eventFilter(self, obj, event):
        if obj == self.canvas:
            handlers = {
                QEvent.MouseButtonPress: self.handle_mouse_press,
                QEvent.MouseMove: self.handle_mouse_move,
                QEvent.MouseButtonRelease: self.handle_mouse_release,
                QEvent.Wheel: self.handle_wheel,
                QEvent.Enter: self.handle_enter,
                QEvent.Leave: self.handle_leave
            }
            handler = handlers.get(event.type())
            if handler:
                handler(event)
        return super().eventFilter(obj, event)

    def handle_mouse_press(self, event: QMouseEvent):
        if event.button() == Qt.LeftButton:
            if self.canvas.dragging_enabled:
                self.last_mouse_pos = event.position()
            elif self.canvas.active_tool and not self.canvas.active_tool.overlapping:
                self.canvas.active_tool.place()

    def handle_mouse_move(self, event: QMouseEvent):
        mouse_pos = event.position()

        if self.canvas.active_tool and self.canvas.active_tool.show_preview:
            self.canvas.active_tool.set_position(mouse_pos)

        # Redraw to show the square at the new position
        self.canvas.update()

        # Handle grid dragging when "Grab" is active
        if self.canvas.dragging_enabled and self.last_mouse_pos:
            delta = mouse_pos - self.last_mouse_pos
            self.canvas.drag(delta)
            self.last_mouse_pos = mouse_pos  # Update the last mouse position

    def handle_mouse_release(self, event: QMouseEvent):
        # Stop dragging when the mouse button is released
        if event.button() == Qt.LeftButton and self.canvas.dragging_enabled:
            self.last_mouse_pos = None

    def handle_wheel(self, event: QWheelEvent):
        # Calculate the zoom factor based on the wheel movement
        zoom_delta = event.angleDelta().y() / 120
        zoom_step = 0.1
        new_grid_size = self.canvas.grid.size * (1 + zoom_step * zoom_delta)
        self.canvas.zoom(event.position(), new_grid_size)

    def handle_enter(self, event):
        self.canvas.setCursor(self.canvas.active_tool.cursor)
        self.canvas.active_tool.show_preview = True
        self.canvas.update()

    def handle_leave(self, event):
        self.canvas.setCursor(Qt.ArrowCursor)
        self.canvas.active_tool.show_preview = False 
        self.canvas.update()
