import subprocess
import time
import pyperclip
import re

def datafilter(text: str) -> str:
    """
    过滤输入文本，去掉末尾的来源、版权说明等杂项。
    按用户逻辑处理首尾引号：
    - 除开头引号外，如果第一个引号是右引号，则保留开头引号，否则去除。
    - 除最后一个引号外，如果最后一个引号是左引号，则保留最后一个引号，否则去除。
    """
    # 1. 按行切分，去掉空行和多余空格
    lines = [line.strip() for line in text.splitlines() if line.strip()]

    # 2. 过滤掉典型的来源/版权信息
    filtered_lines = []
    for line in lines:
        if re.search(r"(摘录来自|版权保护|Scientific American|All rights reserved)", line, re.I):
            continue
        filtered_lines.append(line)

    # 3. 合并为段落
    result = " ".join(filtered_lines)
    result = re.sub(r"\s+", " ", result).strip()

    if not result:
        return result

    # ---- 处理开头引号 ----
    if result[0] in ['“', '"']:
        # 找出除开头以外的第一个引号
        rest = result[1:]
        for ch in rest:
            if ch in ['“', '”', '"']:
                if ch in ['”', '"']:  # 第一个是右引号 => 保留开头引号
                    break
                else:  # 第一个是左引号 => 去掉开头引号
                    result = result[1:].lstrip()
                break

    # ---- 处理结尾引号 ----
    if result and result[-1] in ['”', '"']:
        rest = result[:-1]
        for ch in reversed(rest):
            if ch in ['“', '”', '"']:
                if ch in ['“', '"']:  # 最后一个是左引号 => 保留尾引号
                    break
                else:  # 最后一个是右引号 => 去掉尾引号
                    result = result[:-1].rstrip()
                break

    return result

def get_selected_text_with_clipboard_deprecated():
    original_clipboard = pyperclip.paste()
    applescript_copy = '''
    tell application "System Events"
        keystroke "c" using {command down}
    end tell
    '''
    subprocess.run(['osascript', '-e', applescript_copy])
    selected_text = pyperclip.paste()
    pyperclip.copy(original_clipboard)

    if "摘录来自" in selected_text: 
        selected_text = datafilter(selected_text)
        
    return selected_text

def get_selected_text_with_clipboard():
    original_clipboard = pyperclip.paste()

    if "摘录来自" in original_clipboard: 
        selected_text = datafilter(original_clipboard)
    else: 
        selected_text = original_clipboard
        
    return selected_text
    
