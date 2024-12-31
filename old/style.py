from PySide6.QtGui import QColor

class StyleOptions:
    def __init__(self, style_choice):
        self.bg_color = None
        self.gridline_color = None
        self.overlap_color = QColor(255, 0, 0, 100)
        self.wirestart_color = QColor(0, 0, 255, 255)
        self.wireend_color = QColor(0, 255, 0, 255)
        self.wire_color = None
        self.wire_width = 3

        if style_choice == "basic":
            self.basic()

        elif style_choice == "darkmode":
            self.darkmode()
     
    def basic(self):
        self.bg_color = QColor(255, 255, 255)
        self.gridline_color = QColor(200, 200, 200)
        self.wire_color = QColor(0, 0, 0, 255)

    def darkmode(self):
        self.bg_color = QColor(0, 0, 0)
        self.gridline_color = QColor(50, 50, 50)
        self.wire_color = QColor(255, 255, 255, 255)

    
