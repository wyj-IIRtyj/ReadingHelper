from ui.custom_widgets import BlurWindow, BottomBar, NormalButton, ContentBlock, SplitLine, ContentLabel, VocabularyCard
from functions.text_collection import get_selected_text_with_clipboard
from functions.translate_generation import get_translated_text_stream, get_definition
from functions.audio_generation import AudioPlayer, TTSWorker

import sys
import time
import threading
from PySide6.QtWidgets import QApplication, QVBoxLayout, QScrollArea, QWidget
from PySide6.QtCore import Qt, QThread, QTimer, Signal

class MainWindow(BlurWindow):
    SetCardDataSignal = Signal(dict)

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Reading Helper")

        self.current_text = ""
        self.confirmed = False
        self.read_the_newest_block = False
        self.get_definition_func = get_definition


        self.block_playlist = []
        self.init_audio_player()
        self.init_tts_worker()
        
        # 音频数据
        self.current_audio_data = None

        # 绑定BottomBar按钮功能

        # 设置按钮功能
        def start_read(): 
            self.read_the_newest_block = True
            self.start_read_sequence()
            self.bottom_bar.read_all_button.start_hide_animation()
            QTimer.singleShot(50, lambda: self.bottom_bar.stop_button.start_show_animation())
            QTimer.singleShot(50, lambda: self.bottom_bar.cancel_button.start_show_animation())


        def stop_read():
            self.read_the_newest_block = False
            self.pause_read_sequence()
            self.bottom_bar.stop_button.start_hide_animation()
            QTimer.singleShot(100, lambda: self.bottom_bar.continue_button.start_show_animation())

        def cancel_read():
            self.read_the_newest_block = False
            self.stop_read_sequence()
            self.bottom_bar.stop_button.start_hide_animation()
            self.bottom_bar.cancel_button.start_hide_animation()
            self.bottom_bar.continue_button.start_hide_animation()
            QTimer.singleShot(350, lambda: self.bottom_bar.read_all_button.start_show_animation())

        def continue_read():
            self.read_the_newest_block = True
            self.continue_read_sequence()
            self.bottom_bar.continue_button.start_hide_animation()
            QTimer.singleShot(50, lambda: self.bottom_bar.stop_button.start_show_animation())

        def clear_content():
            blocks = [*self.content_blocks]
            for block in blocks: 
                block._start_close_animation()
            pass

        self.bottom_bar.read_all_button.clicked.connect(start_read)
        self.bottom_bar.stop_button.clicked.connect(stop_read)
        self.bottom_bar.cancel_button.clicked.connect(cancel_read)
        self.bottom_bar.continue_button.clicked.connect(continue_read)
        self.bottom_bar.clear_button.clicked.connect(clear_content)
        self.SetCardDataSignal.connect(self.set_card_data)

        self.loading_word = None

        threading.Thread(target=self.listening_text, daemon=True).start()
    
    # 音频播放器初始化
    def init_audio_player(self):
        """初始化音频播放器"""
        self.audio_player = AudioPlayer()
        self.audio_player.state_changed.connect(self.update_status)
        self.audio_player.error_occurred.connect(self.on_player_error)  # 添加错误处理
    
    def init_tts_worker(self):
        """初始化TTS工作线程"""
        self.tts_thread = QThread()
        self.tts_worker = TTSWorker()
        self.tts_worker.moveToThread(self.tts_thread)
        
        self.tts_worker.finished.connect(self.on_audio_generated)
        self.tts_worker.error.connect(self.on_generation_error)
        self.tts_thread.started.connect(self.tts_worker.generate_audio)
    
    # 音频数据准备
    def generate_audio(self, text, ContentBlock=None):
        """生成音频"""
        if ContentBlock: 
            ContentBlock.set_breath_mode("loading")
            ContentBlock.start_breathing(first_cycle=True)

        text_lines = [line.strip() for line in text.split('\n') if line.strip()]
        # 重置TTS线程
        if self.tts_thread.isRunning():
            self.tts_thread.quit()
            self.tts_thread.wait()
        # 设置参数并开始生成
        self.tts_worker.set_params(text_lines, ContentBlock)
        self.tts_thread.start()

        self.audio_datas[ContentBlock] = b''
    
    def on_audio_generated(self, audio_data, ContentBlock=None):
        """音频生成完成"""
        print(f"Audio data is ready. For text content:{ContentBlock.labels[0].text}")
        self.current_audio_data = audio_data
        self.audio_player.stop()
        self.audio_player.load_audio_data(audio_data)

        if ContentBlock:
            ContentBlock.stop_breathing()
            ContentBlock.set_breath_mode("playing")
            QTimer.singleShot(300, lambda: ContentBlock.start_breathing(first_cycle=True))
            if ContentBlock in self.content_blocks:
                self.audio_datas[ContentBlock] = audio_data
        
        
        # self.status_label.setText(f"语音生成完成，音频大小: {len(audio_data)} 字节")
        
        # 停止线程
        if self.tts_thread.isRunning():
            self.tts_thread.quit()
        
        self.play_audio()
    
    def on_generation_error(self, error, ContentBlock=None):
        """音频生成出错"""
        pass
        if ContentBlock: 
            ContentBlock.stop_breathing()
            if ContentBlock in self.audio_datas: 
                if self.audio_datas[ContentBlock] == b'':
                    del self.audio_datas[ContentBlock]
        
        # 停止线程
        if self.tts_thread.isRunning():
            self.tts_thread.quit()
    
    def on_player_error(self, error):
        """播放器错误处理"""
        pass
    
    # 音频播放相关操作处理

    def play_audio(self):
        """开始播放"""
        if self.current_audio_data:
            self.audio_player.play()
    
    def pause_audio(self):
        """暂停播放"""
        self.audio_player.pause()
        if len(self.block_playlist):
            self.block_playlist[0].stop_breathing()
    
    def resume_audio(self):
        """继续播放"""
        self.audio_player.play()
        if len(self.block_playlist):
            self.block_playlist[0].start_breathing(first_cycle=True)
    
    def stop_audio(self):
        """停止播放"""
        self.audio_player.stop()
        if len(self.block_playlist):
            self.block_playlist[0].stop_breathing()

    def update_status(self, status, start_playlist=False):
        """更新状态"""
        
        # 播放结束时重置按钮状态
        if status == "停止":
            if len(self.block_playlist) and not start_playlist: 
                finished_block = self.block_playlist.pop(0)
                finished_block.stop_breathing()
            if len(self.block_playlist):
                block = self.block_playlist[0] 
                if block in self.audio_datas: 
                    QTimer.singleShot(200, lambda: self.on_audio_generated(self.audio_datas[block], block))
                
                else: 

                    self.generate_audio(block.labels[0].text, block)


    # 朗读全部文本
    def start_read_sequence(self): 
        self.block_playlist = [*self.content_blocks]
        self.update_status("停止", True)

    def pause_read_sequence(self): 
        self.pause_audio()

    def continue_read_sequence(self): 
        self.resume_audio()

    def stop_read_sequence(self): 
        self.stop_audio()
        self.block_playlist = [] 
    
    def read_new_block(self):
        if not len(self.content_blocks):
            self.block_playlist.append(self.content_blocks[-1])
            self.update_status("停止", True)
        else: 
            self.block_playlist.append(self.content_blocks[-1])
        
        

    def set_card_data(self, data):
        # 设置内容
        self.card._setup_content(data)
        
    def load_card_data(self, word): 
        data = {} 
        try:
            data = self.get_definition_func(word)
        except:
            pass 

        if self.loading_word == word:
            self.SetCardDataSignal.emit(data)

    # 激活词卡
    def activate_vocabulary_card(self, word): 
        threading.Thread(target=self.load_card_data, args=[word]).start()
        self.loading_word = word
        self.card = VocabularyCard(word)
        self.card.setWindowFlag(Qt.Window) 
        self.card.setGeometry(self.geometry().left() - 400, self.geometry().top(), 400, 0)
        self.card.show()

    # 全局同步选词
    def sync_selected(self, text, operation="add"):
        deprecated_select_funcs = []
        deprecated_remove_funcs = []
        if operation == "add":
            if text not in self.global_selected_texts:
                self.global_selected_texts.append(text)
                self.activate_vocabulary_card(text)
            for func in self.add_selected_text_funcs:
                try:
                    func(text, need_emit=False)
                except Exception as e: 
                    print(f"Error in add_selected_text_funcs: {e}")
                    deprecated_select_funcs.append(func)
        elif operation == "remove":
            if text in self.global_selected_texts:
                self.global_selected_texts.remove(text)
            for func in self.remove_selected_text_funcs:
                try:
                    func(text)
                except Exception as e: 
                    print(f"Error in remove_selected_text_funcs: {e}")
                    deprecated_remove_funcs.append(func)

        for func in deprecated_select_funcs:
            self.add_selected_text_funcs.remove(func)
        for func in deprecated_remove_funcs:
            self.remove_selected_text_funcs.remove(func)
        
    # 实时剪切板获取
    def listening_text(self):
        while True:
            time.sleep(0.3)
            selected_text = get_selected_text_with_clipboard()
            if selected_text and selected_text not in self.text_history:
                if selected_text != self.current_text:
                    if not self.confirmed: 
                        self.confirmed = True 
                        continue

                    self.current_text = selected_text
                    self.text_history.append(selected_text)
                    self.addContentBlockSignal.emit(self.current_text, (get_translated_text_stream, self.current_text), self.sync_selected)
                    self.confirmed = False
                    
    def closeEvent(self, event):
        """关闭事件"""
        # 停止播放
        self.audio_player.stop()
        
        # 清理TTS线程
        if self.tts_thread.isRunning():
            self.tts_thread.quit()
            self.tts_thread.wait()
        
        # 清理音频缓冲区
        if hasattr(self.audio_player, 'buffer') and self.audio_player.buffer:
            self.audio_player.buffer.close()
        
        event.accept()

if __name__ == "__main__":
    
    app = QApplication(sys.argv)
    w = MainWindow()
    w.resize(400, 700)
    w.show()
    sys.exit(app.exec())