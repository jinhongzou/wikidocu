"""
Text-to-speech conversion module for podcast generation.

This module handles the conversion of text scripts into natural-sounding speech using
multiple TTS providers (Google Cloud TTS and ElevenLabs). It includes functionality for:

- Rate limiting API requests to stay within provider quotas
- Exponential backoff retry logic for API resilience 
- Processing individual conversation lines with appropriate voices
- Merging multiple audio segments into a complete podcast
- Managing temporary audio file storage and cleanup

The module supports different voices for interviewer/interviewee to create natural
conversational flow and allows configuration of voice settings and audio effects
through the PodcastConfig system.

Typical usage:
    config = PodcastConfig()
    convert_to_speech(
        config,
        conversation_script,
        'output.mp3',
        '.temp_audio/',
        'mp3'
    )
"""


import logging
import os
import shutil
from io import BytesIO
from pathlib import Path
from typing import List
import base64
import dashscope
from dashscope.audio.tts import SpeechSynthesizer

from elevenlabs import client as elevenlabs_client
from google.cloud import texttospeech
from google.cloud import texttospeech_v1beta1
from pydub import AudioSegment
import openai

from podcast_llm.config import PodcastConfig
from podcast_llm.utils.rate_limits import (
    rate_limit_per_minute,
    retry_with_exponential_backoff
)


logger = logging.getLogger(__name__)



def check_ffmpeg_available():
    """
    Check if FFmpeg is available in the system PATH.
    
    Returns:
        bool: True if FFmpeg is available, False otherwise
    """
    return shutil.which("ffmpeg") is not None and shutil.which("ffprobe") is not None


def check_audio_dependencies():
    """
    Check if all required audio processing dependencies are available.
    
    Raises:
        RuntimeError: If required dependencies are missing
    """
    if not check_ffmpeg_available():
        raise RuntimeError(
            "FFmpeg/FFprobe not found. Please install FFmpeg and add it to your PATH. "
            "Visit https://ffmpeg.org/download.html to download FFmpeg. "
            "After installation, ensure 'ffmpeg' and 'ffprobe' are in your system PATH."
        )


def clean_text_for_tts(lines: List) -> List:
    """
    Clean text lines for text-to-speech processing by removing special characters.

    Takes a list of dictionaries containing speaker and text information and removes
    characters that may interfere with text-to-speech synthesis, such as asterisks,
    underscores, and em dashes.

    Args:
        lines (List[dict]): List of dictionaries with structure:
            {
                'speaker': str,  # Speaker identifier
                'text': str      # Text to be cleaned
            }

    Returns:
        List[dict]: List of dictionaries with cleaned text and same structure as input
    """
    cleaned = []
    for l in lines:
        cleaned.append({'speaker': l['speaker'], 'text': l['text'].replace("*", "").replace("_", "").replace("—", "")})

    return cleaned



def merge_audio_files(audio_files: list, output_file: str, audio_format: str):
    """
    Merge multiple audio files into a single output file.

    Takes a list of audio file paths and combines them sequentially into one continuous
    audio file. Uses pydub library for audio processing and handles different audio
    formats through the format parameter.

    Args:
        audio_files (list): List of paths to audio files to merge
        output_file (str): Path where the merged audio file should be saved
        audio_format (str): Format for the output file (e.g. 'mp3', 'wav')

    Raises:
        Exception: If there are any errors during the merging process
    """
    logger.info("Merging audio files...")
    try:
        combined = AudioSegment.empty()

        for filename in audio_files:
            try:
                audio = AudioSegment.from_file(filename)
                combined += audio
            except FileNotFoundError as e:
                if "ffmpeg" in str(e).lower() or "ffprobe" in str(e).lower():
                    raise FileNotFoundError(
                        "FFmpeg/FFprobe not found. Please install FFmpeg and add it to your PATH. "
                        "Visit https://ffmpeg.org/download.html to download FFmpeg."
                    ) from e
                else:
                    raise
            except Exception as e:
                logger.error(f"Error processing audio file {filename}: {str(e)}")
                raise

        combined.export(output_file, format=audio_format)

        logger.info(f"Successfully merged audio files into {output_file}")
    except Exception as e:
        logger.error(f"Error merging audio files: {str(e)}")
        raise


