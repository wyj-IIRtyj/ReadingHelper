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


class ContentLabel(QTextEdit):
    wordHovered = Signal(str, QRect)  # 悬浮单词信号，包含单词和位置

    textSelected = Signal(str)  # 选中文本信号，包含选中的文本
    textRemoved = Signal(str)  # 删除文本信号，包含删除的文本

    dataInitialized = Signal()
    realTimeChangeTextSignal = Signal(str)
    
    def __init__(self, text="", parent=None, style_type=1, global_selected=[]):
        super().__init__("", parent)
        self.parent = parent
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
        self.lemma_index = []


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
        self.realTimeChangeTextSignal.connect(self.real_time_change_text)

        # 隐藏定时器
        self.hide_timer = QTimer()
        self.hide_timer.setSingleShot(True)
        self.hide_timer.timeout.connect(self.hide_highlight)
        
        # 设置鼠标跟踪
        self.setMouseTracking(True)
        self.viewport().setMouseTracking(True)
        
        # 设置文本内容
        if text:
            self.setPlainText(text, global_selected)
    
    # 2. 添加自动调整高度的方法
    def adjust_height_to_content(self):
        """根据文本内容自动调整高度"""
        doc = self.document()
        doc_height = doc.size().height()
        margins = self.contentsMargins()
        total_height = int(doc_height + margins.top() + margins.bottom())  # 添加一些边距
        self.setFixedHeight(total_height+1)

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

    def find_lemma_matches(self, lemma_phrase: str):
        """
        在 lemma 序列中查找目标 lemma_phrase（可能是词组），返回所有匹配的 (start, end)
        """
        # 拆分查询词组
        query_tokens = lemma_phrase.split()

        matches = []
        n = len(query_tokens)
        seq = self.lemma_index

        for i in range(len(seq) - n + 1):
            window = [lw for lw, _, _ in seq[i:i+n]]
            if window == query_tokens:
                start = seq[i][1]
                end = seq[i+n-1][2]
                matches.append((start, end))

        return matches
    
    def add_selected_word(self, word, need_emit=True):
        if not self.data_is_initialized:
            return
        is_custom = True
        original_word = word
        lemma_word = self.text_to_lemma(word)

        if lemma_word in [w[0] for w in self.text_split_result]:
            is_custom = False
        existed_words = [w[0] for w in self.selected_words+self.selected_custom_words]

        if lemma_word in existed_words:
            return
        if is_custom:
            matches = self.find_lemma_matches(lemma_word)
            if matches != []:
                self.selected_custom_words.append((lemma_word, matches))
                if need_emit:
                    self.textSelected.emit(lemma_word)

                self.viewport().update()
            
            return
        if original_word and lemma_word not in [w[0] for w, p in self.selected_words]:
            # 查找所有匹配word的位置
            poses = []
            for (w, s, e) in self.text_split_result:
                if w == lemma_word:
                    poses.append((s, e))
            if poses != []:
                self.selected_words.append((lemma_word, poses))
                if need_emit:
                    self.textSelected.emit(lemma_word)
                self.viewport().update()

    def remove_selected_word(self, word):
        word = self.text_to_lemma(word)
        self.selected_words = [item for item in self.selected_words if self.text_to_lemma(item[0]) != word]
        self.selected_custom_words = [item for item in self.selected_custom_words if self.text_to_lemma(item[0]) != word]
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
        word, word_rects = self.get_word_at_position(event.position().toPoint()) # type: ignore
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
        # 将text中所有换行符替换为""
        filtered_lines = [line.strip() for line in text.splitlines() if line.strip() != ""]
        text = " ".join(filtered_lines)

        self.text_split_result = list((self.text_to_lemma(w), s, e) for (w, s, e) in jieba.tokenize(text))
        self.data_is_initialized = True
        for w in selected_words: 
            self.add_selected_word(w)
        

        """
        建立 (lemma_word, start, end) 序列索引
        """
        text = self.toPlainText()
        self.lemma_index = []

        for m in re.finditer(r"\b\w+\b", text):
            original_word = m.group()
            start, end = m.span()
            lemma_word = self.text_to_lemma(original_word)
            self.lemma_index.append((lemma_word, start, end))

        self.dataInitialized.emit()

        QTimer.singleShot(100, self.resizeEvent)

    def stream_data_initialiaze(self, stream):
        
        text = "" 
        for piece in stream[0](stream[1]): 
            text += piece
            self.realTimeChangeTextSignal.emit(text)
            self.text = text
        self.data_initialization(text, selected_words=[])
        
    def real_time_change_text(self, text):
        super().setPlainText(text)
        self.adjust_height_to_content()
        self.parent.adjust_main_window_height_callback()

    def setPlainText(self, text, selected_words=[]):
        """重写设置文本方法"""
        if self.style_type == 1:
            super().setPlainText(text)
            self.text = text
            # 重置高亮状态
            self.data_is_initialized = False
            self.start_data_not_initialized_animation()

            threading.Thread(target=self.data_initialization, args=(text, selected_words,)).start()

            self.hovered_word = ""
            self.hovered_word_rect = QRect()
            self._highlight_opacity = 0
                
            # 自动调整高度
            self.adjust_height_to_content()
        else: 
            self.data_is_initialized = False
            self.start_data_not_initialized_animation()
            threading.Thread(target=self.stream_data_initialiaze, args=(text,)).start()

            self.hovered_word = ""
            self.hovered_word_rect = QRect()
            self._highlight_opacity = 0
                
            # 自动调整高度
            self.adjust_height_to_content()



    def wheelEvent(self, event):
        event.ignore()  # 忽略滚动事件（交给外层容器处理）
    
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
                # 取消选择状态
                cursor.clearSelection()
                self.setTextCursor(cursor)
                lemma_selected = self.text_to_lemma(selected_text)
                start_pos = cursor.selectionStart()
                end_pos = cursor.selectionEnd()
                existed_words = [w[0] for w in self.selected_words+self.selected_custom_words]
                if lemma_selected in existed_words:
                    self.remove_selected_word(selected_text)
                    self.textRemoved.emit(selected_text)
                    return
                else:
                    self.add_selected_word(selected_text)
                
            elif self.hovered_word:
                # 处理悬浮单词的选择/删除逻辑
                if self.text_to_lemma(self.hovered_word) in [w[0] for w in self.selected_words]:
                    self.remove_selected_word(self.hovered_word)
                    self.textRemoved.emit(self.text_to_lemma(self.hovered_word))
                
                else:
                    self.add_selected_word(self.hovered_word)

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
        painter.setRenderHint(QPainter.Antialiasing) # type: ignore
        
        # 设置画笔颜色和宽度
        painter.setBrush(QBrush(self.color))
        painter.setPen(Qt.NoPen) # type: ignore
        
        # 绘制矩形作为分隔线
        painter.drawRect(0, 0, self.width(), self.thickness)


