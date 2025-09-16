from PySide6.QtWidgets import QWidget, QApplication, QPushButton, QVBoxLayout, QMainWindow, QLabel
from PySide6.QtCore import QPropertyAnimation, QEasingCurve, Property
from PySide6.QtGui import QColor, QPainter, QPaintEvent
import sys

class BreathingWidgetAdvanced(QWidget):
    def __init__(self):
        super().__init__()
        # 定义颜色
        self.original_color = QColor(255, 100, 100, 100)  # 原始颜色
        self._background_color = self.original_color
        
        # 动画相关
        self.color_breath_animation = None
        self.stop_animation = None  # 用于停止时的过渡动画
        self.is_running = False
        self.breathing_in = True
        
        self.setup_advanced_animation()
        
    def setup_advanced_animation(self):
        """设置呼吸灯动画"""
        self.color_breath_animation = QPropertyAnimation(self, b"background_color")
        self.color_breath_animation.setDuration(1500)  # 1.5秒
        self.color_breath_animation.setEasingCurve(QEasingCurve.Type.InOutQuad)
        
        # 连接动画完成信号到循环函数
        self.color_breath_animation.finished.connect(self._on_breath_animation_finished)
        
        # 定义颜色范围
        self.min_color = QColor(255, 100, 100, 30)   # 最暗红色
        self.max_color = QColor(255, 100, 100, 220)  # 最亮红色
        
        # 设置停止动画
        self.stop_animation = QPropertyAnimation(self, b"background_color")
        self.stop_animation.setDuration(300)  # 0.3秒过渡
        self.stop_animation.setEasingCurve(QEasingCurve.Type.OutCubic)
    
    def start_breathing(self):
        """开始呼吸动画"""
        if self.is_running:
            return
            
        self.is_running = True
        self.breathing_in = True
        self._start_breathing_cycle()
    
    def stop_breathing(self):
        """停止呼吸动画并过渡到原始颜色"""
        if not self.is_running:
            return
            
        self.is_running = False
        
        # 停止当前动画
        if self.color_breath_animation.state() == QPropertyAnimation.State.Running:
            self.color_breath_animation.stop()
        
        # 启动过渡到原始颜色的动画
        current_color = self._background_color
        self.stop_animation.setStartValue(current_color)
        self.stop_animation.setEndValue(self.original_color)
        self.stop_animation.start()
    
    def toggle_breathing(self):
        """切换呼吸动画状态"""
        if self.is_running:
            self.stop_breathing()
        else:
            self.start_breathing()
    
    def _start_breathing_cycle(self):
        """开始一个呼吸周期"""
        if not self.is_running:
            return
            
        if self.breathing_in:
            # 从暗到亮
            self.color_breath_animation.setStartValue(self.min_color)
            self.color_breath_animation.setEndValue(self.max_color)
        else:
            # 从亮到暗
            self.color_breath_animation.setStartValue(self.max_color)
            self.color_breath_animation.setEndValue(self.min_color)
        
        self.color_breath_animation.start()
    
    def _on_breath_animation_finished(self):
        """动画完成回调"""
        # 只有在运行状态下才继续循环
        if self.is_running and self.sender() == self.color_breath_animation:
            self.breathing_in = not self.breathing_in
            self._start_breathing_cycle()

    @Property(QColor)
    def background_color(self):
        return self._background_color
    
    @background_color.setter
    def background_color(self, color):
        self._background_color = color
        self.update()
        
    def paintEvent(self, event: QPaintEvent):
        painter = QPainter(self)
        painter.fillRect(self.rect(), self._background_color)

