import asyncio
import json
import time
import traceback

from fastapi import (
    APIRouter,
    WebSocket,
    WebSocketDisconnect,
)

from app.ai.speech_service import SpeechService
from app.ai.voice_service import VoiceService
from app.core.conversation_manager import (
    ConversationManager,
)


router = APIRouter()

speech_service = SpeechService()
voice_service = VoiceService()


def get_next_chunk(generator):

    try:
        return next(generator)

    except StopIteration:
        return None


async def stream_voice(
    websocket: WebSocket,
    text: str,
    language: str,
):

    start = time.perf_counter()

    print(
        f"🌍 TTS language passed to VoiceService: "
        f"{language}"
    )

    audio_stream = (
        voice_service.stream_speak(
            text,
            language=language,
        )
    )

    while True:

        chunk = await asyncio.to_thread(
            get_next_chunk,
            audio_stream,
        )

        if chunk is None:
            break

        await websocket.send_bytes(
            chunk
        )

    print(
        "🔊 TTS stream finished: "
        f"{time.perf_counter() - start:.2f}s"
    )


async def send_reply(
    websocket: WebSocket,
    manager: ConversationManager,
    message: str,
):

    print(
        f"👤 Customer: {message}"
    )

    # ------------------------------------
    # AI
    # ------------------------------------

    start = time.perf_counter()

    reply = await manager.process_message(
        message
    )

    print(
        f"🧠 LLM: "
        f"{time.perf_counter() - start:.2f}s"
    )

    print(
        f"🤖 Emma: {reply}"
    )

    # ------------------------------------
    # Text
    # ------------------------------------

    await websocket.send_text(
        json.dumps(
            {
                "type": "text",
                "message": reply,
            }
        )
    )

    # ------------------------------------
    # Booking event
    # ------------------------------------

    booking = (
        manager.consume_booking_event()
    )

    if booking:

        print(
            "📋 DEMO BOOKING CREATED:"
        )

        print(
            json.dumps(
                booking,
                indent=2,
            )
        )

        await websocket.send_text(
            json.dumps(
                {
                    "type": "booking_confirmed",
                    "appointment": booking,
                }
            )
        )

    # ------------------------------------
    # TTS
    # ------------------------------------

    try:

        await stream_voice(
    websocket,
    reply,
    manager.current_language or "en",
)

    except Exception as error:

        print(
            f"❌ TTS Error: {error}"
        )

        await websocket.send_text(
            json.dumps(
                {
                    "type": "error",
                    "message": (
                        "Emma is having a "
                        "temporary voice issue. "
                        "Please try again."
                    ),
                }
            )
        )


@router.websocket("/ws/voice")
async def voice_socket(
    websocket: WebSocket,
):

    await websocket.accept()

    manager = ConversationManager()

    print(
        "🟢 Browser Connected"
    )

    try:

        while True:

            data = await websocket.receive()

            if (
                data.get("type")
                == "websocket.disconnect"
            ):

                print(
                    "🔴 Browser Disconnected"
                )

                break

            # ==========================================
            # TEXT
            # ==========================================

            if data.get("text"):

                await send_reply(
                    websocket,
                    manager,
                    data["text"],
                )

            # ==========================================
            # AUDIO
            # ==========================================

            elif data.get("bytes"):

                audio_bytes = data["bytes"]

                print(
                    "🎤 Customer sent audio: "
                    f"{len(audio_bytes)} bytes"
                )

                # ----------------------------------
                # STT
                # ----------------------------------

                start = time.perf_counter()

                message = (
                    speech_service.transcribe(
                        audio_bytes
                    )
                )

                print(
                    "🎤 Speech: "
                    f"{time.perf_counter() - start:.2f}s"
                )

                print(
                    f"📝 Transcribed: {message}"
                )

                await send_reply(
                    websocket,
                    manager,
                    message,
                )

    except WebSocketDisconnect:

        print(
            "🔴 Browser Disconnected"
        )

    except Exception as error:

        print(
            "\n❌ WebSocket Error"
        )

        print(
            f"Type: {type(error).__name__}"
        )

        print(
            f"Error: {error}"
        )

        traceback.print_exc()

        try:

            await websocket.send_text(
                json.dumps(
                    {
                        "type": "error",
                        "message": (
                            "Sorry, something "
                            "went wrong."
                        ),
                    }
                )
            )

        except Exception:

            pass