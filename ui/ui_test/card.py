from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QTextEdit, QApplication
from PySide6.QtCore import Qt, QRect, QPropertyAnimation, QEasingCurve, QTimer
from PySide6.QtGui import QPainter, QBrush, QColor, QFont, QTextDocument

import sys



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


data = {
    "word": "as",
    "phonetics": [
      {
        "audio": "https://api.dictionaryapi.dev/media/pronunciations/en/as-1-us.mp3",
        "sourceUrl": "https://commons.wikimedia.org/w/index.php?curid=192078",
        "license": {
          "name": "BY-SA 3.0",
          "url": "https://creativecommons.org/licenses/by-sa/3.0"
        }
      }
    ],
    "meanings": [
      {
        "partOfSpeech": "adverb",
        "definitions": [
          {
            "definition": "To such an extent or degree; to the same extent or degree.",
            "synonyms": [],
            "antonyms": [],
            "example": "It's not as well made, but it's twice as expensive."
          },
          {
            "definition": "Considered to be, in relation to something else; in the relation (specified).",
            "synonyms": [],
            "antonyms": [],
            "example": "1865, The Act of Suicide as Distinct from the Crime of Self-Murder: A Sermon"
          },
          {
            "definition": "For example; for instance. (Compare such as.)",
            "synonyms": [],
            "antonyms": []
          }
        ],
        "synonyms": [],
        "antonyms": []
      },
      {
        "partOfSpeech": "preposition",
        "definitions": [
          {
            "definition": "Introducing a basis of comparison, with an object in the objective case.",
            "synonyms": [],
            "antonyms": [],
            "example": "They're big as houses."
          },
          {
            "definition": "In the role of.",
            "synonyms": [],
            "antonyms": [],
            "example": "He was never seen as the boss, but rather as a friend."
          }
        ],
        "synonyms": [],
        "antonyms": []
      },
      {
        "partOfSpeech": "conjunction",
        "definitions": [
          {
            "definition": "In the (same) way or manner that; to the (same) degree that.",
            "synonyms": [],
            "antonyms": [],
            "example": "As you wish, my lord!"
          },
          {
            "definition": "At the time that; during the time when:",
            "synonyms": [],
            "antonyms": []
          },
          {
            "definition": "Being that, considering that, because, since.",
            "synonyms": [],
            "antonyms": [],
            "example": "As it’s too late, I quit."
          },
          {
            "definition": "Introducing a comparison with a hypothetical state (+ subjunctive, or with the verb elided): as though, as if.",
            "synonyms": [],
            "antonyms": []
          },
          {
            "definition": "Functioning as a relative conjunction, and sometimes like a relative pronoun: that, which, who. (See usage notes.)",
            "synonyms": [],
            "antonyms": [],
            "example": "He had the same problem as she did getting the lock open."
          },
          {
            "definition": "(possibly obsolete) Than.",
            "synonyms": [],
            "antonyms": []
          }
        ],
        "synonyms": [
          "while",
          "whilst",
          "given that",
          "seeing that",
          "albeit",
          "although"
        ],
        "antonyms": []
      }
    ],
    "license": {
      "name": "CC BY-SA 3.0",
      "url": "https://creativecommons.org/licenses/by-sa/3.0"
    },
    "sourceUrls": [
      "https://en.wiktionary.org/wiki/as"
    ]
  }


if __name__ == "__main__":
    app = QApplication(sys.argv)
    card = VocabularyCard(data)
    card.setGeometry(0, 0, 400, 0)
    card.show()

    sys.exit(app.exec())