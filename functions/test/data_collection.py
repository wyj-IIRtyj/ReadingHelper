import requests

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
