from PySide6.QtWidgets import *
from PySide6.QtCore import *
from PySide6.QtGui import *

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
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setWindowFlag(Qt.FramelessWindowHint)

        self.style_args = {
            "background-color": QColor(20, 20, 20, 200),
            "font-size": "16px",
            "padding": "10px",
            "border-radius": 10
        }

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

        # 初始隐藏某些按钮
        self.stop_button.start_hide_animation()
        self.continue_button.start_hide_animation()
        self.cancel_button.start_hide_animation()

        # 设置布局
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

        # ============ BottomBar 显示/隐藏动画设置 ============
        
        # 几何形状动画 (位置和大小)
        self.geometry_animation = QPropertyAnimation(self, b"geometry")
        self.geometry_animation.setEasingCurve(QEasingCurve.Type.OutCubic)
        self.geometry_animation.setDuration(400)
        
        # 透明度动画
        self.bar_opacity_effect = QGraphicsOpacityEffect(self)
        self.setGraphicsEffect(self.bar_opacity_effect)
        self.bar_opacity_effect.setOpacity(1.0)
        
        self.bar_opacity_animation = QPropertyAnimation(self.bar_opacity_effect, b"opacity")
        self.bar_opacity_animation.setEasingCurve(QEasingCurve.Type.OutCubic)
        self.bar_opacity_animation.setDuration(300)

        # 动画组 - 同时执行几何形状和透明度动画
        self.show_animation_group = QParallelAnimationGroup()
        self.show_animation_group.addAnimation(self.geometry_animation)
        
        self.hide_animation_group = QParallelAnimationGroup()
        self.hide_animation_group.addAnimation(self.geometry_animation)

        # 动画状态标志
        self.is_visible_state = True
        self.animation_running = False

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

    def start_show_animation(self):
        """显示 BottomBar 的动画"""
        if self.animation_running or self.is_visible_state:
            return
            
        self.animation_running = True
        self.is_visible_state = True
        
        # 确保 widget 可见
        self.show()
        
        # 获取起始和结束位置
        if self.parent():
            current_rect = self.geometry()
            start_geo = self.parent().get_bar_geo(state=0)  # 隐藏状态
            end_geo = self.parent().get_bar_geo(state=1)    # 显示状态
            
            # 设置几何动画
            self.geometry_animation.setStartValue(current_rect)
            self.geometry_animation.setEndValue(QRect(*end_geo))
            
            # 设置透明度动画
            self.bar_opacity_animation.setStartValue(0.0)
            self.bar_opacity_animation.setEndValue(1.0)
            
            # 动画完成后的处理
            def on_show_finished():
                self.animation_running = False
            
            # 清除之前的连接
            try:
                self.show_animation_group.finished.disconnect()
            except:
                pass
                
            self.show_animation_group.finished.connect(on_show_finished)
            self.show_animation_group.start()

    def start_hide_animation(self):
        """隐藏 BottomBar 的动画"""
        if self.animation_running or not self.is_visible_state:
            return
            
        self.animation_running = True
        self.is_visible_state = False
        
        # 获取起始和结束位置
        if self.parent():
            current_rect = self.geometry()
            start_geo = self.parent().get_bar_geo(state=1)  # 显示状态
            end_geo = self.parent().get_bar_geo(state=0)    # 隐藏状态
            
            # 设置几何动画
            self.geometry_animation.setStartValue(current_rect)
            self.geometry_animation.setEndValue(QRect(*end_geo))
            
            # 设置透明度动画
            self.bar_opacity_animation.setStartValue(1.0)
            self.bar_opacity_animation.setEndValue(0.0)
            
            # 动画完成后隐藏 widget
            def on_hide_finished():
                self.animation_running = False
                self.hide()  # 完全隐藏 widget
            
            # 清除之前的连接
            try:
                self.hide_animation_group.finished.disconnect()
            except:
                pass
                
            self.hide_animation_group.finished.connect(on_hide_finished)
            self.hide_animation_group.start()

    def toggle_visibility(self):
        """切换显示/隐藏状态"""
        if self.is_visible_state:
            self.start_hide_animation()
        else:
            self.start_show_animation()

    def set_visible_immediately(self, visible):
        """立即设置可见性，无动画"""
        if visible:
            if self.parent():
                geo = self.parent().get_bar_geo(state=1)
                self.setGeometry(*geo)
            self.bar_opacity_effect.setOpacity(1.0)
            self.show()
            self.is_visible_state = True
        else:
            self.hide()
            self.bar_opacity_effect.setOpacity(0.0)
            self.is_visible_state = False

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        brush = QBrush(self.style_args["background-color"])
        painter.setBrush(brush)
        painter.setPen(Qt.NoPen)
        painter.drawRoundedRect(self.rect(), self.style_args["border-radius"], self.style_args["border-radius"])


# 示例：模拟父级控件
class ParentWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("BottomBar Animation Demo")
        self.resize(800, 600)
        
        # 设置 bar_height 属性
        self.bar_height = 60
        
        # 创建 BottomBar
        self.bottom_bar = BottomBar(self)
        
        # 初始设置位置
        geo = self.get_bar_geo(state=1)
        self.bottom_bar.setGeometry(*geo)
        
        # 添加测试按钮
        self.test_button = QPushButton("Toggle BottomBar", self)
        self.test_button.setGeometry(50, 50, 150, 30)
        self.test_button.clicked.connect(self.bottom_bar.toggle_visibility)
        
        # 添加快捷键
        self.shortcut = QShortcut(QKeySequence("Ctrl+B"), self)
        self.shortcut.activated.connect(self.bottom_bar.toggle_visibility)

    def get_bar_geo(self, state=1):
        """返回 BottomBar 的几何位置"""
        if state:
            # 显示状态：计算BottomBar的宽度和位置
            window_width = self.width()
            bar_width = int(window_width * 0.8)  # 横向占窗口宽度的80%
            bar_height = self.bar_height
            
            # 居中横向位置，底部对齐（留出一点边距）
            x = (window_width - bar_width) // 2
            y = self.height() - bar_height - 20  # 距离底部20px
            return (x, y, bar_width, bar_height)
        else: 
            # 隐藏状态：移到窗口底部外面
            window_width = self.width()
            bar_width = int(window_width) 
            x = (window_width - bar_width) // 2
            y = self.height()  # 完全移出窗口
            return (x, y, bar_width, 0)

    def resizeEvent(self, event):
        """窗口大小改变时更新 BottomBar 位置"""
        super().resizeEvent(event)
        if hasattr(self, 'bottom_bar') and self.bottom_bar.is_visible_state:
            # 如果 BottomBar 当前是可见的，更新其位置
            geo = self.get_bar_geo(state=1)
            self.bottom_bar.setGeometry(*geo)


# 使用示例
if __name__ == "__main__":
    import sys
    
    app = QApplication(sys.argv)
    
    # 这里需要包含 NormalButton 类的定义
    # 为了演示，我添加一个简化版本
    
    
    window = ParentWidget()
    window.show()
    
    print("提示：")
    print("- 点击 'Toggle BottomBar' 按钮或按 Ctrl+B 来切换 BottomBar 显示/隐藏")
    print("- BottomBar 会从窗口底部滑入/滑出，同时有透明度变化")
    
    sys.exit(app.exec_())