class ContentBlock(QWidget):     
    def __init__(self, original_text, stream, parent=None, block_id=1, adjust_main_window_height_callback=None, sync_func=None, del_action_callback=None):
          
        super().__init__(parent)       

        self.setObjectName("ContentBlock")  
        self.setMouseTracking(True)
        self.split_line = None
        self.adjust_main_window_height_callback = adjust_main_window_height_callback    
        self.del_action_callback = del_action_callback
        
        layout = QVBoxLayout(self)
        
        # 创建标签并设置自动换行和对齐方式
        original_label = ContentLabel(original_text, self, style_type=1, global_selected=self.parent().global_selected_texts)
        
        translated_label = ContentLabel(stream, self, style_type=2)
        original_label.textSelected.connect(lambda text: sync_func(text, operation="add") if sync_func else None)
        translated_label.textSelected.connect(lambda text: sync_func(text, operation="add") if sync_func else None)
        original_label.textRemoved.connect(lambda text: sync_func(text, operation="remove") if sync_func else None)
        translated_label.textRemoved.connect(lambda text: sync_func(text, operation="remove") if sync_func else None)

        self.labels = [original_label, translated_label]

        self.add_select_funcs = [original_label.add_selected_word, translated_label.add_selected_word]
        self.remove_select_funcs = [original_label.remove_selected_word, translated_label.remove_selected_word]
        self.set_select_funcs = [original_label.set_selected_words, translated_label.set_selected_words]

        layout.addWidget(original_label)         
        layout.addWidget(SplitLine(thickness=1, color=QColor(255, 255, 255, 100)))         
        layout.addWidget(translated_label)          
        
        # 设置布局边距和间距
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(0)
        
        self.setLayout(layout)          
        
        # 设置尺寸策略，让组件能够扩展
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred) # type: ignore
        
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
            self.split_line.deleteLater()
        self.close()
        if self.del_action_callback:
            self.del_action_callback(self.labels, self)
        self.deleteLater() # 延迟更新高度，确保布局稳定
        
        
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
            parent_layout = self.parent().layout() # type: ignore
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


