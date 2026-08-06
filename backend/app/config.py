from pathlib import Path
import os

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent

load_dotenv(BASE_DIR / ".env")


class Settings:
    def __init__(self):
        self.GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

        # Gemini model for text conversations
        self.CHAT_MODEL = os.getenv(
            "CHAT_MODEL",
            "gemini-flash-latest",
        )

        # Gemini Live model for voice conversations
        self.LIVE_MODEL = os.getenv(
            "LIVE_MODEL",
            "gemini-3.1-flash-live-preview",
        )

                # Gemini Text-to-Speech model
        self.TTS_MODEL = os.getenv(
            "TTS_MODEL",
            "gemini-2.5-flash-preview-tts",
        )

        self.DEFAULT_LANGUAGE = os.getenv(
            "DEFAULT_LANGUAGE",
            "auto",
        )

        self.DEFAULT_VOICE = os.getenv(
            "DEFAULT_VOICE",
            "Aoede",
        )

        if not self.GEMINI_API_KEY:
            raise ValueError(
                "GEMINI_API_KEY is missing in backend/.env"
            )


settings = Settings()