@retry_with_exponential_backoff(max_retries=10, base_delay=2.0)
@rate_limit_per_minute(max_requests_per_minute=20)
def process_line_google(config: PodcastConfig, text: str, speaker: str):
    """
    Process a single line of text using Google Text-to-Speech API.

    Takes a line of text and speaker identifier and generates synthesized speech using
    Google's TTS service. Uses different voices based on the speaker to create natural
    conversation flow.

    Args:
        text (str): The text content to convert to speech
        speaker (str): Speaker identifier to determine voice selection

    Returns:
        bytes: Raw audio data in bytes format containing the synthesized speech
    """
    client = texttospeech.TextToSpeechClient(client_options={'api_key': config.google_api_key})
    tts_settings = config.tts_settings['google']
    
    interviewer_voice = texttospeech.VoiceSelectionParams(
        language_code=tts_settings['language_code'],
        name=tts_settings['voice_mapping']['Interviewer'],
        ssml_gender=texttospeech.SsmlVoiceGender.FEMALE
    )
    
    interviewee_voice = texttospeech.VoiceSelectionParams(
        language_code=tts_settings['language_code'],
        name=tts_settings['voice_mapping']['Interviewee'],
        ssml_gender=texttospeech.SsmlVoiceGender.MALE
    )
    
    synthesis_input = texttospeech.SynthesisInput(text=text)
    voice = interviewee_voice
    if speaker == 'Interviewer':
        voice = interviewer_voice
    
    # Select the type of audio file you want returned
    audio_config = texttospeech.AudioConfig(
        audio_encoding=texttospeech.AudioEncoding.MP3,
        effects_profile_id=tts_settings['effects_profile_id']
    )
    
    # Perform the text-to-speech request on the text input with the selected
    # voice parameters and audio file type
    response = client.synthesize_speech(
        input=synthesis_input, voice=voice, audio_config=audio_config
    )
    
    return response.audio_content


@retry_with_exponential_backoff(max_retries=10, base_delay=2.0)
@rate_limit_per_minute(max_requests_per_minute=20)
def process_line_elevenlabs(config: PodcastConfig, text: str, speaker: str):
    """
    Process a line of text into speech using ElevenLabs TTS service.

    Takes a line of text and speaker identifier and generates synthesized speech using
    ElevenLabs' TTS service. Uses different voices based on the speaker to create natural
    conversation flow.

    Args:
        config (PodcastConfig): Configuration object containing API keys and settings
        text (str): The text content to convert to speech
        speaker (str): Speaker identifier to determine voice selection

    Returns:
        bytes: Raw audio data in bytes format containing the synthesized speech
    """
    client = elevenlabs_client.ElevenLabs(api_key=config.elevenlabs_api_key)
    tts_settings = config.tts_settings['elevenlabs']

    audio = client.generate(
        text=text,
        voice=tts_settings['voice_mapping'][speaker],
        model=tts_settings['model']
    )

    # Convert audio iterator to bytes that can be written to disk
    audio_bytes = BytesIO()
    for chunk in audio:
        audio_bytes.write(chunk)
    
    return audio_bytes.getvalue()


@retry_with_exponential_backoff(max_retries=10, base_delay=2.0)
@rate_limit_per_minute(max_requests_per_minute=20)
def process_line_dashscope(config: PodcastConfig, text: str, speaker: str):
    """
    Process a line of text into speech using DashScope (ModelScope) TTS service.

    Takes a line of text and speaker identifier and generates synthesized speech using
    DashScope's TTS service. Uses different voices based on the speaker to create natural
    conversation flow.

    Args:
        config (PodcastConfig): Configuration object containing API keys and settings
        text (str): The text content to convert to speech
        speaker (str): Speaker identifier to determine voice selection

    Returns:
        bytes: Raw audio data in bytes format containing the synthesized speech
    """
    dashscope.api_key = config.dashscope_api_key
    tts_settings = config.tts_settings['dashscope']
    
    # Map speakers to voices
    voice = tts_settings['voice_mapping'].get(speaker, 'Cherry')  # Default to Cherry if not found
    
    # Call DashScope TTS API
    response = SpeechSynthesizer.call(
        model=os.getenv('OPENAI_MODEL', 'qwen-turbo'),
        text=text,
        voice=voice
    )
    
    # Check if the request was successful
    if response.status_code == 200:
        # Get the audio data from the response
        audio_url = response.output.audio.url
        
        # Download the audio file
        import requests
        audio_response = requests.get(audio_url)
        if audio_response.status_code == 200:
            return audio_response.content
        else:
            raise Exception(f"Failed to download audio file: {audio_response.status_code}")
    else:
        raise Exception(f"DashScope TTS API error: {response.message}")