class VocabularyCard(QWidget):
    def __init__(self, vocab_data: dict, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WA_TranslucentBackground)  # 半透明背景
        self.setWindowFlag(Qt.FramelessWindowHint) # type: ignore
        self.setMouseTracking(True)
        
        # 设置窗口可调整大小
        self.setMinimumWidth(350)

        # 卡片样式配置
        self.style_args = {
            "background-color": QColor(40, 40, 40, 230),
            "font-color": QColor(240, 240, 240),
            "border-radius": 12,
            "padding": 12
        }

        # 动画状态标记
        self.is_animating = False

        self._drag_active = False
        self._drag_position = QPoint(0, 0)


        # 外层布局
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(20, 20, 20, 20)
        self.layout.setSpacing(8)

        # 创建富文本编辑器
        self.text_edit = QTextEdit()
        self._setup_text_edit()
        
        # 设置内容
        self._setup_content(vocab_data)
        
        self.layout.addWidget(self.text_edit)

        # 来源标签（保持在底部）
        source_urls = vocab_data.get("sourceUrls", [])
        if source_urls:
            self.layout.addStretch(1)
            src_label = QLabel(f"Source: {source_urls[0]}")
            src_label.setStyleSheet("font-size: 12px; color: #888888;")
            src_label.setAlignment(Qt.AlignCenter)
            src_label.setWordWrap(True)
            self.layout.addWidget(src_label)

        # ========= 动画 =========
        self.geometry_animation = QPropertyAnimation(self, b"geometry")
        self.geometry_animation.setEasingCurve(QEasingCurve.Type.OutCubic)
        self.geometry_animation.setDuration(1000)
        
        # 连接动画状态信号
        self.geometry_animation.finished.connect(self._on_animation_finished)

    def _setup_text_edit(self):
        """配置QTextEdit"""
        # 禁用编辑
        self.text_edit.setReadOnly(True)
        
        # 去除滚动条
        self.text_edit.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.text_edit.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        
        # 去除边框和背景
        self.text_edit.setFrameStyle(0)
        self.text_edit.setStyleSheet("""
            QTextEdit {
                background: transparent;
                border: none;
                padding: 0px;
            }
        """)
        
        # 禁用文本交互，避免鼠标样式更改
        self.text_edit.setTextInteractionFlags(Qt.TextInteractionFlag.NoTextInteraction)
        
        # 连接文档大小变化信号，自动调整高度
        self.text_edit.document().documentLayout().documentSizeChanged.connect(self._adjust_text_edit_height)

    def _adjust_text_edit_height(self):
        """根据内容调整QTextEdit高度"""
        # 动画期间不调整高度，避免影响动画效果
        if self.is_animating:
            return
            
        doc_height = int(self.text_edit.document().size().height())
        self.text_edit.setFixedHeight(doc_height + 5)  # 留一点余量

    def _setup_content(self, vocab_data):
        """设置富文本内容"""
        word = vocab_data.get("word", "")
        phonetics = [p.get("text", "") for p in vocab_data.get("phonetics", []) if p.get("text")]
        meanings = vocab_data.get("meanings", [])

        # 构建HTML内容
        html_content = []
        
        # 单词标题
        html_content.append(f'<h1 style="color: white; font-size: 22px; font-weight: bold; margin: 0px 0px 8px 0px;">{word}</h1>')
        
        # 音标
        if phonetics:
            phonetic_text = " , ".join(phonetics)
            html_content.append(f'<p style="color: #cccccc; font-size: 16px; margin: 0px 0px 12px 0px;">{phonetic_text}</p>')
        
        # 释义
        for meaning in meanings:
            part_of_speech = meaning.get("partOfSpeech", "")
            definitions = meaning.get("definitions", [])
            synonyms = meaning.get("synonyms", [])
            
            # 词性
            if part_of_speech:
                html_content.append(f'<p style="color: #88c0d0; font-size: 14px; font-style: italic; margin: 8px 0px 4px 0px;"><strong>{part_of_speech}</strong></p>')
            
            # 定义列表
            for i, definition in enumerate(definitions, 1):
                def_text = definition.get("definition", "")
                html_content.append(f'<p style="color: #eeeeee; font-size: 14px; margin: 2px 0px 2px 20px;">{i}. {def_text}</p>')
            
            # 近义词
            if synonyms:
                syn_text = ", ".join(synonyms)
                html_content.append(f'<p style="color: #a3be8c; font-size: 13px; margin: 6px 0px 8px 20px;"><strong>Synonyms:</strong> {syn_text}</p>')
        
        # 设置HTML内容
        html = "".join(html_content)
        self.text_edit.setHtml(html)

    def _on_animation_started(self):
        """动画开始时的处理"""
        self.is_animating = True
        # 暂时移除高度限制，让动画可以自由进行
        self.text_edit.setMaximumHeight(16777215)  # Qt的默认最大高度
        self.text_edit.setMinimumHeight(0)

    def _on_animation_finished(self):
        """动画结束时的处理"""
        self.is_animating = False
        # 恢复内容限制，重新调整高度
        self._adjust_text_edit_height()

    def start_show_animation(self, start_rect: QRect, end_rect: QRect):
        self._on_animation_started()
        self.geometry_animation.setStartValue(start_rect)
        self.geometry_animation.setEndValue(end_rect)
        self.geometry_animation.start()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        brush = QBrush(self.style_args["background-color"])
        painter.setBrush(brush)
        painter.setPen(Qt.NoPen)
        painter.drawRoundedRect(self.rect(), self.style_args["border-radius"], self.style_args["border-radius"])
        painter.end()

    def resizeEvent(self, event):
        """窗口大小改变时的处理"""
        if self.is_animating:
            # QTextEdit会自动处理内容重排，无需额外处理
            return
        super().resizeEvent(event)
        # 动画期间不处理resize事件对内容的影响
    
    def keyPressEvent(self, event):
        if event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
            self.close()
            self.deleteLater()
    

    def mousePressEvent(self, event: QMouseEvent):
        if event.button() == Qt.LeftButton:
            self._drag_active = True
            # 记录鼠标相对窗口左上角的位置
            self._drag_position = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            event.accept()
        super().mousePressEvent(event)
    
    def mouseReleaseEvent(self, event: QMouseEvent):
        if event.button() == Qt.LeftButton:
            self._drag_active = False
            event.accept()
        super().mouseReleaseEvent(event)

    def mouseMoveEvent(self, event: QMouseEvent):
        
        if self._drag_active and event.buttons() & Qt.LeftButton:
            self.move(event.globalPosition().toPoint() - self._drag_position)
            event.accept()



