"""
Contains the EventHandler class.
"""

from PySide6.QtWidgets import QRubberBand
from PySide6.QtCore import QObject, QEvent, Qt, QRect, QSize, QPoint
from PySide6.QtGui import QMouseEvent, QWheelEvent
from component import Select, Grab

class EventHandler(QObject):
    """
    Tracks and interprets mouse events on the canvas.
    """
    def __init__(self, canvas):
        super().__init__()
        self.canvas = canvas
        self.current_mouse_position = None
        self.mouse_pressed_position = None
        self.canvas.installEventFilter(self)
        self.dragging_enabled = False
        self.rubber_band = QRubberBand(QRubberBand.Rectangle, self.canvas)
        self.rubber_band_origin = None

    def eventFilter(self, obj, event):
        """
        Calls the corresponding action when a mouse event occurs on the canvas.
        """
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
        """
        Action to perform when a mouse press occurs on the canvas.
        """
        if event.button() == Qt.LeftButton:
            if isinstance(self.canvas.active_tool, Select):
                # Begin drawing the rectangular area selection
                self.rubber_band_origin = event.pos()
                self.rubber_band.setGeometry(QRect(self.rubber_band_origin, QSize()))
                self.rubber_band.show()

            elif isinstance(self.canvas.active_tool, Grab):
                self.start_dragging()

            elif self.canvas.active_tool.placeable:
                self.canvas.active_tool.place()

            # Remember where the mouse press occured
            self.mouse_pressed_position = event.position().toTuple()

        self.canvas.update()

    def handle_mouse_move(self, event: QMouseEvent):
        """
        Action to perform when the mouse is moved on the canvas.
        """
        if self.rubber_band_origin and isinstance(self.canvas.active_tool, Select):
            # Expand the rectangular area selection
            rect = QRect(self.rubber_band_origin, event.pos()).normalized()
            self.rubber_band.setGeometry(rect)

        if self.dragging_enabled:
            self.drag_canvas(event)
        
        # Update the mouse position
        self.current_mouse_position = event.position().toTuple()

        self.canvas.update()

    def handle_mouse_release(self, event: QMouseEvent):
        """
        Action to perform when the mouse button is released on the canvas.
        """
        if event.button() == Qt.LeftButton:
            # Hide the rectangular area selection and select all components inside the rectangle
            self.rubber_band.hide()
            selected_rect = self.rubber_band.geometry()
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
                
                # If the user clicked on a component without moving the mouse, then select that component
                if self.current_mouse_position == self.mouse_pressed_position:
                    for comp_list in self.canvas.placed_components.values():
                        for comp in comp_list:
                            if isinstance(self.canvas.active_tool, Select) and comp.contains(event.position().toTuple()):
                                comp.property_manager.draw(comp.position)
                                comp.set_selected(True)
                            else:
                                comp.set_selected(False)
            
            if self.dragging_enabled:
                self.stop_dragging()

        # Forget where the mouse press occured
        self.mouse_pressed_position = None

        self.canvas.update()

    def start_dragging(self):
        """
        Start dragging the canvas
        """
        self.dragging_enabled = True
        self.canvas.active_tool.set_dragging_cursor()

    def drag_canvas(self, event):
        """
        Drag the canvas along with the mouse movement
        """
        delta_x = event.position().toTuple()[0] - self.current_mouse_position[0]
        delta_y = event.position().toTuple()[1] - self.current_mouse_position[1]
        delta = (delta_x, delta_y)
        self.canvas.drag(delta)

    def stop_dragging(self):
        """
        Stop dragging the canvas
        """
        self.canvas.active_tool.set_cursor()
        self.dragging_enabled = False

    def handle_enter(self, event):
        """
        Action to perform when the mouse enters the canvas.
        """
        # Begin tracking the mouse position
        self.current_mouse_position = event.position().toTuple()

        # Set the cursor depending on which tool is selected
        self.canvas.active_tool.set_cursor()

        # Show a preview of the selected component
        self.canvas.enablePreview()

        self.canvas.update()

    def handle_leave(self, event):
        """
        Action to perform when the mouse leaves the canvas.
        """
        # Stop tracking the mouse position
        self.current_mouse_position = None

        # Reset the cursor
        self.canvas.setCursor(Qt.ArrowCursor)

        # Hide the component being previewed
        self.canvas.disablePreview()

        self.canvas.update()

    def handle_wheel(self, event: QWheelEvent):
        """
        Action to perform when the mouse wheel scrolls on the canvas.
        """
        # Zoom the canvas
        zoom_delta = event.angleDelta().y() / 120
        self.canvas.zoom(zoom_delta)
        self.canvas.update()