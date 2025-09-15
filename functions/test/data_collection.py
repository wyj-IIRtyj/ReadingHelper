import pyperclip

def get_selected_text():
    """
    获取当前剪贴板中的文字内容，通常用于获取当前选中的文本。
    """
    return pyperclip.paste()

if __name__ == "__main__":
    selected_text = get_selected_text()
    print("当前选取的文字内容：")
    print(selected_text)