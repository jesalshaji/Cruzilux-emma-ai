import json
import time

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.ai.speech_service import SpeechService
from app.ai.voice_service import VoiceService
from app.core.conversation_manager import ConversationManager

router = APIRouter()

speech_service = SpeechService()
voice_service = VoiceService()


@router.websocket("/ws/voice")
async def voice_socket(websocket: WebSocket):

    await websocket.accept()

    manager = ConversationManager()

    print("🟢 Browser Connected")

    try:

        while True:

            data = await websocket.receive()

            # -------------------------
            # Text Message
            # -------------------------
            if data.get("text"):

                message = data["text"]

                print(f"👤 Customer: {message}")

                # AI Response Timing
                start = time.perf_counter()

                reply = await manager.process_message(message)

                print(f"🧠 LLM: {time.perf_counter() - start:.2f}s")
                print(f"🤖 Emma: {reply}")

                # TTS Timing
                start = time.perf_counter()

                voice_bytes = voice_service.speak(reply)

                print(f"🔊 TTS: {time.perf_counter() - start:.2f}s")

                # Send text
                await websocket.send_text(
                    json.dumps({
                        "type": "text",
                        "message": reply
                    })
                )

                # Send audio
                await websocket.send_bytes(voice_bytes)

            # -------------------------
            # Audio Message
            # -------------------------
            elif data.get("bytes"):

                audio_bytes = data["bytes"]

                print(f"🎤 Customer sent audio: {len(audio_bytes)} bytes")

                # -------------------------
                # Speech Recognition
                # -------------------------
                start = time.perf_counter()

                message = speech_service.transcribe(audio_bytes)

                print(f"🎤 Speech: {time.perf_counter() - start:.2f}s")
                print(f"📝 Transcribed: {message}")

                # -------------------------
                # AI Response
                # -------------------------
                start = time.perf_counter()

                reply = await manager.process_message(message)

                print(f"🧠 LLM: {time.perf_counter() - start:.2f}s")
                print(f"🤖 Emma: {reply}")

                # -------------------------
                # Text-to-Speech
                # -------------------------
                start = time.perf_counter()

                voice_bytes = voice_service.speak(reply)

                print(f"🔊 TTS: {time.perf_counter() - start:.2f}s")

                # Send text
                await websocket.send_text(
                    json.dumps({
                        "type": "text",
                        "message": reply
                    })
                )

                # Send audio
                await websocket.send_bytes(voice_bytes)

    except WebSocketDisconnect:

        print("🔴 Browser Disconnected")

    except Exception as e:

        print(f"❌ Error: {e}")

        try:
            await websocket.send_text(
                json.dumps({
                    "type": "error",
                    "message": "Sorry, something went wrong."
                })
            )
        except:
            pass