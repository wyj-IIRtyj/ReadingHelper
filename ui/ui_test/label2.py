import sys
from PySide6.QtWidgets import QApplication, QWidget, QVBoxLayout, QMainWindow, QLabel, QTextEdit
from PySide6.QtCore import Qt, QRect, QPropertyAnimation, QEasingCurve, QTimer, Signal, Property, QPoint
from PySide6.QtGui import QKeyEvent, QPainter, QTextCursor, QTextDocument, QFont, QColor, QPen, QTextCharFormat, QPalette
import re
import time
import jieba


sample_original_text = "Remarkable new treatments can free millions of kids and adults from the deadly threat of peanut allergy, tackling one of our fastest-growing medical problems"
sample_translated_text = "令人瞩目的新疗法可以使数百万儿童和成人摆脱花生过敏的致命威胁，解决我们增长最快的医疗问题之一"

class ContentTextEdit(QTextEdit):
    wordHovered = Signal(str, QRect)  # 悬浮单词信号，包含单词和位置
    textSelected = Signal(str)  # 选中文本信号，包含选中的文本
    textRemoved = Signal(str)  # 删除文本信号，包含删除的文本
    
    def __init__(self, text="", parent=None):
        super().__init__(text, parent)
        
        # 设置为只读模式
        self.setReadOnly(True)
        
        # 设置透明背景样式
        self.setup_transparent_style()
        
        # 当前悬浮的单词信息
        self.hovered_word = ""
        self.hovered_word_rect = QRect()

        self.skip_words = set([" ", "\n", "\t", "", ".", ",", "!", "?", "，", "。", "！", "？", ";", "；", ":", "：", "\"", "'", "“", "”", "‘", "’", "（", "）", "(", ")", "[", "]", "{", "}", "<", ">", "-", "_", "+", "=", "*", "&", "^", "%", "$", "#", "@", "~", "`"])
        self.last_checked_word_timestamp = 0
        self.selected_words = []


        # 动画高亮滑块属性
        self._highlight_x = 0
        self._highlight_y = 0 
        self._highlight_width = 0
        self._highlight_height = 0
        self._highlight_opacity = 0
        
        # 动画对象
        self.highlight_animation = QPropertyAnimation(self, b"highlight_opacity")
        self.highlight_animation.setDuration(200)
        self.highlight_animation.setEasingCurve(QEasingCurve.Type.OutCubic)
        
        self.move_animation = QPropertyAnimation(self, b"highlight_rect")
        self.move_animation.setDuration(300)
        self.move_animation.setEasingCurve(QEasingCurve.Type.OutCubic)
        
        # 隐藏定时器
        self.hide_timer = QTimer()
        self.hide_timer.setSingleShot(True)
        self.hide_timer.timeout.connect(self.hide_highlight)
        
        # 设置鼠标跟踪
        self.setMouseTracking(True)
        self.viewport().setMouseTracking(True)
        
        # 设置文本内容
        if text:
            self.setPlainText(text)
    
    def setup_transparent_style(self):
        """设置透明背景样式"""
        self.setStyleSheet("""
            QTextEdit {
                background: transparent;
                border: none;
                color: rgba(255, 255, 255, 200);
                selection-background-color: rgba(0, 150, 255, 100);
                padding: 10px;
            }
            QTextEdit:focus {
                outline: none;
            }
        """)
        
        # 设置文档边距
        doc = self.document()
        doc.setDocumentMargin(10)
        
        # 设置调色板确保透明背景
        palette = self.palette()
        palette.setColor(QPalette.ColorRole.Base, QColor(0, 0, 0, 0))
        palette.setColor(QPalette.ColorRole.Window, QColor(0, 0, 0, 0))
        self.setPalette(palette)
        
        # 设置视口背景透明
        self.viewport().setAutoFillBackground(False)

    def get_word_at_position(self, pos):
        cursor_at_pos = self.cursorForPosition(pos)
        if cursor_at_pos.isNull():
            return "", []
        
        cursor_pos = cursor_at_pos.position()
        text = self.toPlainText()
        if cursor_pos >= len(text):
            return "", []
        
        for (word, start, end) in self.text_split_result:
            if start <= cursor_pos <= end:
                if not word or word in self.skip_words:
                    return "", []
                word_rects = self.get_word_rects(start, end)
                return word, word_rects
        return "", []

    def set_selected_words(self, words):
        self.selected_words = []
        for word in words:
            self.add_selected_word(word)

    def add_selected_word(self, word):
        if word and word not in self.selected_words:
            # 查找所有匹配word的位置
            poses = []
            for (w, s, e) in self.text_split_result:
                if w == word:
                    poses.append((s, e))
            if poses != []:
                self.selected_words.append((word, poses))
                self.viewport().update()

    def remove_selected_word(self, word):
        self.selected_words = [item for item in self.selected_words if item[0] != word]
        self.viewport().update()

    def get_word_rects(self, start_pos, end_pos):
        """获取单词在视口中的矩形位置（可能跨行，返回多个QRect）"""
        rects = []
        cursor = self.textCursor()
        cursor.setPosition(start_pos)
        
        while cursor.position() < end_pos:
            # 当前行起点
            start_cursor = QTextCursor(cursor)
            start_rect = self.cursorRect(start_cursor)

            start_top_pos = start_rect.top()
            while cursor.position() < end_pos and self.cursorRect(cursor).top() == start_top_pos:
                cursor.setPosition(cursor.position()+1)

            end_cursor = QTextCursor(cursor)
            end_rect = self.cursorRect(end_cursor)
            
            word_text = self.toPlainText()[start_cursor.position():end_cursor.position()]
            text_width = self.fontMetrics().horizontalAdvance(word_text)
            rect = QRect(start_rect.left(), start_rect.top(), text_width, start_rect.height())
            rects.append(rect)

            if self.cursorRect(cursor).top() != start_top_pos:
                cursor.setPosition(cursor.position()-1)
            
            # 移动到下一个位置
            cursor.setPosition(cursor.position()+1)
        return rects

    def paintEvent(self, event):
        super().paintEvent(event)
        if self._highlight_opacity > 0 and hasattr(self, "_highlight_rects"):
            painter = QPainter(self.viewport())
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)
            
            highlight_color = QColor(72, 120, 151, int(120 * self._highlight_opacity))
            pen_color = QColor(0, 200, 255, int(180 * self._highlight_opacity))
            painter.setPen(QPen(pen_color, 2))
            
            for rect in self._highlight_rects:
                painter.fillRect(rect, highlight_color)
                # painter.drawLine(rect.left(), rect.bottom() + 2, rect.right(), rect.bottom() + 2)
            
            painter.end()
        for (word, poses) in self.selected_words:
            if poses:
                painter = QPainter(self.viewport())
                painter.setRenderHint(QPainter.RenderHint.Antialiasing)
                pen_color = QColor(255, 150, 0, int(150))
                painter.setPen(QPen(pen_color, 1))

                for pos in poses:
                    for rect in self.get_word_rects(pos[0], pos[1]):
                        painter.drawLine(rect.left(), rect.bottom(), rect.right(), rect.bottom())
                painter.end()

    def mouseMoveEvent(self, event):
        """鼠标移动事件"""
        # 获取鼠标位置的单词
        if time.time() - self.last_checked_word_timestamp < 0.05:
            super().mouseMoveEvent(event)
            return
        word, word_rects = self.get_word_at_position(event.position().toPoint()) 
        self.last_checked_word_timestamp = time.time()
        if word != self.hovered_word:
            self.hovered_word = word
            if word and word_rects:
                self.show_highlight(word_rects)
                self.wordHovered.emit(word, word_rects[0])  # 兼容旧信号
                self.hide_timer.stop()
            else:
                self.hide_timer.start(300)

        
        super().mouseMoveEvent(event)
    
    def leaveEvent(self, event):
        """鼠标离开事件"""
        self.hovered_word = ""
        self.hovered_word_rect = QRect()
        self.hide_timer.start(300)
        super().leaveEvent(event)
    
    def show_highlight(self, rects):
        self._highlight_rects = rects
        self.highlight_animation.stop()
        self.highlight_animation.setStartValue(0)
        self.highlight_animation.setEndValue(1)
        self.highlight_animation.start()
        
    
    def hide_highlight(self):
        """隐藏高亮"""
        if not self.hovered_word:
            self.highlight_animation.stop()
            self.highlight_animation.setStartValue(float(self._highlight_opacity))
            self.highlight_animation.setEndValue(0.0)
            self.highlight_animation.start()
    
    # 动画属性
    def get_highlight_opacity(self):
        return self._highlight_opacity
    
    def set_highlight_opacity(self, value):
        self._highlight_opacity = value
        self.viewport().update()
    
    def get_highlight_rect(self):
        return [self._highlight_x, self._highlight_y, self._highlight_width, self._highlight_height]
    
    def set_highlight_rect(self, value):
        if value == []:
            self.viewport().update()
            return
        self._highlight_x, self._highlight_y, self._highlight_width, self._highlight_height = value
    
    highlight_opacity = Property(float, get_highlight_opacity, set_highlight_opacity)
    highlight_rect = Property(list, get_highlight_rect, set_highlight_rect)
    
    def setPlainText(self, text):
        """重写设置文本方法"""
        super().setPlainText(text)
        # 重置高亮状态

        self.text_split_result = list(jieba.tokenize(text))
        self.hovered_word = ""
        self.hovered_word_rect = QRect()
        self._highlight_opacity = 0
    
    def keyPressEvent(self, event):
        """禁用键盘输入（只读模式）"""
        # 设置回车触发事件
        if event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
            event.ignore()  # 忽略回车事件，防止插入新行
            if self.hovered_word:
                if self.hovered_word in [w[0] for w in self.selected_words]:
                    self.remove_selected_word(self.hovered_word)
                    self.textRemoved.emit(self.hovered_word)
                else:
                    self.textSelected.emit(self.hovered_word)
                    self.add_selected_word(self.hovered_word)
            return


