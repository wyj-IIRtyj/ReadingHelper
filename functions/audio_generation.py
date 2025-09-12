
import edge_tts
import asyncio
from edge_tts import VoicesManager

valid_locales = ['zh-HK', 'zh-CN', 'zh-CN-liaoning', 'zh-TW', 'zh-CN-shaanxi', 'en-AU', 'en-CA', 'en-HK', 'en-IN', 'en-IE', 'en-KE', 'en-NZ', 'en-NG', 'en-PH', 'en-SG', 'en-US', 'en-ZA', 'en-TZ', 'en-GB']
valid_gender = ["Male", "Female"]

async def generate(text: str, voice: str = "en-GB-RyanNeural") -> bytes:
    """生成音频并返回音频流数据"""
    communicate = edge_tts.Communicate(text, voice, rate='-15%')
    audio_data = b""  # 用于存储生成的音频数据

    # 异步生成音频数据块
    async for chunk in communicate.stream():
        if chunk["type"] == "audio":
            audio_chunk_data = chunk.get("data")
            if audio_chunk_data is not None:
                audio_data += audio_chunk_data

    return audio_data

async def get_voice_names(gender="Male", locale="es"): 
    if gender not in valid_gender + ['-1'] or locale not in valid_locales:
        return []
    voices = await VoicesManager.create()
    if gender == "-1":
        voice = voices.find(Locale=locale)
    else:
        # Ensure gender is exactly 'Male' or 'Female'
        gender_literal = "Male" if gender == "Male" else "Female"
        voice = voices.find(Gender=gender_literal, Locale=locale)
    result = []
    for v in voice: 
        result.append(v["ShortName"])
    return result
import wave

def append_silence(audio_data: bytes, silence_duration: float, sample_rate: int, sample_width: int, num_channels: int) -> bytes:
    """
    在给定的音频二进制数据末尾添加指定时长的静音，并返回新的二进制数据。
    
    :param audio_data: 原始音频的 PCM 二进制数据
    :param silence_duration: 需要插入的静音时长（秒）
    :param sample_rate: 采样率（Hz，例如 44100）
    :param sample_width: 采样深度（字节，例如 2 表示 16-bit）
    :param num_channels: 通道数（1 = 单声道, 2 = 立体声）
    :return: 处理后的二进制数据
    """
    # 计算需要插入的静音字节数
    silence_frames = int(sample_rate * silence_duration)  # 计算静音的帧数
    silence_bytes = silence_frames * sample_width * num_channels  # 计算静音的字节数
    silence_data = b'\x00' * silence_bytes  # 生成静音数据
    
    # 拼接原始数据和静音数据
    return audio_data + silence_data

def get_audio_data(txtdata): 

    sample_rate = 24000   
    sample_width = 2      # 16-bit = 2 字节
    num_channels = 1      # 单声道

    data = b''
    for i in range(len(txtdata)):

        while True:
            try:
                voicedata = asyncio.run(generate(txtdata[i]))
                data += voicedata

                data = append_silence(data, 5, sample_rate, sample_width, num_channels)
                break
            except:
                pass
    return data
