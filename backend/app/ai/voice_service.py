import base64
import io
import wave

from google import genai

from app.config import settings


class VoiceService:

    def __init__(self):

        self.client = genai.Client(
            api_key=settings.GEMINI_API_KEY
        )

    def _create_wave_bytes(
        self,
        pcm_data: bytes,
        channels: int = 1,
        sample_rate: int = 24000,
        sample_width: int = 2,
    ) -> bytes:

        buffer = io.BytesIO()

        with wave.open(buffer, "wb") as wav_file:

            wav_file.setnchannels(channels)
            wav_file.setsampwidth(sample_width)
            wav_file.setframerate(sample_rate)
            wav_file.writeframes(pcm_data)

        return buffer.getvalue()

    def speak(self, text: str) -> bytes:

        interaction = self.client.interactions.create(
            model=settings.TTS_MODEL,
            input=text,
            response_format={
                "type": "audio"
            },
            generation_config={
                "speech_config": [
                    {
                        "voice": settings.DEFAULT_VOICE
                    }
                ]
            }
        )

        pcm_audio = base64.b64decode(
            interaction.output_audio.data
        )

        wav_bytes = self._create_wave_bytes(
            pcm_audio
        )

        return wav_bytes