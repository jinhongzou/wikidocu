# 新增一个类似process_line_dashscope的tts函数，函数参考：
from pathlib import Path
from openai import OpenAI
from playsound import playsound
from pydub import AudioSegment
from pydub.playback import play

speech_file_path = Path(__file__).parent / "siliconcloud-generated-speech.mp3"

client = OpenAI(
    api_key="sk-xxx", # 从 https://cloud.siliconflow.cn/account/ak 获取
    base_url="https://api.siliconflow.cn/v1"
)

with client.audio.speech.with_streaming_response.create(
  model="FunAudioLLM/CosyVoice2-0.5B", # 支持 fishaudio / GPT-SoVITS / CosyVoice2-0.5B 系列模型
  voice="FunAudioLLM/CosyVoice2-0.5B:alex", # 系统预置音色
  # 用户输入信息
  input="你能用高兴的情感说吗？<|endofprompt|>今天真是太开心了，马上要放假了！I'm so happy, Spring Festival is coming!",
  response_format="mp3" # 支持 mp3, wav, pcm, opus 格式
) as response:
    response.stream_to_file(speech_file_path)

# 播放生成的语音
#playsound(speech_file_path)

# 播放
audio = AudioSegment.from_mp3(speech_file_path)
play(audio)