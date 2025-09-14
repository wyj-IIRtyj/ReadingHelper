
class ContentBlock(QWidget):     
    def __init__(self, original_text, translated_text, parent=None):         
        super().__init__(parent)       

        self.setObjectName("ContentBlock")  
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

