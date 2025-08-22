"""
Server Logic for Podcast-LLM

This module provides the server logic for the Podcast-LLM application using Shiny for Python.
"""

import logging
import os
import tempfile
import asyncio
import sys
from pathlib import Path
import pygame
import time
import traceback
import concurrent.futures
import threading

from shiny import App, ui, render, reactive
#from shiny.types import FileInfo
from frontend.utils_podcast import AudioFilenameValidator

logger = logging.getLogger(__name__)

# Add the parent directory to the path to import podcast_llm modules
sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    from podcast_llm.generate import generate
    MODULES_AVAILABLE = True
except ImportError:
    MODULES_AVAILABLE = False
    logger.warning("Warning: podcast_llm modules not available. Generation will not work.")
    ui.notification_show(f"⚠️ 请填写必要信息", type="error", duration=10 )

from .podcast_config import DEFAULT_CONFIG_PATH
from .utils_podcast import save_uploaded_file, process_source_urls, validate_inputs
from config.global_vars import LOG_FILE

def podcast_llm_server(input, output, session):
    #def server(input, output, session):
    # Reactive value to store log content
    log_content = reactive.Value("")
    
    # Reactive value to track if generation is in progress
    is_generating = reactive.Value(False)

    # 多媒体輸出
    audio_file_path = reactive.Value('output/episode.mp3')


    # 初始化 pygame
    pygame.init()

    # 自定义事件
    MUSIC_END_EVENT = pygame.USEREVENT + 1

    # 播放状态与事件通知（reactive 可监听）
    audio_playback_state = reactive.Value({
        'is_playing': False,
        'pygame_initialized': False,
        'playback_finished': False,   # 新增：用于通知播放结束
        'error': None                 # 新增：存储错误信息
    })

    # Create a temporary file for logging
    #temp_log_file = tempfile.NamedTemporaryFile(mode='w', delete=False).name
    temp_log_file = LOG_FILE
    # Function to update log display
    def update_log():
        try:
            with open(temp_log_file, 'r') as f:
                content = f.read()
                log_content.set(content)
        except Exception as e:
            log_content.set(f"Error reading log file: {str(e)}")
            ui.notification_show(f"⚠️ Error reading log file", type="error", duration=10 )

    # Generate podcast when button is clicked
    @reactive.effect
    @reactive.event(input.generate)
    async def generate_podcast():
        # Check if generation is already in progress
        if is_generating.get():
            with open(temp_log_file, 'a') as f:
                f.write("WARNING: Podcast generation is already in progress. Please wait for it to complete.\n")
            update_log()
            return

        # Clear previous log content
        with open(temp_log_file, 'w') as f:
            f.write("Starting podcast generation...\n")

        # Check if modules are available
        if not MODULES_AVAILABLE:
            with open(temp_log_file, 'a') as f:
                f.write("ERROR: podcast_llm modules not available. Please ensure the package is installed correctly.\n")
            update_log()
            ui.notification_show(f"⚠️ podcast_llm 模块不可用", type="error", duration=10 )

            return
        
        # Get input values
        topic = input.topic()
        mode = input.mode()
        qa_rounds = input.qa_rounds()
        use_checkpoints = input.use_checkpoints()
        language = input.language()
        fast_llm_url = input.fast_llm_url()
        long_context_llm_url = input.long_context_llm_url()
        text_output = input.text_output()
        audio_output = input.audio_output()
        source_urls = input.source_urls()
        source_files = input.source_files()
        
        # Validate inputs
        is_valid, error_message = validate_inputs(topic, text_output, audio_output, mode, source_files, source_urls)
        if not is_valid:
            with open(temp_log_file, 'a') as f:
                f.write(f"ERROR: {error_message}\n")
            update_log()
            ui.notification_show(f"⚠️ 必要信息不全: {error_message}", type="error", duration=10 )
            return
        
        # Process source files
        source_files_paths = []
        if source_files:
            for file_info in source_files:
                # Save uploaded files to temporary locations
                temp_path = save_uploaded_file(file_info)
                source_files_paths.append(temp_path)
        
        # Process custom config file
        # custom_config_path = None
        # if input.custom_config():
        #     file_info = input.custom_config()[0]  # Take the first file
        #     temp_path = save_uploaded_file(file_info)
        #     custom_config_path = temp_path
        
        # Process source URLs
        source_urls_list = process_source_urls(source_urls)

        # Combine sources properly as Optional[List[str]]
        all_sources = source_files_paths + source_urls_list
        # 如果列表为空，则设为 None 以符合 Optional[List[str]] 类型
        all_sources = all_sources if all_sources else None

        # Process output paths，输出到指定目录
        text_output_file = Path("output") / text_output.strip() if text_output.strip() else None
        audio_output_file = Path("output") / audio_output.strip() if audio_output.strip() else None
        audio_file_path.set(audio_output_file)

        # Log input values
        logging.info(f'Topic: {topic} (type: {type(topic)})')
        logging.info(f'Mode of Operation: {mode} (type: {type(mode)})')
        logging.info(f'Source Files: {source_files_paths} (type: {type(source_files_paths)})')
        logging.info(f'Source URLs: {source_urls_list} (type: {type(source_urls_list)})')
        logging.info(f'Source: {all_sources} (type: {type(all_sources)})')
        logging.info(f'QA Rounds: {qa_rounds} (type: {type(qa_rounds)})')
        logging.info(f'Use Checkpoints: {use_checkpoints} (type: {type(use_checkpoints)})')
        logging.info(f'Custom Config File: {DEFAULT_CONFIG_PATH} (type: {type(DEFAULT_CONFIG_PATH)})')
        logging.info(f'Text Output: {text_output_file} (type: {type(text_output_file)})')
        logging.info(f'Audio Output: {audio_output_file} (type: {type(audio_output_file)})')

        # Import traceback for better error reporting
        async def run_generation():
            executor = None
            try:
                # Run the generate function in a thread pool to avoid blocking
                loop = asyncio.get_event_loop()
                executor = concurrent.futures.ThreadPoolExecutor()
                
                # Create a future for the generate function
                future = loop.run_in_executor(
                    executor,
                    lambda: generate(
                        topic=topic.strip() if topic else "",
                        mode=mode,
                        sources=all_sources,
                        qa_rounds=qa_rounds,
                        use_checkpoints=use_checkpoints,
                        audio_output=audio_output_file,
                        text_output=text_output_file,
                        #config=custom_config_path if custom_config_path else DEFAULT_CONFIG_PATH,
                        config=DEFAULT_CONFIG_PATH,
                        debug=False,
                        log_file=temp_log_file,
                        fast_llm_base_url=fast_llm_url,
                        long_context_llm_base_url=long_context_llm_url,
                        language=language
                    )
                )

                # Wait for completion or cancellation
                        # Set generating flag to prevent duplicate clicks
                is_generating.set(True)
                ui.notification_show(f"⏳ 开始生成播客，耗时较长，请耐心等待...", type="message", duration=10 )
                await future
                ui.notification_show(f"✅ 播客生成完成，请点击播放按键播放", type="message", duration=10 )
                logging.info("Podcast generation completed!")

            except asyncio.CancelledError:
                logging.info("Podcast generation was cancelled by user.")
                ui.notification_show(f"Podcast generation was cancelled by user", type="message", duration=10 )

            except Exception as e:
                error_msg = f"Error during podcast generation: {str(e)}\n{traceback.format_exc()}"
                ui.notification_show(f"Error during podcast generation: {str(e)}", type="error", duration=10 )
                logging.error(error_msg)
            finally:
                # Reset generating flag when done
                is_generating.set(False)
                if executor:
                    executor.shutdown(wait=False)

        # Start the generation in the background
        asyncio.create_task(run_generation())
        # Update log display periodically while generation is running
        async def update_log_periodically():
            while True:
                await asyncio.sleep(1)  # Update log every second
                update_log()
                # Check if generation is still running by checking for specific log messages
                try:
                    with open(temp_log_file, 'r') as f:
                        content = f.read()
                        if "Podcast generation completed!" in content or "Error during podcast generation:" in content or "Podcast generation was cancelled by user." in content:
                            break
                except:
                    pass

        # Start periodic log updates
        asyncio.create_task(update_log_periodically())

    # 暂时下线
    # @reactive.effect
    # @reactive.event(input.stop_generation)
    # def stop_generation():
    #     # Cancel the generation task if it exists
    #     if hasattr(session, 'current_generation_task') and session.current_generation_task:
    #         session.current_generation_task.cancel()
        
    #     # Log the cancellation
    #     with open(temp_log_file, 'a') as f:
    #         f.write("\n--- STOP REQUESTED ---\n")
    #         f.write("Attempting to stop podcast generation...\n")
    #     update_log()

    @output
    @render.text
    @reactive.file_reader(temp_log_file)
    async def log_output():  # Added function declaration
        # 读取日志文件
        # 检查文件是否存在并且是一个文件
        if not os.path.exists(temp_log_file) or not os.path.isfile(temp_log_file):
            logger.warning("Log file does not exist: %s", temp_log_file)
            return "Log file not found."

        # 使用内置方法读取文本文件
        with open(temp_log_file, "r") as file:
            log_lines = file.readlines()  # 读取所有行
            return ''.join(log_lines)  # 将行合并为一个字符串返回

    # # Play or stop audio when button is clicked
    @reactive.effect
    @reactive.event(input.audio_play)
    def audio_play():

        audio_output = input.audio_output()
        if audio_output.strip() :# 非空
            # 检查音频文件名是否有效
            audio_valid, audio_error =  AudioFilenameValidator().validate(audio_output)
            if not audio_valid: 

                logger.error("%s", audio_error)
                with open(temp_log_file, 'a') as f:
                    f.write(f"{audio_error}")
                update_log()
                return 
            else:
                filename = Path("output") / audio_output.strip()
        else:
            filename = audio_file_path.get()

        state = audio_playback_state.get()

        # If already playing, stop the audio
        if state['is_playing']:
            try:
                if pygame.mixer.get_init():
                    pygame.mixer.music.stop()
                    pygame.mixer.quit()
                
                # 更新状态
                new_state = state.copy()
                new_state['is_playing'] = False
                new_state['pygame_initialized'] = False
                new_state['playback_finished'] = False  # 重置播放完成状态
                audio_playback_state.set(new_state)

                logger.info("Stopped playing audio %s", filename)
                with open(temp_log_file, 'a') as f:
                    f.write(f"\n--- Stopped playing audio {filename} ---\n")
                update_log()

                ui.update_action_button("audio_play", label="Audio Play")
                ui.notification_show("⚠️ 停止播放...", type="message", duration=10)

            except Exception as e:
                logger.error("停止音频时发生错误: %s", e)
                with open(temp_log_file, 'a') as f:
                    f.write(f"\n--- 停止音频时发生错误: {e} ---\n")
                update_log()
                ui.notification_show(f"❌ 播放音频时发生错误", type="error", duration=10)
            return

        # Start playing the audio
        try:
            if not os.path.exists(filename):
                raise FileNotFoundError(f"Audio file not found: {filename}")
            
            logger.info("Playing audio %s...", filename)
            with open(temp_log_file, 'a') as f:
                f.write(f"\n--- Playing audio {filename} ---\n")
            update_log()

            ui.notification_show("⏳ 准备播放中...", type="message", duration=10)

            # Initialize mixer
            if not pygame.mixer.get_init():
                try:
                    pygame.mixer.init()
                except pygame.error:
                    pygame.mixer.quit()
                    pygame.mixer.init(frequency=22050, size=-16, channels=2, buffer=512)
            
            pygame.mixer.music.load(filename)
            pygame.mixer.music.set_endevent(MUSIC_END_EVENT)  # 设置结束事件
            pygame.mixer.music.play()

            # 更新状态：正在播放
            new_state = audio_playback_state.get().copy()  # 创建副本
            new_state['is_playing'] = True
            new_state['pygame_initialized'] = True
            new_state['playback_finished'] = False
            new_state['error'] = None
            audio_playback_state.set(new_state)

            ui.update_action_button("audio_play", label="Audio Stop")

            # 不再需要事件监听线程，状态将由 reactive effect 定期检查

        except Exception as e:
            error_msg = f"播放音频时发生错误: {e}"
            logger.error(error_msg)
            with open(temp_log_file, 'a') as f:
                f.write(f"\n--- {error_msg} ---\n")
            update_log()
            ui.notification_show("❌ 播放音频失败", type="error", duration=10)

            # 使用 with reactive.isolate() 来安全地访问 reactive values
            with reactive.isolate():
                new_state = audio_playback_state.get().copy()  # 创建副本
            new_state['is_playing'] = False
            new_state['error'] = str(e)
            audio_playback_state.set(new_state)

            if pygame.mixer.get_init():
                pygame.mixer.quit()

    # 监听播放状态变化，安全更新 UI
    @reactive.effect
    def _():
        # 只有在播放时才检查状态
        state = audio_playback_state.get()
        if state['is_playing']:
            # 使用 reactive.invalidate_later 来定期检查播放状态
            reactive.invalidate_later(0.1)  # 每100毫秒重新运行此effect
            
            try:
                # 检查是否仍在播放
                if pygame.mixer.get_init() and not pygame.mixer.music.get_busy():
                    # 播放结束
                    new_state = audio_playback_state.get().copy()  # 创建副本
                    new_state['is_playing'] = False
                    new_state['playback_finished'] = True
                    audio_playback_state.set(new_state)
                # 如果仍在播放，effect会在0.1秒后重新运行
            except Exception as e:
                # 发生错误
                new_state = audio_playback_state.get().copy()  # 创建副本
                new_state['is_playing'] = False
                new_state['error'] = str(e)
                audio_playback_state.set(new_state)
        else:
            # 不在播放状态时，检查是否需要更新UI
            if state['playback_finished']:
                try:
                    ui.update_action_button("audio_play", label="Audio Play")
                    ui.notification_show("✅ 播放结束", type="message", duration=10)
                    # 清理 mixer
                    if pygame.mixer.get_init():
                        pygame.mixer.quit()
                except Exception as e:
                    logger.error("更新UI时发生错误: %s", e)
            elif state['error']:
                try:
                    ui.update_action_button("audio_play", label="Audio Play")
                    ui.notification_show("⚠️ 播放失败", type="warning", duration=10)
                    if pygame.mixer.get_init():
                        pygame.mixer.quit()
                except Exception as e:
                    logger.error("更新UI时发生错误: %s", e)