class BottomBar(QWidget):
    def __init__(self, parent=None):
        super().__init__()
        self.setAttribute(Qt.WA_TranslucentBackground) # type: ignore
        self.setWindowFlag(Qt.FramelessWindowHint) # type: ignore
        self.setMouseTracking(True)

        self.style_args = {
            "background-color": QColor(20, 20, 20, 200),
            "font-size": "16px",
            "padding": "10px",
            "border-radius": 10
        }
        self.state = 1
        self.animation_running = False
        self.parent = parent

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

        def clear_content():
            blocks = [*self.parent.content_blocks]
            for block in blocks: 
                block._start_close_animation()
            pass

        self.stop_button.clicked.connect(stop_read)
        self.cancel_button.clicked.connect(cancel_read)
        self.continue_button.clicked.connect(continue_read)
        self.clear_button.clicked.connect(clear_content)

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
        if self.parent:
            current_rect = self.geometry()
            end_geo = self.parent.get_bar_geo(state=1) 
            
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
        if self.parent:
            current_rect = self.geometry()
            end_geo = self.parent.get_bar_geo(state=0)   # 隐藏状态 # type: ignore
            
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
            painter.setRenderHint(QPainter.Antialiasing) # type: ignore
            brush = QBrush(self.style_args["background-color"])
            painter.setBrush(brush)
            painter.setPen(Qt.NoPen) # type: ignore
            painter.drawRoundedRect(self.rect(), self.style_args["border-radius"], self.style_args["border-radius"])
        except Exception as e:
            print(f"绘制错误: {e}")
        finally:
            # 修复：确保painter正确结束
            if painter.isActive():
                painter.end()


