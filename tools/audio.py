import base64
import json
import os
import traceback
from typing import List
from pydantic import Field
from .file_utils import get_file_from_source
from openai import OpenAI
from config import Config
from .decorator import tool
import dashscope
from dashscope import MultiModalConversation


provider = "qwen-audio"
config = Config()
api_key = config.get_api_key(provider)
base_url = config.get_base_url(provider)


client = OpenAI(
    api_key=api_key, 
    base_url=base_url,
)

model = config.get_model(provider)

AUDIO_TRANSCRIBE = """
Input is a base64 encoded audio. Transcribe the audio content. 
Return a json string with the following format: 
{
    "audio_text": "transcribed text from audio"
}
"""


def encode_audio(audio_path):
    with open(audio_path, "rb") as audio_file:
        return base64.b64encode(audio_file.read()).decode("utf-8")


@tool()
def transcribe_audio(audio_path: str) -> str:
    """
    Transcribe the given audio in a list of filepaths or urls.

    Args:
        audio_urls: List of audio file paths or URLs

    Returns:
        str: JSON string containing transcriptions
    """

    # base64_audio = encode_audio(audio_path)
    messages = [
        {
            "role": "system", 
            "content": [{"text": "You are a helpful assistant."}]},
        {
            "role": "user",
            "content": [{"audio": audio_path}, {"text": AUDIO_TRANSCRIBE}],
        }
    ]
    response = MultiModalConversation.call(
        model="qwen-audio-turbo-latest", 
        messages=messages,
        api_key=api_key,
    )

    print(response)
    res = response["output"]["choices"][0]["message"]["content"][0]["text"]
    return res


# @tool()
# def transcribe_audio(
#     audio_urls: List[str] = Field(
#         description="The input audio in given a list of filepaths or urls."
#     ),
# ) -> str:
#     """
#     Transcribe the given audio in a list of filepaths or urls.

#     Args:
#         audio_urls: List of audio file paths or URLs

#     Returns:
#         str: JSON string containing transcriptions
#     """
#     transcriptions = []
#     for audio_url in audio_urls:
#         try:
#             # Get file with validation (only audio files allowed)
#             file_path, mime_type, content = get_file_from_source(
#                 audio_url,
#                 allowed_mime_prefixes=["audio/"],
#                 max_size_mb=50.0,  # 50MB limit for audio files
#                 type="audio",  # Specify type as audio to handle audio files
#             )

#             # Use the file for transcription
#             with open(file_path, "rb") as audio_file:
#                 transcription = client.audio.transcriptions.create(
#                     file=audio_file,
#                     model=model,
#                     response_format="text",
#                 )
#                 transcriptions.append(transcription)

#             # Clean up temporary file if it was created for a URL
#             if file_path != os.path.abspath(audio_url) and os.path.exists(file_path):
#                 os.unlink(file_path)

#         except Exception as e:
#             print(f"Error transcribing {audio_url}: {traceback.format_exc()}")
#             transcriptions.append(f"Error: {str(e)}")

#     print(f"---get_text_by_transcribe-transcription:{transcriptions}")
#     return json.dumps(transcriptions, ensure_ascii=False)
