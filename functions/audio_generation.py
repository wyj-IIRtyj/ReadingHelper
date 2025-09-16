from PySide6.QtCore import QTimer, Signal, QObject
from PySide6.QtMultimedia import QMediaDevices, QAudio
from PySide6.QtCore import QByteArray, QIODevice, QBuffer
from PySide6.QtCore import QObject, Signal, QBuffer, QByteArray, QIODevice, QTimer
from PySide6.QtMultimedia import QAudioFormat, QAudioSink, QMediaDevices

import asyncio
import traceback
import edge_tts
import tempfile
import os

import numpy as np
import soundfile as sf
HAS_SOUNDFILE = True


class AudioConverter:
    """音频格式转换工具类"""
    
    @staticmethod
    def mp3_to_pcm_soundfile(mp3_data: bytes, target_sample_rate: int = 48000, target_channels: int = 2) -> bytes:
        """使用soundfile库转换MP3"""
        if not HAS_SOUNDFILE:
            raise Exception("soundfile库未安装，请执行: pip install soundfile")
            
        try:
            # 创建临时MP3文件
            with tempfile.NamedTemporaryFile(suffix='.mp3', delete=False) as temp_file:
                temp_file.write(mp3_data)
                temp_file.flush()
                temp_path = temp_file.name
            
            # 读取音频文件
            data, samplerate = sf.read(temp_path)
            
            # 转换为目标格式
            if len(data.shape) == 1:  # 单声道
                if target_channels == 2:
                    # 转为立体声
                    data = np.column_stack((data, data))
            elif data.shape[1] == 2 and target_channels == 1:  # 立体声转单声道
                data = np.mean(data, axis=1)
            
            # 重采样（简单线性插值）
            if samplerate != target_sample_rate:
                # 计算新的样本数量
                new_length = int(len(data) * target_sample_rate / samplerate)
                # 简单的线性插值重采样
                old_indices = np.linspace(0, len(data) - 1, len(data))
                new_indices = np.linspace(0, len(data) - 1, new_length)
                
                if len(data.shape) == 1:  # 单声道
                    data = np.interp(new_indices, old_indices, data)
                else:  # 多声道
                    data = np.array([np.interp(new_indices, old_indices, data[:, ch]) 
                                   for ch in range(data.shape[1])]).T
            
            # 转换为16位整数PCM
            if data.dtype != np.int16:
                data = (data * 32767).astype(np.int16)
            
            # 清理临时文件
            os.unlink(temp_path)
            
            return data.tobytes()
            
        except Exception as e:
            raise Exception(f"soundfile转换失败: {e}")
    
    @staticmethod
    def mp3_to_pcm_manual(mp3_data: bytes, target_sample_rate: int = 48000, target_channels: int = 2) -> bytes:
        """手动解码MP3（简化版本，仅适用于特定情况）"""
        try:
            # 这是一个简化的实现，实际可能需要更复杂的MP3解码
            # 对于edge-tts生成的音频，我们可以尝试直接处理
            
            # 注意：这个方法可能不适用于所有MP3文件
            # 建议优先使用ffmpeg或soundfile方法
            
            # 返回原始数据（如果无法处理）
            # 这种情况下播放器需要能够处理MP3格式
            return mp3_data
            
        except Exception as e:
            raise Exception(f"手动音频转换失败: {e}")


