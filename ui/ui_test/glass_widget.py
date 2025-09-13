from PySide6.QtWidgets import *
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QPalette

class ContentBlock(QWidget):     
    def __init__(self, original_text, translated_text, parent=None):         
        super().__init__(parent)       

        self.setObjectName("ContentBlock")   
        
        layout = QVBoxLayout(self)
        
        # 创建标签并设置自动换行和对齐方式
        original_label = QLabel(original_text, self)
        original_label.setObjectName("OriginalLabel")
        original_label.setWordWrap(True)
        original_label.setAlignment(Qt.AlignTop | Qt.AlignLeft)
        
        translated_label = QLabel(translated_text, self)
        translated_label.setObjectName("TranslatedLabel")
        translated_label.setWordWrap(True)
        translated_label.setAlignment(Qt.AlignTop | Qt.AlignLeft)
        
        layout.addWidget(original_label)         
        layout.addWidget(SplitLine(thickness=1, color=QColor(255, 255, 255, 100)))         
        layout.addWidget(translated_label)          
        
        # 设置布局边距和间距
        layout.setContentsMargins(30, 10, 30, 10)
        layout.setSpacing(5)
        
        self.setLayout(layout)          
        
        # 设置尺寸策略，让组件能够扩展
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        
        # 方案1: 使用更明确的样式表
        self.setStyleSheet("""             
            ContentBlock#ContentBlock {
                font-size: 18px;             
                background-color: rgba(200, 255, 200, 130);
                border: 1px solid rgba(150, 200, 150, 150);
                border-radius: 5px;
            }
            QLabel#OriginalLabel, QLabel#TranslatedLabel {
                padding: 0px;
                margin: 0px;
                border: none;
                color: rgba(255, 255, 255, 200);
                background-color: transparent;
            }
        """)

# 方案2: 重写 paintEvent 方法确保背景绘制
class ContentBlockV2(QWidget):     
    def __init__(self, original_text, translated_text, parent=None):         
        super().__init__(parent)       

        self.setObjectName("ContentBlock")   
        
        layout = QVBoxLayout(self)
        
        original_label = QLabel(original_text, self)
        original_label.setWordWrap(True)
        original_label.setAlignment(Qt.AlignTop | Qt.AlignLeft)
        
        translated_label = QLabel(translated_text, self)
        translated_label.setWordWrap(True)
        translated_label.setAlignment(Qt.AlignTop | Qt.AlignLeft)
        
        layout.addWidget(original_label)         
        layout.addWidget(SplitLine(thickness=1, color=QColor(255, 255, 255, 100)))         
        layout.addWidget(translated_label)          
        
        layout.setContentsMargins(30, 10, 30, 10)
        layout.setSpacing(5)
        
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        
        # 确保背景能够绘制
        self.setAutoFillBackground(True)
        
        self.setStyleSheet("""             
            ContentBlock {
                font-size: 18px;             
                background-color: rgba(200, 255, 200, 130);
                border: 1px solid rgba(150, 200, 150, 150);
                border-radius: 5px;
            }
            QLabel {
                padding: 0px;
                border: none;
                color: rgba(255, 255, 255, 200);
                background-color: transparent;
            }
        """)
    
    def paintEvent(self, event):
        # 确保样式表中的背景能够正确绘制
        from PyQt5.QtWidgets import QStyleOption, QStyle
        opt = QStyleOption()
        opt.initFrom(self)
        painter = QPainter(self)
        self.style().drawPrimitive(QStyle.PE_Widget, opt, painter, self)

# 方案3: 使用程序化设置背景色
class ContentBlockV3(QWidget):     
    def __init__(self, original_text, translated_text, parent=None):         
        super().__init__(parent)       
        
        layout = QVBoxLayout(self)
        
        original_label = QLabel(original_text, self)
        original_label.setWordWrap(True)
        original_label.setAlignment(Qt.AlignTop | Qt.AlignLeft)
        
        translated_label = QLabel(translated_text, self)
        translated_label.setWordWrap(True)
        translated_label.setAlignment(Qt.AlignTop | Qt.AlignLeft)
        
        layout.addWidget(original_label)         
        layout.addWidget(SplitLine(thickness=1, color=QColor(255, 255, 255, 100)))         
        layout.addWidget(translated_label)          
        
        layout.setContentsMargins(30, 10, 30, 10)
        layout.setSpacing(5)
        
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        
        # 程序化设置背景色
        self.setAutoFillBackground(True)
        palette = self.palette()
        palette.setColor(QPalette.Window, QColor(200, 255, 200, 130))
        self.setPalette(palette)
        
        # 只设置字体和标签样式
        self.setStyleSheet("""             
            ContentBlockV3 {
                font-size: 18px;
                border: 1px solid rgba(150, 200, 150, 150);
                border-radius: 5px;
            }
            QLabel {
                padding: 0px;
                border: none;
                color: rgba(255, 255, 255, 200);
            }
        """)

# 测试用的主窗口
class TestWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        layout = QVBoxLayout(central_widget)
        
        # 测试不同方案
        block1 = ContentBlock("原文测试1", "Translation test 1")
        block2 = ContentBlockV2("原文测试2", "Translation test 2") 
        block3 = ContentBlockV3("原文测试3", "Translation test 3")
        
        layout.addWidget(QLabel("方案1 - 明确的选择器:"))
        layout.addWidget(block1)
        layout.addWidget(QLabel("方案2 - 重写paintEvent:"))
        layout.addWidget(block2)
        layout.addWidget(QLabel("方案3 - 程序化设置:"))
        layout.addWidget(block3)
        
        # 设置窗口背景色以便看到效果
        self.setStyleSheet("QMainWindow { background-color: #2b2b2b; }")

# 可能需要导入的 SplitLine 类
class SplitLine(QWidget):
    def __init__(self, thickness=1, color=QColor(128, 128, 128), parent=None):
        super().__init__(parent)
        self.thickness = thickness
        self.color = color
        self.setFixedHeight(thickness)
        
    def paintEvent(self, event):
        from PyQt5.QtGui import QPainter
        painter = QPainter(self)
        painter.setPen(self.color)
        painter.drawLine(0, 0, self.width(), 0)