class BlurWindow(QWidget):
    addContentBlockSignal = Signal(str, object, object)

    def __init__(self):
        super().__init__()
        self.setAttribute(Qt.WA_TranslucentBackground)  # 透明背景 # type: ignore
        self.setWindowFlag(Qt.FramelessWindowHint)  # type: ignore
        self.setMouseTracking(True)     # 去掉窗口边框


        self._drag_active = False
        self._drag_position = QPoint(0, 0)


        self.global_selected_texts = []
        self.text_history = []


        self.add_selected_text_funcs = []
        self.remove_selected_text_funcs = []
        self.set_selected_text_funcs = []

        self.content_blocks = []

        self.get_definition_func = lambda word: {}


        self._height_anim = QPropertyAnimation(self, b"height_prop")
        self._height_anim.setDuration(300)
        self._height_anim.setEasingCurve(QEasingCurve.InOutQuad)

        # 初始高度
        self.setMaximumHeight(800)

        # 样式参数
        self.style_args = {
            "background-color": QColor(40, 40, 40, 230),
            "font-size": "16px",
            "padding": "10px",
            "border-radius": 10
        }

        # ========== ScrollArea ==========
        self.scroll_area = QScrollArea(self)

        self.scroll_area.setMouseTracking(True)
        self.scroll_area.viewport().setMouseTracking(True)

        self.scroll_area.setWidgetResizable(True)  # 随内容调整大小
        self.scroll_area.setFrameShape(QScrollArea.NoFrame)  # 去掉边框 # type: ignore
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)  # 只要垂直滚动条 # type: ignore
        
        self.scroll_area.setStyleSheet("QScrollArea { background: transparent; }")
        content_widget = QWidget()
        content_widget.setMouseTracking(True)
        content_widget.setAutoFillBackground(False)
        content_widget.setStyleSheet("QWidget { background: transparent; }")
        
        self.content_layout = QVBoxLayout(content_widget)
        self.content_layout.setContentsMargins(0, 0, 0, 0)
        self.content_layout.setSpacing(0)

        self.content_layout.addStretch(2)  # 底部弹性空间

        self.scroll_area.setWidget(content_widget)

        # ========== 创建BottomBar ==========
        self.bottom_bar = BottomBar(self)
        self.bottom_bar.setParent(self)
        self.bottom_bar.setFixedHeight(60)
        self.bar_height = 60

        # ========== 主布局 ==========
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 10, 0, 10)
        layout.addWidget(self.scroll_area)
        self.setLayout(layout)

        self.addContentBlockSignal.connect(self.add_content_block)

    def block_del_callback(self, labels, contentblock=None):
        """内容块删除回调"""
        for label in labels:
            if label.text in self.text_history:
                self.text_history.remove(label.text)
        if contentblock:
            if contentblock in self.content_blocks: 
                self.content_blocks.remove(contentblock)
        QTimer.singleShot(100, lambda: self.adjust_height_animation(False))

    def add_content_block(self, original_text, stream, sync_selected_text_func):
        """添加内容块"""
        block = ContentBlock(original_text, stream, adjust_main_window_height_callback=self.adjust_height_animation, sync_func=sync_selected_text_func, del_action_callback=self.block_del_callback, parent=self) # type: ignore
        self.content_blocks.append(block)
        split_line = SplitLine()
        block.setMouseTracking(True)
        block.set_split_line(split_line)
        self.set_selected_text_funcs += block.set_select_funcs 
        self.add_selected_text_funcs += block.add_select_funcs
        self.remove_selected_text_funcs += block.remove_select_funcs

        for func in block.set_select_funcs:
            func(self.global_selected_texts)

        self.content_layout.insertWidget(self.content_layout.count()-1, block)  
        self.content_layout.insertWidget(self.content_layout.count()-1, split_line)

        self.content_layout.update()
        self.content_layout.activate()

        QTimer.singleShot(100, self.adjust_height_animation)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing) # type: ignore
        brush = QBrush(self.style_args["background-color"])
        painter.setBrush(brush)
        painter.setPen(Qt.NoPen) # type: ignore
        painter.drawRoundedRect(self.rect(), self.style_args["border-radius"], self.style_args["border-radius"])
    
    def get_bar_geo(self, state=1):
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
    
    def adjust_height_animation(self, to_bottom=True):
        # 计算所有 ContentBlock 和 SplitLine 的总高度
        total_height = 0
        for i in range(self.content_layout.count()):
            item = self.content_layout.itemAt(i)
            widget = item.widget()
            if widget and isinstance(widget, (ContentBlock, SplitLine)):
                total_height += widget.height()

        # 加上底部弹性空间的高度
        stretch_height = 0
        for i in range(self.content_layout.count()):
            if self.content_layout.itemAt(i).spacerItem():
                stretch_height += self.content_layout.itemAt(i).spacerItem().sizeHint().height()

        target_height = min(total_height + stretch_height, 800)

        # 如果没有内容，高度过渡到0
        if self.content_layout.count() == 1:
            target_height = 0


        self._height_anim.stop()
        self._height_anim.setStartValue(self.height())
        self._height_anim.setEndValue(target_height)
        self._height_anim.start()

        if to_bottom:
            # scroll_to_bottom
            if self.height() != self.maximumHeight():
                QTimer.singleShot(350, lambda: self.scroll_area.verticalScrollBar().setValue(self.scroll_area.verticalScrollBar().maximum()))
            else:
                QTimer.singleShot(150, lambda: self.scroll_area.verticalScrollBar().setValue(self.scroll_area.verticalScrollBar().maximum()))


    def getHeight(self):
        return self.height()

    def setHeight(self, h):
        self.resize(self.width(), h) 

    height_prop = Property(int, getHeight, setHeight)  # 自定义高度属性

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

    def mousePressEvent(self, event: QMouseEvent):
        if event.button() == Qt.LeftButton:
            self._drag_active = True
            # 记录鼠标相对窗口左上角的位置
            self._drag_position = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            event.accept()
        super().mousePressEvent(event)
    
    def mouseReleaseEvent(self, event: QMouseEvent):
        if event.button() == Qt.LeftButton:
            self._drag_active = False
            event.accept()
        super().mouseReleaseEvent(event)

    def mouseMoveEvent(self, event: QMouseEvent):
        
        if self._drag_active and event.buttons() & Qt.LeftButton:
            self.move(event.globalPosition().toPoint() - self._drag_position)
            event.accept()
         # 根据鼠标位置和当前状态决定显示或隐藏 BottomBar
        if (event.position().y() < self.height() - 100 and self.bottom_bar.state == 1) or self.content_layout.count() == 1:
            self.bottom_bar.start_hide_animation()
        elif event.position().y() > self.height() - 30 and self.bottom_bar.state == 0:
            self.bottom_bar.start_show_animation()
        return super().mouseMoveEvent(event)


