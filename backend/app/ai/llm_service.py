from google import genai

from app.config import settings


class GeminiService:
    """Handles all communication with the Gemini API."""

    def __init__(self):
        self.client = genai.Client(
            api_key=settings.GEMINI_API_KEY
        )

    def chat(self, system_prompt: str, user_message: str) -> str:
        prompt = f"""
{system_prompt}

User:
{user_message}
"""

        response = self.client.models.generate_content(
            model="gemini-flash-latest",
            contents=prompt
        )

        return response.text