import pandas as pd
import pickle
import base64

def save_vars(filename: str, **kwargs):
    """
    将多个变量存储到 parquet 文件
    :param filename: 输出文件名
    :param kwargs: 要保存的变量，按变量名传入
    """
    rows = []
    for name, value in kwargs.items():
        # 用 pickle 序列化后 base64 存储
        pickled = base64.b64encode(pickle.dumps(value)).decode("utf-8")
        rows.append({"varname": name, "value": pickled})
    df = pd.DataFrame(rows)
    df.to_parquet(filename, index=False)

def load_vars(filename: str) -> dict:
    """
    从 parquet 文件中恢复变量字典
    """
    df = pd.read_parquet(filename)
    result = {}
    for _, row in df.iterrows():
        value = pickle.loads(base64.b64decode(row["value"]))
        result[row["varname"]] = value
    return result


