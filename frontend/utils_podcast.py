"""
Utility functions for Podcast-LLM Frontend

This module provides utility functions for the Podcast-LLM frontend.
"""

import tempfile
import shutil
from shiny.types import FileInfo

def save_uploaded_file(file_info: FileInfo) -> str:
    """
    Save an uploaded file to a temporary location and return the path.
    
    Args:
        file_info: FileInfo object from Shiny
        
    Returns:
        str: Path to the temporary file
    """
    temp_path = tempfile.NamedTemporaryFile(delete=False).name
    shutil.copy(file_info['datapath'], temp_path)
    return temp_path

def process_source_urls(source_urls_text: str) -> list:
    """
    Process source URLs text and return a list of valid URLs.
    
    Args:
        source_urls_text: Text containing URLs separated by newlines
        
    Returns:
        list: List of valid URLs
    """
    if not source_urls_text or not source_urls_text.strip():
        return []
        
    urls = [
        url.strip() 
        for url in source_urls_text.strip().split('\n') 
        if url.strip() and url.strip().startswith(('http://', 'https://'))
    ]
    return urls

import re
from pathlib import Path

class AudioFilenameValidator:
    """音频文件名校验器"""
    
    def __init__(self):
        self.valid_extensions = {'.mp3', '.wav', '.flac', '.m4a', '.aac', '.ogg'}
        self.reserved_names = self._get_reserved_names()
    
    def _get_reserved_names(self):
        """获取系统保留文件名"""
        reserved = {'CON', 'PRN', 'AUX', 'NUL'}
        reserved.update([f'COM{i}' for i in range(1, 10)])
        reserved.update([f'LPT{i}' for i in range(1, 10)])
        return reserved
    
    def validate(self, filename):
        """
        校验音频文件名
        返回: (is_valid, error_message)
        """
        if not filename or not filename.strip():
            return False, "音频文件名不能为空"
        
        filename = filename.strip()
        
        # 长度检查
        if len(filename) > 255:
            return False, "音频文件名过长（最多255字符）"
        
        # 非法字符检查
        if re.search(r'[<>:"/\\|?*\x00-\x1f]', filename):
            return False, "音频文件名包含非法字符: <>:\"/\\|?*"
        
        # 结尾字符检查
        if filename.endswith('.') or filename.endswith(' '):
            return False, "音频文件名不能以点或空格结尾"
        
        # 扩展名检查
        ext = Path(filename).suffix.lower()
        if not ext:
            return False, "音频文件必须包含扩展名"
        if ext not in self.valid_extensions:
            return False, f"不支持的音频格式，支持: {', '.join(sorted(self.valid_extensions))}"
        
        # 保留名检查
        name_without_ext = Path(filename).stem.upper()
        if name_without_ext in self.reserved_names:
            return False, "音频文件名与系统保留名冲突"
        
        return True, "音频文件名有效"

class TextFilenameValidator:
    """文本文件名校验器"""
    
    def __init__(self):
        self.valid_extensions = {'.md', '.txt'}
        self.reserved_names = self._get_reserved_names()
    
    def _get_reserved_names(self):
        """获取系统保留文件名"""
        reserved = {'CON', 'PRN', 'AUX', 'NUL'}
        reserved.update([f'COM{i}' for i in range(1, 10)])
        reserved.update([f'LPT{i}' for i in range(1, 10)])
        return reserved
    
    def validate(self, filename):
        """
        校验文本文件名
        返回: (is_valid, error_message)
        """
        if not filename or not filename.strip():
            return False, "文本文件名不能为空"
        
        filename = filename.strip()
        
        # 长度检查
        if len(filename) > 255:
            return False, "文本文件名过长（最多255字符）"
        
        # 非法字符检查
        if re.search(r'[<>:"/\\|?*\x00-\x1f]', filename):
            return False, "文本文件名包含非法字符: <>:\"/\\|?*"
        
        # 结尾字符检查
        if filename.endswith('.') or filename.endswith(' '):
            return False, "文本文件名不能以点或空格结尾"
        
        # 扩展名检查
        ext = Path(filename).suffix.lower()
        if not ext:
            return False, "文本文件必须包含扩展名"
        if ext not in self.valid_extensions:
            return False, f"不支持的文本格式，支持: {', '.join(sorted(self.valid_extensions))}"
        
        # 保留名检查
        name_without_ext = Path(filename).stem.upper()
        if name_without_ext in self.reserved_names:
            return False, "文本文件名与系统保留名冲突"
        
        return True, "文本文件名有效"

# 使用示例
# def validate_filenames(audio_filename, text_filename):
#     """同时校验音频和文本文件名"""
#     audio_validator = AudioFilenameValidator()
#     text_validator = TextFilenameValidator()
    
#     # 校验音频文件名
#     audio_valid, audio_error = audio_validator.validate(audio_filename)
#     if not audio_valid:
#         return False, f"音频文件: {audio_error}"
    
#     # 校验文本文件名
#     text_valid, text_error = text_validator.validate(text_filename)
#     if not text_valid:
#         return False, f"文本文件: {text_error}"
    
#     return True, "所有文件名校验通过"

# # 在UI中使用
# def setup_validators():
#     """创建校验器实例"""
#     return {
#         'audio': AudioFilenameValidator(),
#         'text': TextFilenameValidator()
#     }

# # 使用示例
# validators = setup_validators()

# # 校验音频文件名
# audio_valid, audio_msg = validators['audio'].validate("episode01.mp3")
# print(f"音频校验: {audio_msg}")

# # 校验文本文件名
# text_valid, text_msg = validators['text'].validate("transcript.md")
# print(f"文本校验: {text_msg}")

def validate_inputs(topic: str, text_output: str, audio_output: str, mode: str, source_files=None, source_urls=None):
    """
    Validate user inputs.
    
    Args:
        topic: Podcast topic
        text_output: Text output file name
        audio_output: Audio output file name
        mode: Operation mode
        source_files: Source files (optional)
        source_urls: Source URLs text (optional)
        
    Returns:
        tuple: (is_valid, error_message)
    """
    # Validate required inputs
    if not topic or not topic.strip():
        return False, "Podcast topic cannot be empty."

    # text_output
    if not text_output or not text_output.strip():
        return False, "Text output path cannot be empty."
    
    else:
        audio_valid, audio_error =  TextFilenameValidator().validate(text_output)
        if not audio_valid: return audio_valid, audio_error
        audio_valid, audio_error =  TextFilenameValidator().validate(text_output.strip())
        if not audio_valid: return audio_valid, audio_error

    # audio_output
    if audio_output.strip():
        audio_valid, audio_error =  AudioFilenameValidator().validate(audio_output.strip())
        if not audio_valid: return audio_valid, audio_error

    # For context mode, validate that either source files or URLs are provided
    if mode == "context":
        source_files_provided = source_files is not None and len(source_files) > 0
        source_urls_provided = source_urls is not None and source_urls.strip() and any(
            url.strip() for url in source_urls.strip().split('\n') if url.strip()
        )
        
        if not source_files_provided and not source_urls_provided:
            return False, "For context mode, either source files or source URLs must be provided."
            
    return True, None