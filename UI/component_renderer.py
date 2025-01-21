from PySide6.QtCore import Qt, QPointF, QRectF
from PySide6.QtGui import QColor, QPen

class ComponentRenderer:
    """Contains methods for displaying components on the canvas."""

    SHAPE_METHODS = {
        "square": "draw_square",
        "circle": "draw_ellipse",
        "half circle": "draw_half_circle",
        "X": "draw_X",
        "diagonal line": "draw_diagonal_line",
        "arrow": "draw_arrow",
    }

    def __init__(self, window):
        self.window = window
        self.update_node_styles()
        self.line_width = 3
        self.shape_type = ["square"]

    # Style

    def _transparent(self, col):
        return (col[0], col[1], col[2], 128)
    
    def update_node_styles(self):
        styles = self.window.style_manager.get_node_styles()
        self.face_color = styles["face_color"]
        self.border_color = styles["border_color"]
        self.selected_border_color = styles["selected_border_color"]
        self.error_color = styles["error_color"]
        self.name_color = styles["name_color"]

    def set_painter_style(self, painter, pen_color=None, brush_color=None, transparent=False):
        """
        Set the style for drawing components.
        pen_color (tuple): color for shape borders and lines
        brush_color (tuple): color for filling in shapes
        transparent (bool): make the shape 50% transparent
        """
        if not pen_color:
            pen_color = self.border_color
        if not brush_color:
            brush_color = self.face_color

        if transparent:
            pen_color = self._transparent(pen_color)
            brush_color = self._transparent(brush_color)

        pen = QPen(QColor(*pen_color))
        pen.setWidth(self.line_width)
        painter.setPen(pen)

        painter.setBrush(QColor(*brush_color))

    # Drawing

    def draw_name(self, painter, comp):
        """Display a component's name on top of the component shape."""
        name_position = comp.node_positions[0]
        self.set_painter_style(painter, pen_color = self.name_color)
        scale = comp.shape_scale * self.window.canvas.grid.size
        rectangle = QRectF(name_position[0] - 0.5*scale, name_position[1] - 0.5*scale, scale, scale)
        painter.drawText(rectangle, Qt.AlignCenter, comp.name)

    def draw_property_box(self, comp):
        comp.property_box.draw()

    def draw_square(self, painter, pos, scale):
        half_scale = 0.5*scale

        bottom_left = QPointF(pos.x() - half_scale, pos.y() - half_scale)
        painter.drawRect(bottom_left.x(), bottom_left.y(), scale, scale)

    def draw_ellipse(self, painter, pos, scale):
        painter.drawEllipse(pos, 0.5*scale, 0.5*scale)

    def draw_half_circle(self, painter, pos, scale):
        rectangle = QRectF(pos.x() - 0.75*scale, pos.y() - 0.5*scale, scale, scale)
        start_angle = -90 * 16 # in 16ths of a degree
        span_angle = 180 * 16
        painter.drawPie(rectangle, start_angle, span_angle)

    def draw_X(self, painter, pos, scale):
        half_scale = 0.5*scale
        quarter_scale = 0.25*scale

        bottom_left = QPointF(pos.x() - half_scale, pos.y() - half_scale)
        top_left = QPointF(pos.x() - half_scale, pos.y() + half_scale)
        bottom_right = QPointF(pos.x() + half_scale, pos.y() - half_scale)
        top_right = QPointF(pos.x() + half_scale, pos.y() + half_scale)

        painter.drawLine(bottom_left, top_right)
        painter.drawLine(top_left, bottom_right)
        painter.drawEllipse(pos, quarter_scale, quarter_scale)
    
    def draw_diagonal_line(self, painter, pos, scale):
        half_scale = 0.5*scale
        quarter_scale = 0.25*scale

        bottom_left = QPointF(pos.x() - half_scale, pos.y() - half_scale)
        top_right = QPointF(pos.x() + half_scale, pos.y() + half_scale)
        painter.drawLine(bottom_left, top_right)
        painter.drawEllipse(pos, quarter_scale, quarter_scale)

    def draw_arrow(self, painter, pos, scale):
        half_scale = 0.5*scale
        bottom_left = QPointF(pos.x() - half_scale, pos.y() - half_scale)
        top_left = QPointF(pos.x() - half_scale, pos.y() + half_scale)

        painter.drawLine(bottom_left, pos)
        painter.drawLine(top_left, pos)

    def draw_shape(self, painter, comp, pos, shape_type):
        scale = comp.shape_scale * self.window.canvas.grid.size

        pos = QPointF(pos[0], pos[1])

        draw_method_name = self.SHAPE_METHODS.get(shape_type)
        if draw_method_name:
            draw_method = getattr(self, draw_method_name)
            draw_method(painter, pos, scale)

    def set_component_style(self, painter, comp):
        if comp.is_selected:
            self.set_painter_style(painter, pen_color=self.selected_border_color)
        else:
            self.set_painter_style(painter)

    def draw_wire(self, painter, comp, start_position, end_position):
        self.set_component_style(painter, comp)
        painter.drawLine(QPointF(start_position[0], start_position[1]), QPointF(end_position[0], end_position[1]))

    def draw_node(self, painter, comp, position, shape_type):
        self.set_component_style(painter, comp)
        self.draw_shape(painter, comp, position, shape_type)

    def draw(self, painter, comp):
        """Draws a component on the canvas."""
        for j, pos in enumerate(reversed(comp.node_positions)):
            i = len(comp.node_positions) - 1 - j
            if pos:
                if i != 0:
                    self.draw_wire(painter, comp, comp.node_positions[i-1], pos)
                self.draw_node(painter, comp, pos, comp.shape_type[i])
        self.draw_name(painter, comp)

        if comp.is_selected and comp.is_only_selected_component():
            self.draw_property_box(comp)

    def preview(self, painter, comp):
        """Draws a preview of the component that follows the mouse around while snapping to the grid."""
        for i, pos in enumerate(comp.node_positions):
            if pos:
                # draw node
                self.set_painter_style(painter)
                self.draw_shape(painter, comp, pos, comp.shape_type[i])
            else:
                # draw final node, which moves with the mouse
                brush_color = self.error_color if not comp.placeable else None
                self.set_painter_style(painter, brush_color=brush_color, transparent=True)
                self.draw_shape(painter, comp, comp.potential_placement, comp.shape_type[i])

                # draw wire
                if i != 0:
                    previous_pos = comp.node_positions[i-1]
                    painter.drawLine(QPointF(previous_pos[0], previous_pos[1]), QPointF(comp.potential_placement[0], comp.potential_placement[1]))

            if not pos:
                break