class TTSWorker(QObject):
    finished = Signal(bytes, object)
    error = Signal(str, object)
    
    def __init__(self):
        super().__init__()
        self.text_data = []
        self.voice = "en-GB-RyanNeural"
        self.ContentBlock = None
    
    def set_params(self, text_data, ContentBlock):
        self.text_data = text_data
        self.ContentBlock = ContentBlock
    
    async def generate_audio_async(self, text: str, voice: str = "en-GB-RyanNeural") -> bytes:
        """生成音频并返回音频流数据（返回纯 bytes）"""
        try:
            communicate = edge_tts.Communicate(text, voice, rate='-15%')
            audio_data = b""
            async for chunk in communicate.stream():
                if chunk["type"] == "audio":
                    audio_data += chunk["data"]  # 直接拼接MP3数据
            return audio_data
        except Exception as e:
            raise
    
    def generate_audio(self):
        """生成完整音频数据并转换为PCM格式"""
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            # 获取MP3数据
            mp3_data = loop.run_until_complete(
                self.generate_audio_async(" ".join(self.text_data), self.voice)
            )
            loop.close()
            
            # 获取系统默认音频格式
            default_device = QMediaDevices.defaultAudioOutput()
            preferred_format = default_device.preferredFormat()
            
            target_sample_rate = preferred_format.sampleRate() if preferred_format.sampleRate() > 0 else 48000
            target_channels = preferred_format.channelCount() if preferred_format.channelCount() > 0 else 2
            
            try:
                # 尝试使用soundfile
                pcm_data = AudioConverter.mp3_to_pcm_soundfile(
                    mp3_data, target_sample_rate, target_channels
                )
                print(f"使用soundfile转换音频: {target_sample_rate}Hz, {target_channels}声道")
            except Exception as soundfile_error:
                print(f"soundfile转换失败: {soundfile_error}")
                try:
                    # 回退到手动处理
                    pcm_data = AudioConverter.mp3_to_pcm_manual(
                        mp3_data, target_sample_rate, target_channels
                    )
                    print("使用手动方法处理音频")
                except Exception as manual_error:
                    print(f"手动转换也失败: {manual_error}")
                    # 最后回退：直接使用原始MP3数据
                    pcm_data = mp3_data
                    print("使用原始MP3数据（可能无法播放）")
            
            self.finished.emit(pcm_data, self.ContentBlock)
            
        except Exception as e:
            print(e)
            self.error.emit(str(e), self.ContentBlock)
            traceback.print_exc()


