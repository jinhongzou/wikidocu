"""
Configuration for Podcast-LLM Frontend

This module provides configuration settings for the Podcast-LLM frontend.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# 加载 .env 文件
load_dotenv()

# Configuration paths
PACKAGE_ROOT = Path(__file__).parent.parent
DEFAULT_CONFIG_PATH = os.path.join(PACKAGE_ROOT, 'podcast_llm', 'config', 'config.yaml')

# Default values
DEFAULT_FAST_LLM_URL =  os.getenv("FAST_LLM_BASE_URL", "https://dashscope.aliyuncs.com/compatible-mode/v1")
DEFAULT_LONG_CONTEXT_LLM_URL =  os.getenv("LONGCONTEXT_LLM_BASE_URL", "https://dashscope.aliyuncs.com/compatible-mode/v1")
DEFAULT_TEXT_OUTPUT = "episode.md"
DEFAULT_AUDIO_OUTPUT = "episode.mp3"
DEFAULT_SOURCE_URL = "https://finance.sina.com.cn/wm/2024-02-03/doc-inaftiir0348604.shtml"
