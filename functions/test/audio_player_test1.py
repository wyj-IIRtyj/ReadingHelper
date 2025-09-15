import sys
import asyncio
import threading
import io
from PySide6.QtWidgets import (QApplication, QMainWindow, QVBoxLayout, 
                               QHBoxLayout, QWidget, QPushButton, QTextEdit, 
                               QLabel, QComboBox, QSlider, QProgressBar)
from PySide6.QtCore import Qt, QTimer, Signal, QObject, QThread
from PySide6.QtMultimedia import QMediaPlayer, QAudioOutput, QMediaDevices
from PySide6.QtCore import QUrl, QByteArray, QIODevice, QBuffer
import edge_tts
from edge_tts import VoicesManager

class TTSWorker(QObject):
    """TTS工作线程"""
    finished = Signal(bytes)
    error = Signal(str)
    
    def __init__(self):
        super().__init__()
        self.text_data = []
        self.voice = "en-GB-RyanNeural"
    
    def set_params(self, text_data, voice):
        self.text_data = text_data
        self.voice = voice
    
    async def generate_audio_async(self, text: str, voice: str = "en-GB-RyanNeural") -> bytes:
        """生成音频并返回音频流数据"""
        try:
            communicate = edge_tts.Communicate(text, voice, rate='-15%')
            audio_data = b""
            
            async for chunk in communicate.stream():
                if chunk["type"] == "audio":
                    audio_chunk_data = chunk.get("data")
                    if audio_chunk_data is not None:
                        audio_data += audio_chunk_data
            
            return audio_data
        except Exception as e:
            raise e
    
    def append_silence(self, audio_data: bytes, silence_duration: float, 
                      sample_rate: int, sample_width: int, num_channels: int) -> bytes:
        """在音频末尾添加静音"""
        silence_frames = int(sample_rate * silence_duration)
        silence_bytes = silence_frames * sample_width * num_channels
        silence_data = b'\x00' * silence_bytes
        return audio_data + silence_data
    
    def generate_audio(self):
        """生成完整音频数据"""
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            sample_rate = 24000
            sample_width = 2
            num_channels = 1
            
            data = b''
            for text in self.text_data:
                if text.strip():  # 只处理非空文本
                    voice_data = loop.run_until_complete(
                        self.generate_audio_async(text, self.voice)
                    )
                    data += voice_data
                    data = self.append_silence(data, 1.0, sample_rate, sample_width, num_channels)
            
            loop.close()
            self.finished.emit(data)
            
        except Exception as e:
            self.error.emit(str(e))

class AudioPlayer(QObject):
    """音频播放器"""
    position_changed = Signal(int)
    duration_changed = Signal(int)
    state_changed = Signal(str)
    
    def __init__(self):
        super().__init__()
        self.player = QMediaPlayer()
        self.audio_output = QAudioOutput()
        self.player.setAudioOutput(self.audio_output)
        self.buffer = None
        self.io_device = None
        
        # 连接信号
        self.player.positionChanged.connect(self._on_position_changed)
        self.player.durationChanged.connect(self._on_duration_changed)
        self.player.playbackStateChanged.connect(self._on_state_changed)
    
    def _on_position_changed(self, position):
        """处理位置变化信号"""
        self.position_changed.emit(int(position))
    
    def _on_duration_changed(self, duration):
        """处理时长变化信号"""
        self.duration_changed.emit(int(duration))
        
    def _on_state_changed(self, state):
        if state == QMediaPlayer.PlaybackState.PlayingState:
            self.state_changed.emit("播放中")
        elif state == QMediaPlayer.PlaybackState.PausedState:
            self.state_changed.emit("暂停")
        else:
            self.state_changed.emit("停止")
    
    def load_audio_data(self, audio_data: bytes):
        """加载音频数据"""
        try:
            # 创建WAV文件头
            wav_header = self._create_wav_header(audio_data)
            full_audio_data = wav_header + audio_data
            
            # 创建QBuffer
            self.buffer = QBuffer()
            self.buffer.setData(QByteArray(full_audio_data))
            self.buffer.open(QIODevice.ReadOnly)
            
            # 设置媒体源
            self.player.setSourceDevice(self.buffer)
            
        except Exception as e:
            print(f"加载音频数据出错: {e}")
    
    def _create_wav_header(self, audio_data):
        """创建WAV文件头"""
        sample_rate = 24000
        sample_width = 2
        num_channels = 1
        
        data_size = len(audio_data)
        file_size = data_size + 36
        
        header = b'RIFF'
        header += file_size.to_bytes(4, 'little')
        header += b'WAVE'
        header += b'fmt '
        header += (16).to_bytes(4, 'little')  # fmt chunk size
        header += (1).to_bytes(2, 'little')   # audio format (PCM)
        header += num_channels.to_bytes(2, 'little')
        header += sample_rate.to_bytes(4, 'little')
        header += (sample_rate * num_channels * sample_width).to_bytes(4, 'little')  # byte rate
        header += (num_channels * sample_width).to_bytes(2, 'little')  # block align
        header += (sample_width * 8).to_bytes(2, 'little')  # bits per sample
        header += b'data'
        header += data_size.to_bytes(4, 'little')
        
        return header
    
    def play(self):
        """开始播放"""
        self.player.play()
    
    def pause(self):
        """暂停播放"""
        self.player.pause()
    
    def stop(self):
        """停止播放"""
        self.player.stop()
    
    def set_position(self, position):
        """设置播放位置"""
        self.player.setPosition(position)
    
    def set_volume(self, volume):
        """设置音量 (0-100)"""
        self.audio_output.setVolume(volume / 100.0)
    
    def set_output_device(self, device_info):
        """设置音频输出设备"""
        self.audio_output = QAudioOutput(device_info)
        self.player.setAudioOutput(self.audio_output)

class TTSPlayerWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Edge TTS 播放器")
        self.setGeometry(100, 100, 800, 600)
        
        # 初始化组件
        self.init_ui()
        self.init_audio_player()
        self.init_tts_worker()
        
        # 音频数据
        self.current_audio_data = None
    
    def init_ui(self):
        """初始化用户界面"""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        layout = QVBoxLayout(central_widget)
        
        # 文本输入区域
        layout.addWidget(QLabel("输入文本 (每行一句):"))
        self.text_edit = QTextEdit()
        self.text_edit.setPlainText("Hello, this is a test.\nThis is the second line.\nAnd this is the third line.")
        layout.addWidget(self.text_edit)
        
        # 语音和设备选择
        voice_layout = QHBoxLayout()
        voice_layout.addWidget(QLabel("语音:"))
        self.voice_combo = QComboBox()
        self.voice_combo.addItems([
            "en-GB-RyanNeural", "en-US-JennyNeural", "en-US-GuyNeural",
            "zh-CN-XiaoxiaoNeural", "zh-CN-YunxiNeural"
        ])
        voice_layout.addWidget(self.voice_combo)
        
        # 音频输出设备选择
        voice_layout.addWidget(QLabel("输出设备:"))
        self.device_combo = QComboBox()
        self.populate_audio_devices()
        self.device_combo.currentIndexChanged.connect(self.change_output_device)
        voice_layout.addWidget(self.device_combo)
        
        voice_layout.addStretch()
        layout.addLayout(voice_layout)
        
        # 生成按钮
        self.generate_btn = QPushButton("生成语音")
        self.generate_btn.clicked.connect(self.generate_audio)
        layout.addWidget(self.generate_btn)
        
        # 播放控制按钮
        control_layout = QHBoxLayout()
        self.play_btn = QPushButton("开始播放")
        self.play_btn.clicked.connect(self.play_audio)
        self.play_btn.setEnabled(False)
        
        self.pause_btn = QPushButton("暂停播放")
        self.pause_btn.clicked.connect(self.pause_audio)
        self.pause_btn.setEnabled(False)
        
        self.resume_btn = QPushButton("继续播放")
        self.resume_btn.clicked.connect(self.resume_audio)
        self.resume_btn.setEnabled(False)
        
        self.stop_btn = QPushButton("停止播放")
        self.stop_btn.clicked.connect(self.stop_audio)
        self.stop_btn.setEnabled(False)
        
        control_layout.addWidget(self.play_btn)
        control_layout.addWidget(self.pause_btn)
        control_layout.addWidget(self.resume_btn)
        control_layout.addWidget(self.stop_btn)
        layout.addLayout(control_layout)
        
        # 进度条
        self.progress_bar = QProgressBar()
        self.progress_bar.setEnabled(False)
        layout.addWidget(self.progress_bar)
        
        # 音量控制
        volume_layout = QHBoxLayout()
        volume_layout.addWidget(QLabel("音量:"))
        self.volume_slider = QSlider(Qt.Horizontal)
        self.volume_slider.setRange(0, 100)
        self.volume_slider.setValue(70)
        self.volume_slider.valueChanged.connect(self.set_volume)
        volume_layout.addWidget(self.volume_slider)
        self.volume_label = QLabel("70%")
        volume_layout.addWidget(self.volume_label)
        layout.addLayout(volume_layout)
        
        # 状态标签
        self.status_label = QLabel("就绪")
        layout.addWidget(self.status_label)
    
    def init_audio_player(self):
        """初始化音频播放器"""
        self.audio_player = AudioPlayer()
        self.audio_player.position_changed.connect(self.update_progress)
        self.audio_player.duration_changed.connect(self.set_progress_range)
        self.audio_player.state_changed.connect(self.update_status)
    
    def init_tts_worker(self):
        """初始化TTS工作线程"""
        self.tts_thread = QThread()
        self.tts_worker = TTSWorker()
        self.tts_worker.moveToThread(self.tts_thread)
        
        self.tts_worker.finished.connect(self.on_audio_generated)
        self.tts_worker.error.connect(self.on_generation_error)
        self.tts_thread.started.connect(self.tts_worker.generate_audio)
        
    def populate_audio_devices(self):
        """填充音频输出设备列表"""
        devices = QMediaDevices.audioOutputs()
        self.audio_devices = devices
        
        for device in devices:
            self.device_combo.addItem(device.description())
        
        # 设置默认设备为当前项
        default_device = QMediaDevices.defaultAudioOutput()
        if default_device:
            for i, device in enumerate(devices):
                if device.id() == default_device.id():
                    self.device_combo.setCurrentIndex(i)
                    break
    
    def change_output_device(self, index):
        """更改音频输出设备"""
        if hasattr(self, 'audio_devices') and index < len(self.audio_devices):
            device = self.audio_devices[index]
            self.audio_player.set_output_device(device)
            self.status_label.setText(f"已切换到设备: {device.description()}")
        
    def generate_audio(self):
        """生成语音"""
        text = self.text_edit.toPlainText().strip()
        if not text:
            self.status_label.setText("请输入文本")
            return
        
        # 分割文本
        text_lines = [line.strip() for line in text.split('\n') if line.strip()]
        voice = self.voice_combo.currentText()
        
        # 设置参数并开始生成
        self.tts_worker.set_params(text_lines, voice)
        self.generate_btn.setEnabled(False)
        self.status_label.setText("正在生成语音...")
        
        if not self.tts_thread.isRunning():
            self.tts_thread.start()
        else:
            self.tts_worker.generate_audio()
    
    def on_audio_generated(self, audio_data):
        """音频生成完成"""
        self.current_audio_data = audio_data
        self.audio_player.load_audio_data(audio_data)
        
        self.generate_btn.setEnabled(True)
        self.play_btn.setEnabled(True)
        self.stop_btn.setEnabled(True)
        self.progress_bar.setEnabled(True)
        
        self.status_label.setText("语音生成完成，可以播放")
    
    def on_generation_error(self, error):
        """音频生成出错"""
        self.generate_btn.setEnabled(True)
        self.status_label.setText(f"生成出错: {error}")
    
    def play_audio(self):
        """开始播放"""
        if self.current_audio_data:
            self.audio_player.play()
            self.play_btn.setEnabled(False)
            self.pause_btn.setEnabled(True)
            self.resume_btn.setEnabled(False)
    
    def pause_audio(self):
        """暂停播放"""
        self.audio_player.pause()
        self.play_btn.setEnabled(False)
        self.pause_btn.setEnabled(False)
        self.resume_btn.setEnabled(True)
    
    def resume_audio(self):
        """继续播放"""
        self.audio_player.play()
        self.play_btn.setEnabled(False)
        self.pause_btn.setEnabled(True)
        self.resume_btn.setEnabled(False)
    
    def stop_audio(self):
        """停止播放"""
        self.audio_player.stop()
        self.play_btn.setEnabled(True)
        self.pause_btn.setEnabled(False)
        self.resume_btn.setEnabled(False)
        self.progress_bar.setValue(0)
    
    def set_volume(self, volume):
        """设置音量"""
        self.audio_player.set_volume(volume)
        self.volume_label.setText(f"{volume}%")
    
    def update_progress(self, position):
        """更新进度条"""
        self.progress_bar.setValue(position)
    
    def set_progress_range(self, duration):
        """设置进度条范围"""
        self.progress_bar.setRange(0, duration)
    
    def update_status(self, status):
        """更新状态"""
        self.status_label.setText(status)
    
    def closeEvent(self, event):
        """关闭事件"""
        if self.tts_thread.isRunning():
            self.tts_thread.quit()
            self.tts_thread.wait()
        event.accept()

def main():
    app = QApplication(sys.argv)
    
    window = TTSPlayerWindow()
    window.show()
    
    sys.exit(app.exec())

if __name__ == "__main__":
    main()