class AudioPlayer(QObject):
    """使用QAudioSink的音频播放器，支持系统混音"""
    position_changed = Signal(int)
    duration_changed = Signal(int)
    state_changed = Signal(str)
    error_occurred = Signal(str)
    
    def __init__(self):
        super().__init__()
        self.audio_sink = None
        self.buffer = None
        self.audio_data = None
        self.is_playing = False
        self.is_paused = False
        self.current_position = 0
        self.total_duration = 0
        
        # 定时器用于更新播放位置
        self.position_timer = QTimer()
        self.position_timer.timeout.connect(self._update_position)
        self.position_timer.setInterval(100)  # 每100ms更新一次

        
    def _get_audio_format(self):
        """获取系统默认音频格式"""
        default_device = QMediaDevices.defaultAudioOutput()
        preferred_format = default_device.preferredFormat()
        
        format = QAudioFormat()
        
        # 使用系统偏好格式，如果无效则使用默认值
        sample_rate = preferred_format.sampleRate() if preferred_format.sampleRate() > 0 else 48000
        channels = preferred_format.channelCount() if preferred_format.channelCount() > 0 else 2
        
        format.setSampleRate(sample_rate)
        format.setChannelCount(channels)
        format.setSampleFormat(QAudioFormat.Int16)  # 16位整数
        
        return format
    
    

    def _update_position(self):
        """更新播放位置"""
        if self.audio_sink and self.is_playing and not self.is_paused:
            # 计算播放位置（基于已处理的字节数）
            bytes_per_ms = (self.audio_format.sampleRate() * 
                          self.audio_format.channelCount() * 
                          self.audio_format.bytesPerSample()) / 1000
            
            if bytes_per_ms > 0:
                processed_bytes = self.audio_sink.bytesFree() - self.initial_buffer_size
                if processed_bytes > 0:
                    self.current_position = int(processed_bytes / bytes_per_ms)
                    self.position_changed.emit(self.current_position)
    
    def load_audio_data(self, audio_data: bytes):
        """加载PCM音频数据"""
        try:
            if self.audio_sink:
                self.audio_sink.stop()
                self.audio_sink = None
            
            if self.buffer:
                self.buffer.close()
                self.buffer = None
            
            self.audio_data = audio_data
            self.audio_format = self._get_audio_format()
            
            # 计算音频时长
            bytes_per_second = (self.audio_format.sampleRate() * 
                              self.audio_format.channelCount() * 
                              self.audio_format.bytesPerSample())
            self.total_duration = int((len(audio_data) / bytes_per_second) * 1000)  # 毫秒
            self.duration_changed.emit(self.total_duration)
            print(self.total_duration)
            
            # 创建缓冲区
            self.buffer = QBuffer()
            self.buffer.setData(QByteArray(audio_data))
            
            # 创建音频输出设备
            default_device = QMediaDevices.defaultAudioOutput()
            self.audio_sink = QAudioSink(default_device, self.audio_format)

            self.audio_sink.stateChanged.connect(self._on_state_changed)
            
            # 检查格式是否支持
            if not default_device.isFormatSupported(self.audio_format):
                self.error_occurred.emit("音频格式不被系统支持")
                return
                
            self.current_position = 0
            self.is_playing = False
            self.is_paused = False
            self.state_changed.emit("准备就绪")
            
        except Exception as e:
            print(f"加载音频数据出错: {e}")
            self.error_occurred.emit(f"加载音频数据出错: {e}")
    
    def _on_state_changed(self, state):
        if state == QAudio.IdleState:
            self.state_changed.emit("停止")
    
    def play(self):
        """开始播放"""
        try:
            if not self.buffer or not self.audio_sink:
                self.error_occurred.emit("音频未准备就绪")
                return
            
            if self.is_paused:
                # 从暂停恢复
                self.audio_sink.resume()
                self.is_paused = False
            else:
                # 重新开始播放
                self.buffer.close()
                self.buffer.open(QIODevice.ReadOnly)
                self.audio_sink.start(self.buffer)
                self.initial_buffer_size = self.audio_sink.bufferSize()
            
            self.is_playing = True
            self.position_timer.start()
            self.state_changed.emit("播放中")
            
        except Exception as e:
            print(f"播放出错: {e}")
            self.error_occurred.emit(f"播放出错: {e}")
    
    def pause(self):
        """暂停播放"""
        if self.audio_sink and self.is_playing:
            self.audio_sink.suspend()
            self.is_paused = True
            self.position_timer.stop()
            self.state_changed.emit("暂停")
    
    def stop(self):
        """停止播放"""
        if self.audio_sink:
            self.audio_sink.stop()
        
        self.is_playing = False
        self.is_paused = False
        self.current_position = 0
        self.position_timer.stop()
        self.position_changed.emit(0)

    def set_position(self, position_ms):
        """设置播放位置（毫秒）"""
        if not self.buffer or not self.audio_data:
            return
        
        try:
            # 计算字节偏移量
            bytes_per_ms = (self.audio_format.sampleRate() * 
                           self.audio_format.channelCount() * 
                           self.audio_format.bytesPerSample()) / 1000
            
            byte_offset = int(position_ms * bytes_per_ms)
            
            # 确保偏移量对齐到帧边界
            frame_size = self.audio_format.channelCount() * self.audio_format.bytesPerSample()
            byte_offset = (byte_offset // frame_size) * frame_size
            
            if byte_offset < len(self.audio_data):
                was_playing = self.is_playing
                if was_playing:
                    self.stop()
                
                # 重新设置缓冲区位置
                self.buffer.close()
                self.buffer.seek(byte_offset)
                self.buffer.open(QIODevice.ReadOnly)
                
                self.current_position = position_ms
                self.position_changed.emit(self.current_position)
                
                if was_playing:
                    self.play()
                    
        except Exception as e:
            print(f"设置播放位置出错: {e}")
            self.error_occurred.emit(f"设置播放位置出错: {e}")
    
    def set_volume(self, volume):
        """设置音量 (0-100)"""
        if self.audio_sink:
            self.audio_sink.setVolume(volume / 100.0)
    
    def get_position(self):
        """获取当前播放位置（毫秒）"""
        return self.current_position
    
    def get_duration(self):
        """获取音频总时长（毫秒）"""
        return self.total_duration
