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

sample_original_text = """1.Can Peanut Allergies Be Cured?\nA visit to an allergist confirmed that Anabelle was severely allergic to the peanut butter in the dessert, as well as to most other nuts. It began a life upheaval familiar to families of kids with allergies: learning to decode labels, to carry an EpiPen, and to interrogate friends and their parents about the ingredients in a birthday cake."""
sample_translated_text = "令人瞩目的新疗法可以使数百万儿童和成人摆脱花生过敏的致命威胁，解决我们增长最快的医疗问题之一"


class ContentLabel(QTextEdit):
    wordHovered = Signal(str, QRect)  # 悬浮单词信号，包含单词和位置
    textSelected = Signal(str)  # 选中文本信号，包含选中的文本
    textRemoved = Signal(str)  # 删除文本信号，包含删除的文本

    dataInitialized = Signal()
    
    def __init__(self, text="", parent=None, style_type=1):
        super().__init__(text, parent)
        
        # 设置为只读模式
        self.setReadOnly(True)
        
        # 设置透明背景样式
        self.style_type = style_type
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

        self._background_animation_opacity = 0.0
        self.flash_color_selections = {
            "green": (150, 220, 160, 100), 
            "red": (220, 150, 160, 100)
        }
        self.flash_color_select = "green"
        self.background_animation = QPropertyAnimation(self, b"background_animation_opacity")
        self.background_animation.setDuration(500)  # 1秒
        self.background_animation.setEasingCurve(QEasingCurve.Type.InOutCubic)
        

        self.move_animation = QPropertyAnimation(self, b"highlight_rect")
        self.move_animation.setDuration(300)
        self.move_animation.setEasingCurve(QEasingCurve.Type.OutCubic)
        
        self.dataInitialized.connect(self.start_data_initialized_animation)

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
        total_height = int(doc_height + margins.top() + margins.bottom())  # 添加一些边距
        self.setFixedHeight(total_height)

    def setup_transparent_style(self):
        """设置透明背景样式"""
        if self.style_type == 1:
            self.setStyleSheet("""
                QTextEdit {
                    background: rgba(200, 200, 200, 50);
                    border: none;
                    border-top-left-radius: 10px;
                    border-top-right-radius: 10px;
                    color: rgba(255, 255, 255, 200);
                    selection-background-color: rgba(0, 150, 255, 100);
                    padding: 10px;
                }
                QTextEdit:focus {
                    outline: none;}
            """)
        elif self.style_type == 2:
            self.setStyleSheet("""
                QTextEdit {
                    background: rgba(200, 200, 200, 50);
                    border: none;
                    border-bottom-left-radius: 10px;
                    border-bottom-right-radius: 10px;
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
        doc.setDocumentMargin(0)
        
        # 设置调色板确保透明背景
        palette = self.palette()
        palette.setColor(QPalette.ColorRole.Base, QColor(0, 0, 0, 0))
        palette.setColor(QPalette.ColorRole.Window, QColor(0, 0, 0, 0))
        self.setPalette(palette)

        self._background_color = self.palette().color(self.backgroundRole())

        # 设置视口背景透明
        self.viewport().setAutoFillBackground(False)

    def get_word_at_position(self, pos):
        if not self.data_is_initialized: 
            return 
        
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
        if not self.data_is_initialized:
            return
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
        
        if self._background_animation_opacity > 0:
            painter = QPainter(self.viewport())
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)
            
            # 动画背景色
            anim_color = QColor(self.flash_color_selections[self.flash_color_select][0],
                                self.flash_color_selections[self.flash_color_select][1],
                                self.flash_color_selections[self.flash_color_select][2],
                                int(self.flash_color_selections[self.flash_color_select][3] * self._background_animation_opacity))
            painter.fillRect(self.viewport().rect(), anim_color)
            painter.end()
        
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

    def resizeEvent(self, event):
        super().resizeEvent(event)   # 保持默认行为
        self.adjust_height_to_content()

    def mouseMoveEvent(self, event):
        """鼠标移动事件"""
        # 获取鼠标位置的单词
        if time.time() - self.last_checked_word_timestamp < 0.05:
            return super().mouseMoveEvent(event)
        if not self.data_is_initialized:
            return super().mouseMoveEvent(event)
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
        return super().mouseMoveEvent(event)

        
    
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

    def get_background_animation_opacity(self):
            return self._background_animation_opacity

    def set_background_animation_opacity(self, value):
        self._background_animation_opacity = value
        self.update()  # 触发重绘

    highlight_opacity = Property(float, get_highlight_opacity, set_highlight_opacity)
    highlight_rect = Property(list, get_highlight_rect, set_highlight_rect)
    background_animation_opacity = Property(float, get_background_animation_opacity, set_background_animation_opacity)


    def start_data_initialized_animation_fadeout(self):
        """执行淡出"""
        self.background_animation.setStartValue(1.0)
        self.background_animation.setEndValue(0.0)
        self.background_animation.start()
        
        # 断开之前的连接，连接新的
        try:
            self.background_animation.finished.disconnect(self.start_data_initialized_animation_fadeout)
        except:
            pass

    def start_data_initialized_animation(self):
        print(111)
        self.flash_color_select = "green"
        self.background_animation.setStartValue(0.0)
        self.background_animation.setEndValue(1.0)
        self.background_animation.start()    

        self.background_animation.finished.connect(self.start_data_initialized_animation_fadeout)
    
    def start_data_not_initialized_animation(self):
        self.flash_color_select = "red"
        self.background_animation.setStartValue(0.0)
        self.background_animation.setEndValue(1.0)
        self.background_animation.start()    


    def data_initialization(self, text, selected_words):
        self.text_split_result = list((self.text_to_lemma(w), s, e) for (w, s, e) in jieba.tokenize(text))
        self.data_is_initialized = True
        for w in selected_words: 
            self.add_selected_word(w)
        self.dataInitialized.emit()
        

    def setPlainText(self, text, selected_words=[]):
        """重写设置文本方法"""
        super().setPlainText(text)
        # 重置高亮状态
        self.data_is_initialized = False
        self.start_data_not_initialized_animation()

        threading.Thread(target=self.data_initialization, args=(text, selected_words,)).start()

        self.hovered_word = ""
        self.hovered_word_rect = QRect()
        self._highlight_opacity = 0
            
        # 自动调整高度
        self.adjust_height_to_content()

    
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

        super().keyPressEvent(event)

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
    def __init__(self, original_text, translated_text, parent=None, block_id=1):          
        super().__init__(parent)       

        self.setObjectName("ContentBlock")  
        self.setMouseTracking(True)
        self.split_line = None
        
        layout = QVBoxLayout(self)
        
        # 创建标签并设置自动换行和对齐方式
        original_label = ContentLabel(original_text, self, style_type=1)
        
        translated_label = ContentLabel(translated_text, self, style_type=2)
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

    def set_split_line(self, line):
        """设置分隔线控件"""
        self.split_line = line

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
        if self.split_line: 
            self.split_line.close()
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
        super().keyPressEvent(event)

    def mouseMoveEvent(self, event: QMouseEvent) -> None:
        return super().mouseMoveEvent(event)
        


class NormalButton(QPushButton):
    def __init__(self, text, parent=None, state=1, text_color="white"):
        super().__init__(text, parent)

        self.setStyleSheet(f"""
            QPushButton {{
                background-color: rgba(70, 70, 70, 200);
                color: {text_color};
                border: none;
                padding: 6px 14px;
                border-radius: 6px;
            }}
            QPushButton:hover {{
                background-color: rgba(100, 100, 100, 170);
            }}
        """)
        self.state = state

        # 添加透明度效果
        self.opacity_effect = QGraphicsOpacityEffect(self)
        self.setGraphicsEffect(self.opacity_effect)
        self.opacity_effect.setOpacity(1.0)

        # 修复1: 使用 maximumWidth 和 minimumWidth 同时控制宽度动画
        self.width_animation = QPropertyAnimation(self, b"maximumWidth")
        self.width_animation.setEasingCurve(QEasingCurve.Type.OutCubic)
        self.width_animation.setDuration(300)

        # 保存初始宽度
        self.initial_width = self.sizeHint().width()
        
        # 修复2: 添加动画完成后的布局更新信号
        self.width_animation.finished.connect(self._on_animation_finished)

    def _on_animation_finished(self):
        """动画完成后更新父布局"""
        if self.parent():
            parent_layout = self.parent().layout()
            if parent_layout:
                parent_layout.update()
                parent_layout.activate()

    def start_show_animation(self, if_change_state=1):
        self.state = 1
        self.show()  # 确保按钮可见
        
        # 重置尺寸约束
        self.setMaximumWidth(16777215)  # Qt的默认最大宽度
        self.setMinimumWidth(0)

        # 宽度恢复动画
        self.width_animation.stop()
        # 从当前实际宽度开始
        current_width = self.width()
        self.width_animation.setStartValue(current_width)
        self.width_animation.setEndValue(self.initial_width)
        
        # 修复：同时设置最小和最大宽度
        self.width_animation.valueChanged.connect(self._update_width_constraints)
        self.width_animation.start()

    def start_hide_animation(self, if_change_state=1):
        self.state = 0
        # 宽度缩小到0
        self.width_animation.stop()
        current_width = self.width()
        self.width_animation.setStartValue(current_width)
        self.width_animation.setEndValue(0)
        
        # 修复：同时设置最小和最大宽度
        self.width_animation.valueChanged.connect(self._update_width_constraints)
        self.width_animation.start()

    def _update_width_constraints(self, width):
        """更新宽度约束，确保动画正确显示"""
        self.setMaximumWidth(int(width))
        self.setMinimumWidth(int(width))


class BottomBar(QWidget):
    def __init__(self):
        super().__init__()
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setWindowFlag(Qt.FramelessWindowHint)
        self.setMouseTracking(True)

        self.style_args = {
            "background-color": QColor(20, 20, 20, 200),
            "font-size": "16px",
            "padding": "10px",
            "border-radius": 10
        }
        self.state = 1
        self.animation_running = False

        # 创建按钮
        self.read_all_button = NormalButton("Read All", self)
        self.read_all_button.setFixedHeight(30)
        self.stop_button = NormalButton("Stop", self)
        self.stop_button.setFixedHeight(30)
        self.continue_button = NormalButton("Continue", self)
        self.continue_button.setFixedHeight(30)
        self.cancel_button = NormalButton("Cancel", self)
        self.cancel_button.setFixedHeight(30)
        self.clear_button = NormalButton("Clear", self, text_color="red")
        self.clear_button.setFixedHeight(30)

        self.stop_button.start_hide_animation()
        self.continue_button.start_hide_animation()
        self.cancel_button.start_hide_animation()

        # 创建更灵活的布局
        content_layout = QHBoxLayout(self)
        content_layout.setContentsMargins(20, 0, 20, 0)
        content_layout.setSpacing(10)
        
        # 左侧按钮组
        left_group = QHBoxLayout()
        left_group.setSpacing(10)
        left_group.addWidget(self.read_all_button)
        left_group.addWidget(self.stop_button)
        left_group.addWidget(self.continue_button)
        left_group.addWidget(self.cancel_button)
        left_group.addStretch(0)
        
        content_layout.addLayout(left_group)
        content_layout.addStretch(1)
        content_layout.addWidget(self.clear_button)

        # 设置按钮功能
        def start_read(): 
            self.read_all_button.start_hide_animation()
            QTimer.singleShot(50, lambda: self.stop_button.start_show_animation())
            QTimer.singleShot(50, lambda: self.cancel_button.start_show_animation())

        self.read_all_button.clicked.connect(start_read)

        def stop_read():
            self.stop_button.start_hide_animation()
            QTimer.singleShot(100, lambda: self.continue_button.start_show_animation())

        def cancel_read():
            self.stop_button.start_hide_animation()
            self.cancel_button.start_hide_animation()
            self.continue_button.start_hide_animation()
            QTimer.singleShot(350, lambda: self.read_all_button.start_show_animation())

        def continue_read():
            self.continue_button.start_hide_animation()
            QTimer.singleShot(50, lambda: self.stop_button.start_show_animation())

        self.stop_button.clicked.connect(stop_read)
        self.cancel_button.clicked.connect(cancel_read)
        self.continue_button.clicked.connect(continue_read)

        # =============== 修复自身动画配置 ===============


        # 几何形状动画 (位置和大小)
        self.geometry_animation = QPropertyAnimation(self, b"geometry")
        self.geometry_animation.setEasingCurve(QEasingCurve.Type.OutCubic)
        self.geometry_animation.setDuration(250)
        
        # 动画状态标志
        self.is_visible_state = True
        self.animation_running = False


    def start_show_animation(self):
        """显示 BottomBar 的动画"""
        if self.animation_running or self.is_visible_state:
            return
            
        self.animation_running = True
        self.is_visible_state = True
        
        
        # 获取起始和结束位置
        if self.parent():
            current_rect = self.geometry()
            end_geo = self.parent().get_bar_geo(state=1)    # 显示状态
            print(end_geo)
            
            # 设置几何动画
            self.geometry_animation.setStartValue(current_rect)
            self.geometry_animation.setEndValue(QRect(*end_geo))
        
            
            # 动画完成后的处理
            def on_show_finished():
                self.animation_running = False
                self.state = 1
            
            # 清除之前的连接
            try:
                self.geometry_animation.finished.disconnect()
            except:
                pass
                
            self.geometry_animation.finished.connect(on_show_finished)
            self.geometry_animation.start()

    def start_hide_animation(self):
        """隐藏 BottomBar 的动画"""
        if self.animation_running or not self.is_visible_state:
            return
            
        self.animation_running = True
        self.is_visible_state = False
        
        # 获取起始和结束位置
        if self.parent():
            current_rect = self.geometry()
            end_geo = self.parent().get_bar_geo(state=0)   # 隐藏状态
            
            # 设置几何动画
            self.geometry_animation.setStartValue(current_rect)
            self.geometry_animation.setEndValue(QRect(*end_geo))
            
            
            # 动画完成后隐藏 widget
            def on_hide_finished():
                self.animation_running = False
                self.state = 0
            
            # 清除之前的连接
            try:
                self.geometry_animation.finished.disconnect()
            except:
                pass
                
            self.geometry_animation.finished.connect(on_hide_finished)
            self.geometry_animation.start()

        
    def paintEvent(self, event):
        # 修复：添加安全检查，避免绘制冲突
        if not event or not self.isVisible():
            return
            
        painter = QPainter(self)
        
        # 修复：检查painter是否成功初始化
        if not painter.isActive():
            return
            
        try:
            painter.setRenderHint(QPainter.Antialiasing)
            brush = QBrush(self.style_args["background-color"])
            painter.setBrush(brush)
            painter.setPen(Qt.NoPen)
            painter.drawRoundedRect(self.rect(), self.style_args["border-radius"], self.style_args["border-radius"])
        except Exception as e:
            print(f"绘制错误: {e}")
        finally:
            # 修复：确保painter正确结束
            if painter.isActive():
                painter.end()

    def closeEvent(self, event):
        """修复：清理资源，防止内存泄漏"""
        # 停止所有动画
        if hasattr(self, 'show_animation_group'):
            self.show_animation_group.stop()
        if hasattr(self, 'hide_animation_group'):
            self.hide_animation_group.stop()
        super().closeEvent(event)

    def __del__(self):
        """修复：析构时清理动画资源"""
        try:
            if hasattr(self, 'show_animation_group'):
                self.show_animation_group.stop()
            if hasattr(self, 'hide_animation_group'):
                self.hide_animation_group.stop()
        except:
            pass

class BlurWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setAttribute(Qt.WA_TranslucentBackground)  # 透明背景
        self.setWindowFlag(Qt.FramelessWindowHint) 
        self.setMouseTracking(True)     # 去掉窗口边框

        # 样式参数
        self.style_args = {
            "background-color": QColor(40, 40, 40, 230),
            "font-size": "16px",
            "padding": "10px",
            "border-radius": 10
        }

        # ========== ScrollArea ==========
        scroll_area = QScrollArea(self)

        scroll_area.setMouseTracking(True)
        scroll_area.viewport().setMouseTracking(True)

        scroll_area.setWidgetResizable(True)  # 随内容调整大小
        scroll_area.setFrameShape(QScrollArea.NoFrame)  # 去掉边框
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)  # 只要垂直滚动条
        
        scroll_area.setStyleSheet("QScrollArea { background: transparent; }")
        content_widget = QWidget()
        content_widget.setMouseTracking(True)
        content_widget.setAutoFillBackground(False)
        content_widget.setStyleSheet("QWidget { background: transparent; }")
        
        content_layout = QVBoxLayout(content_widget)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(0)

        # 加入一些测试控件和分隔线
        for i in range(3):
            block = ContentBlock(sample_original_text, sample_translated_text)
            split_line = SplitLine()
            block.set_split_line(split_line)

            content_layout.addWidget(block)
            content_layout.addWidget(split_line)

        content_layout.addStretch(2)  # 底部弹性空间

        scroll_area.setWidget(content_widget)

        # ========== 创建BottomBar ==========
        self.bottom_bar = BottomBar()
        self.bottom_bar.setParent(self)
        self.bottom_bar.setFixedHeight(60)
        self.bar_height = 60

        # ========== 主布局 ==========
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 10, 0, 10)
        layout.addWidget(scroll_area)
        self.setLayout(layout)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        brush = QBrush(self.style_args["background-color"])
        painter.setBrush(brush)
        painter.setPen(Qt.NoPen)
        painter.drawRoundedRect(self.rect(), self.style_args["border-radius"], self.style_args["border-radius"])
    
    def get_bar_geo(self, state=1):
        print(state)
        if state:
            # 计算BottomBar的宽度和位置
            window_width = self.width()
            bar_width = int(window_width * 0.8)  # 横向占窗口宽度的70%
            bar_height = self.bar_height
            
            # 居中横向位置，底部对齐（留出一点边距）
            x = (window_width - bar_width) // 2
            y = self.height() - bar_height - 20  # 距离底部20px
            return (x, y, bar_width, bar_height)
        else: 
            # 计算BottomBar的宽度和位置
            window_width = self.width()
            bar_width = int(window_width) 
            x = (window_width - bar_width) // 2
            y = self.height() # 距离底部20px
            return (x, y, bar_width, 0)
            

    def resizeEvent(self, event):
        """窗口大小改变时调整BottomBar的位置和大小"""
        super().resizeEvent(event)
        
        self.bottom_bar.setGeometry(*self.get_bar_geo(self.bottom_bar.state))

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Escape:
            self.close()
        elif event.key() == Qt.Key.Key_0:
            self.bottom_bar.start_hide_animation()
        elif event.key() == Qt.Key.Key_1:
            self.bottom_bar.start_show_animation()
        super().keyPressEvent(event)

    def mouseMoveEvent(self, event: QMouseEvent):
        if event.position().y() > self.height() - 30 and self.bottom_bar.state == 0:
            self.bottom_bar.start_show_animation()
        elif event.position().y() < self.height() - 100 and self.bottom_bar.state == 1:
            self.bottom_bar.start_hide_animation()
        return super().mouseMoveEvent(event)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    w = BlurWindow()
    w.resize(400, 700)
    w.show()
    sys.exit(app.exec())