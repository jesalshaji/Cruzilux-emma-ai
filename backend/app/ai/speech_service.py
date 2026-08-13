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
        """
You are the speech transcription layer for Emma, an AI receptionist.

Transcribe the customer's speech as accurately as possible.

Important rules:
- Return ONLY the words actually spoken by the customer.
- Do NOT answer the customer.
- Do NOT summarize the speech.
- Do NOT translate the speech.
- Do NOT invent or replace words.
- Preserve the customer's language.
- The customer may speak naturally, quickly, or with short pauses.
- Pay special attention to words commonly used in a business receptionist conversation.

Relevant vocabulary may include:
appointment, booking, book, tomorrow, today, haircut,
haircuts, beard, beard trim, beard trimming, kids haircut,
barber, service, services, opening hours, available,
morning, afternoon, evening, time, price, cost.

The customer may also speak German.

Return only the transcription.
""",
        types.Part.from_bytes(
            data=audio_bytes,
            mime_type="audio/webm",
        ),
    ],
)

        return response.text.strip()