@retry_with_exponential_backoff(max_retries=10, base_delay=2.0)
@rate_limit_per_minute(max_requests_per_minute=20)
def process_line_siliconcloud(config: PodcastConfig, text: str, speaker: str):
    """
    Process a line of text into speech using SiliconCloud TTS service.

    Takes a line of text and speaker identifier and generates synthesized speech using
    SiliconCloud's TTS service. Uses different voices based on the speaker to create natural
    conversation flow.

    Args:
        config (PodcastConfig): Configuration object containing API keys and settings
        text (str): The text content to convert to speech
        speaker (str): Speaker identifier to determine voice selection

    Returns:
        bytes: Raw audio data in bytes format containing the synthesized speech
    """
    client = openai.OpenAI(
        api_key=os.getenv("SILICONFLOW_API_KEY"), # 从 https://cloud.siliconflow.cn/account/ak 获取
        base_url="https://api.siliconflow.cn/v1"
    )
    tts_settings = config.tts_settings['siliconcloud']
    
    # Map speakers to voices
    voice = tts_settings['voice_mapping'].get(speaker, 'alex')  # Default to alex if not found
    
    # Map speakers to models
    model = tts_settings.get('model_mapping', {}).get(speaker, 'FunAudioLLM/CosyVoice2-0.5B')  # Default to FunAudioLLM/CosyVoice2-0.5B if not found
    
    # Generate speech using SiliconCloud TTS
    response = client.audio.speech.create(
        model=model,
        voice=f"{model}:{voice}", #voice="FunAudioLLM/CosyVoice2-0.5B:alex", # 系统预置音色
        # model="FunAudioLLM/CosyVoice2-0.5B", # 支持 fishaudio / GPT-SoVITS / CosyVoice2-0.5B 系列模型
        # voice="FunAudioLLM/CosyVoice2-0.5B:alex", # 系统预置音色
        input=text,
        response_format="mp3" # 支持 mp3, wav, pcm, opus 格式
    )
    
    # Return the audio content as bytes
    return response.content


def combine_consecutive_speaker_chunks(chunks: List[dict]) -> List[dict]:
    """
    Combine consecutive chunks from the same speaker into single chunks.
    
    Args:
        chunks (List[dict]): List of dictionaries containing conversation chunks with structure:
            {
                'speaker': str,  # Speaker identifier
                'text': str      # Text content
            }
    
    Returns:
        List[dict]: List of combined chunks where consecutive entries from the same speaker
                   are merged into single chunks
    """
    combined_chunks = []
    current_chunk = None

    for chunk in chunks:
        if current_chunk is None:
            current_chunk = chunk.copy()
        elif current_chunk['speaker'] == chunk['speaker']:
            current_chunk['text'] += ' ' + chunk['text']
        else:
            combined_chunks.append(current_chunk)
            current_chunk = chunk.copy()

    if current_chunk is not None:
        combined_chunks.append(current_chunk)

    return combined_chunks


@retry_with_exponential_backoff(max_retries=10, base_delay=2.0)
@rate_limit_per_minute(max_requests_per_minute=20)
def process_lines_google_multispeaker(config: PodcastConfig, chunks: List):
    """
    Process multiple lines of text into speech using Google's multi-speaker TTS service.

    Takes a chunk of conversation lines and generates synthesized speech using Google's
    multi-speaker TTS service. Handles up to 6 turns of conversation at once for more
    natural conversational flow.

    Args:
        config (PodcastConfig): Configuration object containing API keys and settings
        chunks (List): List of dictionaries containing conversation lines with structure:
            {
                'speaker': str,  # Speaker identifier
                'text': str      # Line content to convert to speech
            }

    Returns:
        bytes: Raw audio data in bytes format containing the synthesized speech
    """
    client = texttospeech_v1beta1.TextToSpeechClient(client_options={'api_key': config.google_api_key})
    tts_settings = config.tts_settings['google_multispeaker']

    # Combine consecutive lines from same speaker
    chunks = combine_consecutive_speaker_chunks(chunks)

    # Create multi-speaker markup
    multi_speaker_markup = texttospeech_v1beta1.MultiSpeakerMarkup()

    # Add each line as a conversation turn
    for line in chunks:
        turn = texttospeech_v1beta1.MultiSpeakerMarkup.Turn()
        turn.text = line['text']
        turn.speaker = tts_settings['voice_mapping'][line['speaker']]
        multi_speaker_markup.turns.append(turn)

    # Configure synthesis input with multi-speaker markup
    synthesis_input = texttospeech_v1beta1.SynthesisInput(
        multi_speaker_markup=multi_speaker_markup
    )

    # Configure voice parameters
    voice = texttospeech_v1beta1.VoiceSelectionParams(
        language_code=tts_settings['language_code'],
        name='en-US-Studio-MultiSpeaker'
    )

    # Configure audio output
    audio_config = texttospeech_v1beta1.AudioConfig(
        audio_encoding=texttospeech_v1beta1.AudioEncoding.MP3_64_KBPS,
        effects_profile_id=tts_settings['effects_profile_id']
    )

    # Generate speech
    response = client.synthesize_speech(
        input=synthesis_input,
        voice=voice,
        audio_config=audio_config
    )

    return response.audio_content


