import sys
from PySide6.QtWidgets import QApplication, QWidget, QVBoxLayout, QLabel, QGraphicsBlurEffect
from PySide6.QtCore import Qt
from PySide6.QtGui import QPainter, QColor, QBrush
from PySide6.QtCore import Qt

class BlurWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setAttribute(Qt.WA_TranslucentBackground)
        # 去掉窗口边框
        self.setWindowFlag(Qt.FramelessWindowHint)

        layout = QVBoxLayout()
        self.label = QLabel("主窗口", self)
        self.label.setAlignment(Qt.AlignCenter)

        self.setStyleSheet("""
            font-size: 20px;
            padding: 20px;
            border: none;
        """)
        self.style_args = {
            "background-color": QColor(40, 40, 40, 230),
            "font-size": "16px",
            "padding": "10px",
            "border-radius": 10
        }

        layout.addWidget(self.label)
        self.setLayout(layout)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        brush = QBrush(self.style_args["background-color"])
        painter.setBrush(brush)
        painter.setPen(Qt.NoPen)
        painter.drawRoundedRect(self.rect(), self.style_args["border-radius"], self.style_args["border-radius"])

class BottomBar(QWidget):
    def __init__(self):
        super().__init__()
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setWindowFlag(Qt.FramelessWindowHint)

        self.style_args = {
            "background-color": QColor(20, 20, 20, 200),
            "font-size": "16px",
            "padding": "10px",
            "border-radius": 10
        }


    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        brush = QBrush(self.style_args["background-color"])
        painter.setBrush(brush)

        # 去掉边框
        painter.setPen(Qt.NoPen)

        painter.drawRoundedRect(self.rect(), self.style_args["border-radius"], self.style_args["border-radius"])

class NormalButton(QPushButton):
    def __init__(self, text):
        super().__init__(text)
        self.setStyleSheet("""
            QPushButton {
                background-color: rgba(255, 255, 255, 40);
                color: white;
                border: none;
                padding: 6px 14px;
                border-radius: 6px;
            }
            QPushButton:hover {
                background-color: rgba(255, 255, 255, 70);
            }
        """)


