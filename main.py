from ui.custom_widgets import BlurWindow, BottomBar, NormalButton, ContentBlock, SplitLine, ContentLabel
from functions.text_collection import get_selected_text_with_clipboard


import sys
import time
import threading
from PySide6.QtWidgets import QApplication, QVBoxLayout, QScrollArea, QWidget
from PySide6.QtCore import Qt

class MainWindow(BlurWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Reading Helper")


        self.text_history = []
        self.current_text = ""
        self.confirmed = False
        threading.Thread(target=self.listening_text, daemon=True).start()

    def sync_selected(self, text, operation="add"):
        deprecated_select_funcs = []
        deprecated_remove_funcs = []
        if operation == "add":
            print(f"Global Adding text: {text}")
            if text not in self.global_selected_texts:
                self.global_selected_texts.append(text)
            for func in self.add_selected_text_funcs:
                try:
                    func(text, need_emit=False)
                except Exception as e: 
                    print(f"Error in add_selected_text_funcs: {e}")
                    deprecated_select_funcs.append(func)
        elif operation == "remove":
            print(f"Global Removing text: {text}")
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
                    self.addContentBlockSignal.emit(self.current_text, "Translating...", self.sync_selected)
                    self.confirmed = False
                    


if __name__ == "__main__":
    
    app = QApplication(sys.argv)
    w = MainWindow()
    w.resize(400, 700)
    w.show()
    sys.exit(app.exec())