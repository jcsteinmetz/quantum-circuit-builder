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
                "property_box_color": f"background-color: {QColor(*(0, 0, 0)).name()}; color: {QColor(*(255, 255, 255)).name()}",
            },
            "darkmode": {
                "face_color": (255, 255, 255),
                "border_color": (255, 255, 255),
                "selected_border_color": (219, 197, 119),
                "bg_color": (0, 0, 0),
                "gridline_color": (50, 50, 50),
                "error_color": (255, 0, 0),
                "name_color": (0, 0, 0),
                "property_box_color": f"background-color: {QColor(*(255, 255, 255)).name()}; color: {QColor(*(0, 0, 0)).name()}",
            }
        }

    def get_styles(self):
        return {
            "face_color": self.get_style("face_color"),
            "border_color": self.get_style("border_color"),
            "selected_border_color": self.get_style("selected_border_color"),
            "error_color": self.get_style("error_color"),
            "name_color": self.get_style("name_color"),
        }

    def set_theme(self, theme):
        if theme in self.styles:
            self.current_theme = theme
            self.update_styles()
        else:
            raise ValueError(f"Theme '{theme}' not found.")

    def get_style(self, key):
        return self.styles[self.current_theme].get(key)
    
    def update_styles(self):
        self.window.canvas.update_styles()
        self.window.canvas.component_renderer.update_styles()

    def darkmode_toggle(self):
        if self.current_theme == "basic":
            self.set_theme("darkmode")
        elif self.current_theme == "darkmode":
            self.set_theme("basic")
        self.window.canvas.repaint()