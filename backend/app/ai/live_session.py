from google import genai
from google.genai import types

from app.config import settings
from app.core.prompt_manager import PromptManager


class LiveSession:
    """
    Manages one Gemini Live conversation session.
    """

    def __init__(self):
        self.client = genai.Client(
            api_key=settings.GEMINI_API_KEY
        )

        self.prompt_manager = PromptManager()

        self.config = types.LiveConnectConfig(
            response_modalities=["AUDIO"],
            system_instruction=self.prompt_manager.get_system_prompt(),
        )

    async def connect(self):
        """
        Open a Live session with Gemini.
        """

        return self.client.aio.live.connect(
            model=settings.LIVE_MODEL,
            config=self.config,
        )