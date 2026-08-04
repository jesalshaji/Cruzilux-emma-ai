from google import genai
from google.genai import types

from app.config import settings


class SpeechService:
    """
    Converts recorded audio into text using Gemini.
    """

    def __init__(self):

        self.client = genai.Client(
            api_key=settings.GEMINI_API_KEY
        )

    def transcribe(self, audio_bytes: bytes) -> str:

        response = self.client.models.generate_content(
            model=settings.CHAT_MODEL,
            contents=[
                "Transcribe this audio. Return only the spoken words.",
                types.Part.from_bytes(
                    data=audio_bytes,
                    mime_type="audio/webm",
                ),
            ],
        )

        return response.text.strip()