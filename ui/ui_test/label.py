import sys
from PySide6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QLabel, QScrollArea, QSizePolicy
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QPainter, QColor, QBrush

from PySide6.QtWidgets import QWidget
from PySide6.QtCore import Qt
from PySide6.QtGui import QPainter, QColor, QBrush
from PySide6.QtWidgets import QApplication, QWidget, QVBoxLayout, QLabel, QGraphicsBlurEffect, QPushButton, QMainWindow, QTextEdit
from PySide6.QtCore import Qt, QRect, QPropertyAnimation, QEasingCurve, QTimer, Signal, Property, QPoint
from PySide6.QtGui import QPainter, QTextCursor, QTextDocument, QFont, QColor, QPen, QTextCharFormat, QPalette, QBrush

import re
import sys
import time
import jieba
import spacy

sample_original_text = """
1.	Can Peanut Allergies Be Cured?
d. A visit to an allergist confirmed that Anabelle was severely allergic to the peanut butter in the dessert, as well as to most other nuts. It began a life upheaval familiar to families of kids with allergies: learning to decode labels, to carry an EpiPen, and to interrogate friends and their parents about the ingredients in a birthday cake.
"""
sample_translated_text = "令人瞩目的新疗法可以使数百万儿童和成人摆脱花生过敏的致命威胁，解决我们增长最快的医疗问题之一"