# 示例窗口
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("ContentTextEdit 示例 - 透明多行文本框")
        self.setGeometry(100, 100, 800, 600)
        
        # 设置深色背景
        self.setStyleSheet("""
            QMainWindow {
                background-color: #2b2b2b;
            }
        """)
        
        # 创建中央窗口
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        layout = QVBoxLayout(central_widget)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # 示例文本
        sample_text = sample_original_text

        # 创建ContentTextEdit
        self.content_edit = ContentTextEdit(sample_text)
        self.content_edit.wordHovered.connect(self.on_word_hovered)
        layout.addWidget(self.content_edit, 1)  # 给予更多空间
        
        # 状态标签
        self.status_label = QLabel("将鼠标悬浮在上方文本的单词上...")
        self.status_label.setStyleSheet("""
            QLabel {
                color: rgba(255, 255, 255, 150);
                padding: 15px;
                background: rgba(255, 255, 255, 10);
                border-radius: 8px;
                font-size: 12px;
            }
        """)
        self.status_label.setWordWrap(True)
        layout.addWidget(self.status_label)
        
        # 控制按钮区域
        controls_widget = QWidget()
        controls_layout = QVBoxLayout(controls_widget)
        
        # 添加一个按钮来测试setText功能
        from PySide6.QtWidgets import QPushButton
        test_button = QPushButton("更换示例文本")
        test_button.setStyleSheet("""
            QPushButton {
                background: rgba(0, 150, 255, 100);
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 5px;
                font-weight: bold;
            }
            QPushButton:hover {
                background: rgba(0, 150, 255, 150);
            }
            QPushButton:pressed {
                background: rgba(0, 120, 200, 200);
            }
        """)
        test_button.clicked.connect(self.change_text)
        controls_layout.addWidget(test_button)
        
        layout.addWidget(controls_widget)
    
    def on_word_hovered(self, word, rect):
        """处理单词悬浮事件"""
        self.status_label.setText(
            f"悬浮单词: '{word}'\n"
            f"位置: ({rect.x()}, {rect.y()})\n"
            f"尺寸: {rect.width()} × {rect.height()} 像素\n"
            f"使用QTextEdit内置API获取精确位置"
        )
    
    def change_text(self):
        """更换文本内容"""
        new_text = """这是新的文本内容！This is new text content!

QTextEdit提供了强大的文本处理能力：
✓ 精确的光标定位 (cursorForPosition)
✓ 文本块和字符格式支持
✓ 内置的文本度量和几何计算
✓ 自动换行和滚动支持

QTextEdit provides powerful text processing capabilities:
✓ Precise cursor positioning (cursorForPosition)  
✓ Text block and character format support
✓ Built-in text metrics and geometry calculation
✓ Automatic word wrap and scroll support

试试悬浮在这些新单词上！Try hovering over these new words!"""
        
        self.content_edit.setPlainText(new_text)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    window = MainWindow()
    window.show()
    
    sys.exit(app.exec())