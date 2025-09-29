
import sys
from PySide6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QScrollArea, QSizePolicy
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QMouseEvent, QPainter, QColor, QBrush

from PySide6.QtWidgets import QWidget, QGraphicsOpacityEffect
from PySide6.QtCore import Qt
from PySide6.QtGui import QPainter, QColor, QBrush
from PySide6.QtWidgets import QApplication, QWidget, QVBoxLayout, QLabel, QGraphicsBlurEffect, QPushButton, QMainWindow, QTextEdit
from PySide6.QtCore import Qt, QRect, QPropertyAnimation, QEasingCurve, QTimer, Signal, Property, QPoint, QParallelAnimationGroup
from PySide6.QtGui import QPainter, QTextCursor, QTextDocument, QFont, QColor, QPen, QTextCharFormat, QPalette, QBrush

import re
import sys
import time
import jieba
import spacy
import threading

class VocabularyCard(QWidget):
    def __init__(self, radius=5, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WA_TranslucentBackground)  # 半透明背景
        self.setWindowFlag(Qt.FramelessWindowHint) # type: ignore
        self.setMouseTracking(True)
        
        # 设置窗口可调整大小
        self.setGeometry(200, 200, 200, 200)

        # 卡片样式配置
        self.style_args = {
            "background-color": QColor(40, 40, 40, 30),
            "font-color": QColor(240, 240, 240),
            "border-radius": radius,
            "padding": 12
        }


    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        brush = QBrush(self.style_args["background-color"])
        painter.setBrush(brush)
        painter.setPen(Qt.NoPen)
        painter.drawRoundedRect(self.rect(), self.style_args["border-radius"], self.style_args["border-radius"])
        painter.end()

    


if __name__ == "__main__":
    app = QApplication(sys.argv)
    cards = []
    for i in range(6):
        radius = 5 + i * 10
        card = VocabularyCard(radius=radius)
        card.setWindowTitle(f"VocabularyCard radius={radius}")
        card.move(220, 220)
        card.resize(200, 200)
        card.show()
        cards.append(card)
    sys.exit(app.exec())