
API_KEY = "sk-8wrV0iue1gRXadSaCLZFGEROwv6VOblPVOLx3psnrUid6ZUo"
from openai import OpenAI
import requests


client = OpenAI(
    # defaults to os.environ.get("OPENAI_API_KEY")
    api_key=API_KEY,
    base_url="https://api.chatanywhere.tech/v1"
)

# 非流式响应
def gpt_35_api(messages: list):
    """为提供的对话消息创建新的回答

    Args:
        messages (list): 完整的对话消息
    """
    completion = client.chat.completions.create(model="gpt-3.5-turbo", messages=messages)
    print(completion.choices[0].message.content)

def gpt_35_api_stream(messages: list):
    """为提供的对话消息创建新的回答 (流式传输)

    Args:
        messages (list): 完整的对话消息
    """
    stream = client.chat.completions.create(
        model='gpt-3.5-turbo',
        messages=messages,
        stream=True,
    )
    return stream

def get_translated_text_stream(text):
    messages = [
    {
        "role": "system",
        "content": (
            "你是一个专业翻译助手，将接下来的英文内容翻译为简体中文。"
            "要求如下：\n"
            "1. 保留英文专有名词、人名或无法自然翻译的英文词汇。\n"
            "2. 翻译内容要准确、自然流畅，符合中文表达习惯。\n"
            "3. 保留原文意思，不添加额外信息，也不要过度意译。\n"
            "请直接输出翻译结果。"
        )
    },
    {
        "role": "user",
        "content": text
    }
    ]
    stream = gpt_35_api_stream(messages)
    for chunk in stream:
        if chunk.choices and chunk.choices[0].delta.content:
            yield chunk.choices[0].delta.content
    

def get_translated_text(text):
    messages = [
    {
        "role": "system",
        "content": (
            "你是一个专业翻译助手，将接下来的英文内容翻译为简体中文。"
            "要求如下：\n"
            "1. 保留英文专有名词、人名或无法自然翻译的英文词汇。\n"
            "2. 翻译内容要准确、自然流畅，符合中文表达习惯。\n"
            "3. 保留原文意思，不添加额外信息，也不要过度意译。\n"
            "请直接输出翻译结果。"
        )
    },
    {
        "role": "user",
        "content": text
    }
    ]
    return gpt_35_api(messages)

def get_definition(word: str):
    """
    查询单词释义
    :param word: 英文单词
    :return: 返回 json 数据或 None
    """
    url = f"https://api.dictionaryapi.dev/api/v2/entries/en/{word}"
    try:
        response = requests.get(url, timeout=5)
        response.raise_for_status()  # 检查请求是否成功
        return response.json()[0]
    except requests.exceptions.RequestException as e:
        print(f"请求出错: {e}")
        return None

#