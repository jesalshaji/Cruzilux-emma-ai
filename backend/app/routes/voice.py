from fastapi import APIRouter, WebSocket

router = APIRouter()


@router.websocket("/ws/voice")
async def voice_socket(websocket: WebSocket):
    await websocket.accept()

    print("🟢 Browser Connected")

    await websocket.send_text(
        "Connected to Emma!"
    )

    try:
        while True:
            message = await websocket.receive_text()

            print(f"Customer: {message}")

            await websocket.send_text(
                f"Emma received: {message}"
            )

    except Exception:
        print("🔴 Browser Disconnected")