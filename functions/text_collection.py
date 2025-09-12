import subprocess
import time
import pyperclip

def get_selected_text_with_clipboard():
    original_clipboard = pyperclip.paste()
    applescript_copy = '''
    tell application "System Events"
        keystroke "c" using {command down}
    end tell
    '''
    subprocess.run(['osascript', '-e', applescript_copy])
    time.sleep(0.2)  
    selected_text = pyperclip.paste()
    pyperclip.copy(original_clipboard)
    return selected_text

