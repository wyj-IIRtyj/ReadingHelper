import sys
from PySide6.QtWidgets import QApplication, QWidget, QVBoxLayout, QLabel, QGraphicsBlurEffect
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
            background-color: rgba(40, 40, 40, 230);
            font-size: 20px;
            padding: 20px;
            border-radius: 10px;
            border: none;
        """)

        layout.addWidget(self.label)
        self.setLayout(layout)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = BlurWindow()
    window.resize(400, 700)
    window.show()
    sys.exit(app.exec())
