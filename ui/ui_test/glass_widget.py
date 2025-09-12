import sys
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QPainter, QBrush
from PySide6.QtWidgets import (
    QApplication, QWidget, QGraphicsBlurEffect, QVBoxLayout, QLabel
)


class FrostedGlassWidget(QWidget):
    def __init__(self, parent=None, blur_radius=10, background_color=QColor(255, 255, 255, 60)):
        super().__init__(parent)

        # 毛玻璃控件本身透明
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setWindowFlag(Qt.FramelessWindowHint)
        self.setAutoFillBackground(False)

        # 设置模糊效果
        blur = QGraphicsBlurEffect(self)
        blur.setBlurRadius(blur_radius)
        self.setGraphicsEffect(blur)

        # 背景颜色（半透明白色/黑色）
        self.background_color = background_color

        # 内容布局
        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 15, 15, 15)
        self.label = QLabel("🌫 毛玻璃控件", self)
        self.label.setStyleSheet("color: black; font-size: 16px;")
        layout.addWidget(self.label)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        # 绘制半透明背景矩形
        brush = QBrush(self.background_color)
        painter.setBrush(brush)
        painter.setPen(Qt.NoPen)
        painter.drawRoundedRect(self.rect(), 20, 20)



if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = FrostedGlassWidget()
    window.show()
    sys.exit(app.exec())
