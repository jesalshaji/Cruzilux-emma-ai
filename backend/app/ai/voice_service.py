import base64
import time
from collections import OrderedDict

from google import genai

from app.config import settings


class VoiceService:
    """
    Handles Emma's Gemini text-to-speech generation.

    Supports:
        - English
        - German
        - Explicit TTS language
        - Language-aware cache
        - Streaming PCM audio
    """

    def __init__(self):

        self.client = genai.Client(
            api_key=settings.GEMINI_API_KEY
        )

        self.audio_cache = OrderedDict()

        self.max_cache_size = 50

    # ============================================================
    # LANGUAGE
    # ============================================================

    def _normalize_language(self, language):

        if not language:
            return "en"

        language = str(language).lower().strip()

        if language.startswith("de"):
            return "de"

        return "en"

    # ============================================================
    # CACHE
    # ============================================================

    def _make_cache_key(
        self,
        text,
        language
    ):

        return (
            f"{language}:"
            f"{text.strip()}"
        )

    def _get_cached_audio(
        self,
        text,
        language
    ):

        key = self._make_cache_key(
            text,
            language
        )

        if key not in self.audio_cache:
            return None

        self.audio_cache.move_to_end(key)

        print(
            f"⚡ TTS cache hit [{language}]"
        )

        return self.audio_cache[key]

    def _save_cached_audio(
        self,
        text,
        language,
        chunks
    ):

        key = self._make_cache_key(
            text,
            language
        )

        self.audio_cache[key] = chunks

        self.audio_cache.move_to_end(key)

        while len(self.audio_cache) > self.max_cache_size:

            self.audio_cache.popitem(
                last=False
            )

    # ============================================================
    # STREAM SPEECH
    # ============================================================

    def stream_speak(
        self,
        text,
        language="en"
    ):

        language = self._normalize_language(
            language
        )

        print(
            "\n========== Emma TTS STREAM =========="
        )

        print(
            f"🌍 Language: {language}"
        )

        print(
            f"📝 Text: {text}"
        )

        # --------------------------------------------------------
        # CACHE
        # --------------------------------------------------------

        cached_chunks = (
            self._get_cached_audio(
                text,
                language
            )
        )

        if cached_chunks is not None:

            print(
                f"📦 Cached chunks: "
                f"{len(cached_chunks)}"
            )

            for chunk in cached_chunks:
                yield chunk

            print(
                "====================================\n"
            )

            return

        # --------------------------------------------------------
        # TTS
        # --------------------------------------------------------

        start = time.perf_counter()

        first_audio_time = None

        chunk_count = 0

        total_bytes = 0

        collected_chunks = []

        try:

            # ====================================================
            # IMPORTANT:
            #
            # Gemini Interactions API supports an explicit
            # speech language.
            #
            # This is what makes German actually German.
            # ====================================================

            speech_language = (
                "de"
                if language == "de"
                else "en"
            )

            stream = (
                self.client.interactions.create(
                    model=settings.TTS_MODEL,

                    input=text,

                    response_format={
                        "type": "audio"
                    },

                    generation_config={
                        "speech_config": [
                            {
                                "language": speech_language,
                                "voice": (
                                    settings.DEFAULT_VOICE
                                )
                            }
                        ]
                    },

                    stream=True
                )
            )

            # ----------------------------------------------------
            # AUDIO STREAM
            # ----------------------------------------------------

            for event in stream:

                if event.event_type == "error":

                    print(
                        "❌ Gemini TTS Error Event:"
                    )

                    print(event)

                    error_message = str(
                        getattr(
                            event,
                            "error",
                            event,
                        )
                    )

                    if "quota_exceeded" in error_message:

                        raise RuntimeError(
                            "TTS_QUOTA_EXCEEDED"
                        )

                    raise RuntimeError(
                        "TTS_GENERATION_FAILED"
                    )

                if (
                    event.event_type
                    != "step.delta"
                ):
                    continue

                delta = event.delta

                if (
                    getattr(
                        delta,
                        "type",
                        None
                    )
                    != "audio"
                ):
                    continue

                pcm_audio = (
                    base64.b64decode(
                        delta.data
                    )
                )

                if not pcm_audio:

                    print(
                        "⚠️ Empty audio chunk"
                    )

                    continue

                chunk_count += 1

                total_bytes += (
                    len(pcm_audio)
                )

                collected_chunks.append(
                    pcm_audio
                )

                if first_audio_time is None:

                    first_audio_time = (
                        time.perf_counter()
                        - start
                    )

                    print(
                        f"⚡ First audio chunk: "
                        f"{first_audio_time:.2f}s"
                    )

                # Send immediately
                yield pcm_audio

            # ----------------------------------------------------
            # CACHE
            # ----------------------------------------------------

            if not collected_chunks:

                raise RuntimeError(
                    "TTS_NO_AUDIO"
                )

            self._save_cached_audio(
                text,
                language,
                collected_chunks
            )

            total_time = (
                time.perf_counter()
                - start
            )

            print(
                f"🔊 TTS complete: "
                f"{total_time:.2f}s"
            )

            print(
                f"📦 Chunks: "
                f"{chunk_count}"
            )

            print(
                f"📦 Total PCM: "
                f"{total_bytes} bytes"
            )

            print(
                f"💾 Cache size: "
                f"{len(self.audio_cache)}"
            )

            print(
                "====================================\n"
            )

        except Exception as e:

            print(
                f"❌ TTS Streaming Error: {e}"
            )

            raise