class ContentLabel(QTextEdit):
    wordHovered = Signal(str, QRect)  # 悬浮单词信号，包含单词和位置
    textSelected = Signal(str)  # 选中文本信号，包含选中的文本
    textRemoved = Signal(str)  # 删除文本信号，包含删除的文本

    
    def __init__(self, text="", parent=None):
        super().__init__(text, parent)
        
        # 设置为只读模式
        self.setReadOnly(True)
        
        # 设置透明背景样式
        self.setup_transparent_style()

        # 禁用滚动条，自适应高度
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)


        # 当前悬浮的单词信息
        self.hovered_word = ""
        self.hovered_word_rect = QRect()
        self.nlp = spacy.load("en_core_web_sm")

        self.skip_words = set([" ", "\n", "\t", "", ".", ",", "!", "?", "，", "。", "！", "？", ";", "；", ":", "：", "\"", "'", "“", "”", "‘", "’", "（", "）", "(", ")", "[", "]", "{", "}", "<", ">", "-", "_", "+", "=", "*", "&", "^", "%", "$", "#", "@", "~", "`"])
        self.last_checked_word_timestamp = 0
        self.selected_words = []
        self.selected_custom_words = []


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
    
    # 2. 添加自动调整高度的方法
    def adjust_height_to_content(self):
        """根据文本内容自动调整高度"""
        doc = self.document()
        doc_height = doc.size().height()
        margins = self.contentsMargins()
        total_height = int(doc_height + margins.top() + margins.bottom() + 20)  # 添加一些边距
        self.setFixedHeight(total_height)

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

        # 设置鼠标样式为箭头，避免变成文本编辑光标
        self.setCursor(Qt.CursorShape.ArrowCursor)
        self.viewport().setCursor(Qt.CursorShape.ArrowCursor)
        
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
                return text[start:end], word_rects
        return "", []

    def set_selected_words(self, words):
        self.selected_words = []
        for word in words:
            self.add_selected_word(word)

    def add_selected_word(self, word):
        is_custom = True
        original_word = word
        lemma_word = self.text_to_lemma(word)

        if lemma_word in [w[0] for w in self.text_split_result]:
            is_custom = False
        
        if is_custom:
            pattern = rf"\b{re.escape(original_word)}\b"
            matches = [(m.start(), m.end()) for m in re.finditer(pattern, self.toPlainText())]
            if matches != []:
                self.selected_custom_words.append((original_word, matches))
                self.viewport().update()
            
            return
        if original_word and original_word not in self.selected_words:
            # 查找所有匹配word的位置
            poses = []
            for (w, s, e) in self.text_split_result:
                if w == lemma_word:
                    poses.append((s, e))
            if poses != []:
                self.selected_words.append((original_word, poses))
                self.viewport().update()

    def remove_selected_word(self, word):
        self.selected_words = [item for item in self.selected_words if item[0] != word]
        self.viewport().update()

    # 文本处理
    def text_to_lemma(self, text):
        doc = self.nlp(text)
        return " ".join([token.lemma_ for token in doc])

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
                highlight_color = QColor(255, 150, 0, int(45))
                pen_color = QColor(255, 150, 0, int(150))
                painter.setPen(QPen(pen_color, 1))

                for pos in poses:
                    for rect in self.get_word_rects(pos[0], pos[1]):
                        painter.fillRect(rect, highlight_color)
                        painter.drawLine(rect.left(), rect.bottom(), rect.right(), rect.bottom())
                painter.end()
        for (word, poses) in self.selected_custom_words:
            if poses:
                painter = QPainter(self.viewport())
                painter.setRenderHint(QPainter.RenderHint.Antialiasing)
                pen_color = QColor(150, 255, 100, int(150))
                painter.setPen(QPen(pen_color, 1))

                for pos in poses:
                    for rect in self.get_word_rects(pos[0], pos[1]):
                        painter.drawLine(rect.left(), rect.bottom()+2, rect.right(), rect.bottom()+2)
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
                self.setFocus()
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

        self.text_split_result = list((self.text_to_lemma(w), s, e) for (w, s, e) in jieba.tokenize(text))
        self.hovered_word = ""
        self.hovered_word_rect = QRect()
        self._highlight_opacity = 0
            
        # 自动调整高度
        QTimer.singleShot(0, self.adjust_height_to_content)  # 使用定时器确保文档已更新

    
    def keyPressEvent(self, event):
        """禁用键盘输入（只读模式）"""
        # 设置回车触发事件
        if event.key() == Qt.Key.Key_Escape:
            super().keyPressEvent(event)
            return

        if event.key() in (Qt.Key.Key_Delete, Qt.Key.Key_Backspace):
            super().keyPressEvent(event)
            return

        if event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
            event.ignore()  # 忽略回车事件，防止插入新行
            
            # 检查是否有选中的文字
            cursor = self.textCursor()
            if cursor.hasSelection():
                selected_text = cursor.selectedText()
                start_pos = cursor.selectionStart()
                end_pos = cursor.selectionEnd()
                print(f"选中文字: '{selected_text}', 起始位置: {start_pos}, 结束位置: {end_pos}")
                if selected_text in [w[0] for w in self.selected_words]:
                    self.remove_selected_word(selected_text)
                    self.textRemoved.emit(selected_text)
                    print(f"删除单词: {selected_text}")
                    return
                elif selected_text in [w[0] for w in self.selected_custom_words]:
                    self.selected_custom_words = [item for item in self.selected_custom_words if item[0] != selected_text]
                    self.textRemoved.emit(selected_text)
                    self.viewport().update()
                    print(f"删除单词: {selected_text}")
                    return
                else:
                    # 发射信号，传递选中的文字
                    self.textSelected.emit(selected_text)
                    self.add_selected_word(selected_text)
                
            elif self.hovered_word:
                # 处理悬浮单词的选择/删除逻辑
                if self.hovered_word in [w[0] for w in self.selected_words]:
                    self.remove_selected_word(self.hovered_word)
                    self.textRemoved.emit(self.hovered_word)
                    print(f"删除单词: {self.hovered_word}")
                else:
                    self.textSelected.emit(self.hovered_word)
                    self.add_selected_word(self.hovered_word)
                    print(f"选中单词: {self.hovered_word}")

            return


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
        layout.setSpacing(0)
        
        self.setLayout(layout)          
        
        # 设置尺寸策略，让组件能够扩展
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        
        # 删除动画相关属性
        self._background_color = QColor(200, 255, 200, 0)  # 初始背景颜色
        self._delete_animation_running = False  # 动画运行状态
        
        # 创建颜色动画
        self.color_animation = QPropertyAnimation(self, b"background_color")
        self.color_animation.setDuration(500)  # 0.5秒
        self.color_animation.setEasingCurve(QEasingCurve.Type.OutCubic)
        self.color_animation.finished.connect(self._on_animation_finished)

        # 创建高度收缩动画
        self.height_animation = QPropertyAnimation(self, b"maximumHeight")
        self.height_animation.setDuration(300)  # 0.3秒
        self.height_animation.setEasingCurve(QEasingCurve.Type.InOutQuart)
        self.height_animation.finished.connect(self._on_height_animation_finished)
        
        self.setStyleSheet("""      
            QLabel {
                padding: 0;
                border: none;
                color: rgba(255, 255, 255, 200);
            }
        """)
    
    def get_background_color(self):
        return self._background_color
    
    def set_background_color(self, color):
        self._background_color = color
        self.update()  # 触发重绘
    
    # 定义属性，用于动画
    background_color = Property(QColor, get_background_color, set_background_color)
    
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.fillRect(self.rect(), self._background_color)
        super().paintEvent(event)
    
    def _on_animation_finished(self):
        """动画完成回调"""
        self._delete_animation_running = False
        # 将背景色设置为透明深蓝色
        self._background_color = QColor(255, 100, 100, 0)  # 透明深蓝色
        self.update()
    
    def _on_height_animation_finished(self):
        """高度动画完成后真正关闭组件"""
        self.close()
        
    def _start_close_animation(self):
        """开始关闭动画"""
        # 保存当前高度
        self._original_height = self.height()
        
        # 设置高度动画
        self.height_animation.setStartValue(self._original_height)
        self.height_animation.setEndValue(0)
        
        # 设置固定高度约束，防止内容撑开
        self.setMaximumHeight(self._original_height)
        
        # 开始高度收缩动画
        self.height_animation.start()
    
    def _start_delete_animation(self):
        """开始删除动画"""
        if self._delete_animation_running:
            # 如果动画正在运行，开始关闭动画
            self._start_close_animation()
            return
        
        # 标记动画开始
        self._delete_animation_running = True
        
        # 设置动画起始和结束颜色
        start_color = QColor(255, 100, 100, 200)  # 较高不透明度的红色
        end_color = QColor(255, 100, 100, 0)       # 透明深蓝色
        
        self.color_animation.setStartValue(start_color)
        self.color_animation.setEndValue(end_color)
        
        # 立即设置起始颜色并开始动画
        self._background_color = start_color
        self.update()
        self.color_animation.start()
    
    def keyPressEvent(self, event):
        """禁用键盘输入（只读模式）"""
        # 设置回车触发事件
        if event.key() == Qt.Key.Key_Escape:
            super().keyPressEvent(event)
            return

        if event.key() in (Qt.Key.Key_Delete, Qt.Key.Key_Backspace):
            self._start_delete_animation()
            return


class BlurWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setAttribute(Qt.WA_TranslucentBackground)  # 透明背景
        self.setWindowFlag(Qt.FramelessWindowHint)      # 去掉窗口边框

        # 样式参数
        self.style_args = {
            "background-color": QColor(40, 40, 40, 230),
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
        for i in range(10):
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

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Escape:
            self.close()
        super().keyPressEvent(event)  # 不要吃掉事件



if __name__ == "__main__":
    app = QApplication(sys.argv)
    w = BlurWindow()
    w.resize(400, 700)
    w.show()
    sys.exit(app.exec())