def convert_to_speech(config: PodcastConfig, 
                    conversation: list, 
                    output_file: str, 
                    temp_audio_dir: str, 
                    audio_format: str):
    """
    Convert a conversation script to speech and merge into a single audio file.

    Takes a conversation script and converts each line to speech using the configured
    TTS provider. Individual audio segments are saved to temporary files and then
    merged into a single output file. Temporary files are cleaned up after merging.

    Args:
        config (PodcastConfig): Configuration object containing TTS settings
        conversation (str): List of dictionaries containing conversation lines with structure:
            {
                'speaker': str,  # Speaker identifier ('Interviewer' or 'Interviewee')
                'text': str      # Line content to convert to speech
            }
        output_file (str): Path where the final merged audio file should be saved
        temp_audio_dir (str): Directory path for temporary audio file storage
        audio_format (str): Format of the audio files (e.g. 'mp3')

    Raises:
        Exception: If any errors occur during TTS conversion or file operations
    """
    # Check audio processing dependencies
    check_audio_dependencies()

    tts_audio_formats = {
        'elevenlabs': 'mp3',
        'google': 'mp3',
        'google_multispeaker': 'mp3',
        'dashscope': 'wav',  # DashScope TTS returns WAV format
        'siliconcloud': 'mp3'  # SiliconCloud TTS returns MP3 format
    }

    try:
        logger.info(f"Generating audio files for {len(conversation)} lines...")
        audio_files = []
        counter = 0

        if config.tts_provider == 'google_multispeaker':
            # We will not use a line by line strategy. 
            # Instead we will process in chunks of 6.
            # Process conversation in chunks of 6 lines
            for chunk_start in range(0, len(conversation), 4):
                chunk = conversation[chunk_start:chunk_start + 4]
                logger.info(f"Processing chunk {counter} with {len(chunk)} lines...")
                
                audio = process_lines_google_multispeaker(config, chunk)
                
                file_name = os.path.join(temp_audio_dir, f"{counter:03d}.{tts_audio_formats[config.tts_provider]}")
                with open(file_name, "wb") as out:
                    out.write(audio)
                audio_files.append(file_name)
                
                counter += 1
        else:
            for line in conversation:
                logger.info(f"Generating audio for line {counter}...")

                if config.tts_provider == 'google':
                    audio = process_line_google(config, line['text'], line['speaker'])
                elif config.tts_provider == 'elevenlabs':
                    audio = process_line_elevenlabs(config, line['text'], line['speaker'])
                elif config.tts_provider == 'dashscope':
                    audio = process_line_dashscope(config, line['text'], line['speaker'])
                elif config.tts_provider == 'siliconcloud':
                    audio = process_line_siliconcloud(config, line['text'], line['speaker'])

                logger.info(f"Saving audio chunk {counter}...")
                file_name = os.path.join(temp_audio_dir, f"{counter:03d}.{tts_audio_formats[config.tts_provider]}")
                with open(file_name, "wb") as out:
                    out.write(audio)
                audio_files.append(file_name)

                counter += 1

        # Merge all audio files and save the result
        merge_audio_files(audio_files, output_file, audio_format)

        # Clean up individual audio files
        for file in audio_files:
            os.remove(file)

    except Exception as e:
        raise

def generate_audio(config: PodcastConfig, final_script: list, output_file: str) -> str:
    """
    Generate audio from a podcast script using text-to-speech.

    Takes a final script consisting of speaker/text pairs and generates a single audio file
    using Google's Text-to-Speech service. The script is first cleaned and processed to be
    TTS-friendly, then converted to speech with different voices for different speakers.

    Args:
        final_script (list): List of dictionaries containing script lines with structure:
            {
                'speaker': str,  # Speaker identifier ('Interviewer' or 'Interviewee')
                'text': str      # Line content to convert to speech
            }
        output_file (str): Path where the final audio file should be saved

    Returns:
        str: Path to the generated audio file

    Raises:
        Exception: If any errors occur during TTS conversion or file operations
    """
    cleaned_script = clean_text_for_tts(final_script)

    temp_audio_dir = Path(config.temp_audio_dir)
    temp_audio_dir.mkdir(parents=True, exist_ok=True)
    convert_to_speech(config, cleaned_script, output_file, config.temp_audio_dir, config.output_format)

    return output_file
