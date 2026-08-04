from google import genai

from app.config import settings


class GeminiService:
    """
    Handles all communication with the Gemini Text API.
    """

    def __init__(self):
        self.client = genai.Client(
            api_key=settings.GEMINI_API_KEY
        )

    def chat(self, system_prompt: str, user_message: str) -> str:
        """
        Send a text prompt to Gemini and return the response.
        """

        prompt = f"""
{system_prompt}

User:
{user_message}

Emma:
"""

        response = self.client.models.generate_content(
            model=settings.CHAT_MODEL,
            contents=prompt,
        )

        return response.text.strip()