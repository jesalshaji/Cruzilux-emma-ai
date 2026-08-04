from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.core.conversation_manager import ConversationManager

router = APIRouter()


@router.websocket("/ws/voice")
async def voice_socket(websocket: WebSocket):
    await websocket.accept()

    manager = ConversationManager()

    print("🟢 Browser Connected")

    await websocket.send_text("Connected to Emma!")

    try:
        while True:
            # Receive message from browser
            message = await websocket.receive_text()

            print(f"👤 Customer: {message}")

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