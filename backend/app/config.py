from pathlib import Path
import os

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent

load_dotenv(BASE_DIR / ".env")


class Settings:
    def __init__(self):
        self.GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

        self.LIVE_MODEL = os.getenv(
    "LIVE_MODEL",
    "gemini-3.1-flash-live-preview",
)
        
        if not self.GEMINI_API_KEY:
            raise ValueError(
                "GEMINI_API_KEY is missing in backend/.env"
            )


settings = Settings()