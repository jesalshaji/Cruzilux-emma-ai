from app.ai.gemini_service import GeminiService
from app.core.prompt_manager import PromptManager


class ConversationManager:
    """
    Manages one text conversation with Emma.
    """

    def __init__(self):
        self.gemini = GeminiService()
        self.prompt_manager = PromptManager()

    async def process_message(self, message: str) -> str:
        """
        Send a text message to Gemini and return the reply.
        """

        system_prompt = self.prompt_manager.get_system_prompt()

        reply = self.gemini.chat(
            system_prompt=system_prompt,
            user_message=message,
        )

        return reply