class BreathingControlDemo(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setup_ui()
        
    def setup_ui(self):
        """设置用户界面"""
        central_widget = QWidget()
        layout = QVBoxLayout()
        
        # 标题
        title_label = QLabel("可控制的呼吸灯动画")
        title_label.setStyleSheet("font-size: 16px; font-weight: bold; margin: 10px;")
        
        # 呼吸灯组件
        self.breathing_widget = BreathingWidgetAdvanced()
        self.breathing_widget.setFixedSize(400, 200)
        
        # 控制按钮
        self.start_button = QPushButton("开始呼吸灯")
        self.start_button.clicked.connect(self.breathing_widget.start_breathing)
        
        self.stop_button = QPushButton("停止呼吸灯")
        self.stop_button.clicked.connect(self.breathing_widget.stop_breathing)
        
        self.toggle_button = QPushButton("切换状态")
        self.toggle_button.clicked.connect(self.breathing_widget.toggle_breathing)
        
        # 状态显示
        self.status_label = QLabel("状态: 已停止")
        
        # 添加到布局
        layout.addWidget(title_label)
        layout.addWidget(self.breathing_widget)
        layout.addWidget(self.start_button)
        layout.addWidget(self.stop_button)
        layout.addWidget(self.toggle_button)
        layout.addWidget(self.status_label)
        
        central_widget.setLayout(layout)
        self.setCentralWidget(central_widget)
        
        # 更新状态显示
        self.setup_status_update()
        
    def setup_status_update(self):
        """设置状态更新"""
        # 使用定时器定期更新状态显示
        from PySide6.QtCore import QTimer
        
        self.status_timer = QTimer()
        self.status_timer.timeout.connect(self.update_status)
        self.status_timer.start(100)  # 每100ms更新一次
        
    def update_status(self):
        """更新状态显示"""
        if self.breathing_widget.is_running:
            direction = "变亮" if self.breathing_widget.breathing_in else "变暗"
            animation_state = "运行中" if self.breathing_widget.color_animation.state() == QPropertyAnimation.State.Running else "暂停"
            self.status_label.setText(f"状态: 运行中 ({direction}) - {animation_state}")
        else:
            stop_state = "过渡中" if self.breathing_widget.stop_animation.state() == QPropertyAnimation.State.Running else "已停止"
            self.status_label.setText(f"状态: {stop_state}")

# 简化版本 - 只需要基本控制功能
class SimpleBreathingWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.original_color = QColor(100, 150, 255, 120)
        self._background_color = self.original_color
        
        self.setup_animations()
        
    def setup_animations(self):
        """设置动画"""
        # 呼吸动画
        self.breathing_animation = QPropertyAnimation(self, b"background_color")
        self.breathing_animation.setDuration(2000)
        self.breathing_animation.setEasingCurve(QEasingCurve.Type.InOutSine)
        self.breathing_animation.finished.connect(self._continue_breathing)
        
        # 停止过渡动画
        self.stop_transition = QPropertyAnimation(self, b"background_color")
        self.stop_transition.setDuration(300)
        self.stop_transition.setEasingCurve(QEasingCurve.Type.OutCubic)
        
        # 状态
        self.is_breathing = False
        self.breathing_direction = True  # True: 变亮, False: 变暗
        
    def start_breathing(self):
        """开始呼吸动画"""
        if self.is_breathing:
            return
            
        self.is_breathing = True
        self._do_breathing_cycle()
        
    def stop_breathing(self):
        """停止并过渡到原始颜色"""
        if not self.is_breathing:
            return
            
        self.is_breathing = False
        self.breathing_animation.stop()
        
        # 过渡到原始颜色
        self.stop_transition.setStartValue(self._background_color)
        self.stop_transition.setEndValue(self.original_color)
        self.stop_transition.start()
        
    def _do_breathing_cycle(self):
        """执行一个呼吸周期"""
        if not self.is_breathing:
            return
            
        if self.breathing_direction:
            # 变亮
            start_color = QColor(100, 150, 255, 50)
            end_color = QColor(100, 150, 255, 200)
        else:
            # 变暗
            start_color = QColor(100, 150, 255, 200)
            end_color = QColor(100, 150, 255, 50)
            
        self.breathing_animation.setStartValue(start_color)
        self.breathing_animation.setEndValue(end_color)
        self.breathing_animation.start()
        
    def _continue_breathing(self):
        """继续呼吸动画"""
        if self.is_breathing:
            self.breathing_direction = not self.breathing_direction
            self._do_breathing_cycle()

    @Property(QColor)
    def background_color(self):
        return self._background_color
    
    @background_color.setter
    def background_color(self, color):
        self._background_color = color
        self.update()
        
    def paintEvent(self, event: QPaintEvent):
        painter = QPainter(self)
        painter.fillRect(self.rect(), self._background_color)

# 使用示例
if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    # 创建演示窗口
    demo = BreathingControlDemo()
    demo.setWindowTitle("呼吸灯控制演示")
    demo.resize(500, 400)
    demo.show()
    
    sys.exit(app.exec())