from PySide6.QtGui import QColor

class StyleManager:
    def __init__(self, window):
        self.window = window

        self.current_theme = "darkmode"
        self.styles = {
            "basic": {
                "face_color": (0, 0, 0),
                "border_color": (0, 0, 0),
                "selected_border_color": (219, 197, 119),
                "bg_color": (255, 255, 255),
                "gridline_color": (0, 0, 0),
                "error_color": (255, 0, 0),
                "name_color": (255, 255, 255),
                "property_manager_color": f"background-color: {QColor(*(0, 0, 0)).name()}; color: {QColor(*(255, 255, 255)).name()}",
            },
            "darkmode": {
                "face_color": (255, 255, 255),
                "border_color": (255, 255, 255),
                "selected_border_color": (219, 197, 119),
                "bg_color": (0, 0, 0),
                "gridline_color": (50, 50, 50),
                "error_color": (255, 0, 0),
                "name_color": (0, 0, 0),
                "property_manager_color": f"background-color: {QColor(*(255, 255, 255)).name()}; color: {QColor(*(0, 0, 0)).name()}",
            }
        }

    def set_theme(self, theme):
        if theme in self.styles:
            self.current_theme = theme
            self.window.canvas.update_styles()
            self.window.canvas.component_renderer.update_styles()
        else:
            raise ValueError(f"Theme '{theme}' not found.")

    def get_style(self, key):
        return self.styles[self.current_theme].get(key)