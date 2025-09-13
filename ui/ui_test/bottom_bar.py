import sys
from PySide6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QLabel, QScrollArea, QSizePolicy
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QPainter, QColor, QBrush

from PySide6.QtWidgets import QWidget
from PySide6.QtCore import Qt
from PySide6.QtGui import QPainter, QColor, QBrush

sample_original_text = "Remarkable new treatments can free millions of kids and adults from the deadly threat of peanut allergy, tackling one of our fastest-growing medical problems"
sample_translated_text = "令人瞩目的新疗法可以使数百万儿童和成人摆脱花生过敏的致命威胁，解决我们增长最快的医疗问题之一"

class SplitLine(QWidget):
    def __init__(self, thickness=1, color=QColor(255, 255, 255, 100), parent=None):
        """
        分隔线控件
        
        Args:
            thickness (int): 线条粗细，默认2px
            color (QColor): 线条颜色，默认半透明白色
            parent: 父控件
        """
        super().__init__(parent)
        self.thickness = thickness
        self.color = color
        
        # 设置固定高度为线条粗细
        self.setFixedHeight(thickness)
        
        # 设置水平拉伸策略，自动占据父级容器横向宽度
        self.setSizePolicy(
            QSizePolicy.Policy.Expanding,  # 水平方向扩展
            QSizePolicy.Policy.Fixed       # 垂直方向固定
        )
        
        # 设置背景透明
        self.setContentsMargins(0, 0, 0, 0)
        self.setStyleSheet("background: transparent;")
    
    def set_thickness(self, thickness):
        """设置线条粗细"""
        self.thickness = thickness
        self.setFixedHeight(thickness)
        self.update()  # 刷新重绘
    
    def set_color(self, color):
        """设置线条颜色"""
        self.color = color
        self.update()  # 刷新重绘
    
    def paintEvent(self, event):
        """绘制分隔线"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # 设置画笔颜色和宽度
        painter.setBrush(QBrush(self.color))
        painter.setPen(Qt.NoPen)
        
        # 绘制矩形作为分隔线
        painter.drawRect(0, 0, self.width(), self.thickness)


class ContentLabel(QLabel):
    def __init__(self, text="", parent=None):
        super().__init__(text, parent)
        self.setWordWrap(True)  # 启用自动换行
        self.setAlignment(Qt.AlignTop | Qt.AlignLeft)  # 顶部左对齐
        self.setStyleSheet("""
            QLabel {
                padding: 0;
                border: none;
                color: rgba(255, 255, 255, 200);
            }
        """)


class ContentBlock(QWidget):     
    def __init__(self, original_text, translated_text, parent=None):         
        super().__init__(parent)       

        self.setObjectName("ContentBlock")  
        
        layout = QVBoxLayout(self)
        
        # 创建标签并设置自动换行和对齐方式
        original_label = ContentLabel(original_text, self)
        
        translated_label = ContentLabel(translated_text, self)
        
        layout.addWidget(original_label)         
        layout.addWidget(SplitLine(thickness=1, color=QColor(255, 255, 255, 100)))         
        layout.addWidget(translated_label)          
        
        # 设置布局边距和间距
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(5)
        
        self.setLayout(layout)          
        
        # 设置尺寸策略，让组件能够扩展
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        
        self.setStyleSheet("""      
            QLabel {
                padding: 0;
                border: none;
                color: rgba(255, 255, 255, 200);
            }
        """)
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.fillRect(self.rect(), QColor(200, 255, 200, 0))
        super().paintEvent(event)



class BlurWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setAttribute(Qt.WA_TranslucentBackground)  # 透明背景
        self.setWindowFlag(Qt.FramelessWindowHint)      # 去掉窗口边框

        # 样式参数
        self.style_args = {
            "background-color": QColor(60, 40, 40, 230),
            "font-size": "16px",
            "padding": "10px",
            "border-radius": 10
        }

        # ========== ScrollArea ==========
        scroll_area = QScrollArea(self)
        scroll_area.setWidgetResizable(True)  # 随内容调整大小
        scroll_area.setFrameShape(QScrollArea.NoFrame)  # 去掉边框
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)  # 只要垂直滚动条
        
        # 关键修改：设置 QScrollArea 背景透明
        scroll_area.setStyleSheet("QScrollArea { background: transparent; }")

        # 内容容器
        content_widget = QWidget()
        content_widget.setAutoFillBackground(False)
        # 关键修改：设置内容容器背景透明
        content_widget.setStyleSheet("QWidget { background: transparent; }")
        
        content_layout = QVBoxLayout(content_widget)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(0)

        # 加入一些测试控件和分隔线
        for i in range(15):
            block = ContentBlock(sample_original_text, sample_translated_text)

            content_layout.addWidget(block)
            
            content_layout.addWidget(SplitLine())

        scroll_area.setWidget(content_widget)

        # ========== 主布局 ==========
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 10, 0, 10)  # 让scroll_area填充整个窗口
        layout.addWidget(scroll_area)
        self.setLayout(layout)

    def paintEvent(self, event):
        """绘制模糊窗口背景"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        brush = QBrush(self.style_args["background-color"])
        painter.setBrush(brush)
        painter.setPen(Qt.NoPen)
        painter.drawRoundedRect(self.rect(), self.style_args["border-radius"], self.style_args["border-radius"])


if __name__ == "__main__":
    app = QApplication(sys.argv)
    w = BlurWindow()
    w.resize(400, 700)
    w.show()
    sys.exit(app.exec())