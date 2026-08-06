import base64
import wave

from google import genai

from app.config import settings


class VoiceService:

    def __init__(self):

        self.client = genai.Client(
            api_key=settings.GEMINI_API_KEY
        )

    def _save_wave(
        self,
        filename: str,
        pcm_data: bytes,
        channels: int = 1,
        sample_rate: int = 24000,
        sample_width: int = 2,
    ):

        with wave.open(filename, "wb") as wav_file:

            wav_file.setnchannels(channels)
            wav_file.setsampwidth(sample_width)
            wav_file.setframerate(sample_rate)
            wav_file.writeframes(pcm_data)

    def speak(self, text: str):

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

        self._save_wave(
            "test.wav",
            pcm_audio,
        )

        return "test.wav"