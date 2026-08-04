from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.ai.speech_service import SpeechService
from app.core.conversation_manager import ConversationManager

router = APIRouter()

speech_service = SpeechService()


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

                reply = await manager.process_message(message)

                print(f"🤖 Emma: {reply}")

                await websocket.send_text(reply)

            # -------------------------
            # Audio Message
            # -------------------------
            elif data.get("bytes"):

                audio_bytes = data["bytes"]

                print(f"🎤 Customer sent audio: {len(audio_bytes)} bytes")

                # Convert audio to text
                message = speech_service.transcribe(audio_bytes)

                print(f"📝 Transcribed: {message}")

                # Ask Emma
                reply = await manager.process_message(message)

                print(f"🤖 Emma: {reply}")

                # Send reply back to browser
                await websocket.send_text(reply)

    except WebSocketDisconnect:

        print("🔴 Browser Disconnected")

    except Exception as e:

        print(f"❌ Error: {e}")

        await websocket.send_text(
            "Sorry, something went wrong."
        )