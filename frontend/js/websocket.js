import {
    addEmmaMessage,
    hideTyping,
    setStatus
} from "./ui.js";

let socket = null;

export function connect() {

    socket = new WebSocket(
        "ws://127.0.0.1:8000/ws/voice"
    );

    socket.binaryType = "arraybuffer";

    setStatus("🟡 Connecting...");

    socket.onopen = () => {

        setStatus("🟢 Emma Online");

        addEmmaMessage(
            "Hello! I'm Emma. How can I help you today?"
        );

    };

        socket.onmessage = async (event) => {

        hideTyping();

        // JSON message
        if (typeof event.data === "string") {

            const data = JSON.parse(event.data);

            if (data.type === "text") {

                addEmmaMessage(data.message);

            }

            else if (data.type === "error") {

                addEmmaMessage(data.message);

            }

        }

        // Binary Audio
        else {

            const blob = new Blob(
                [event.data],
                {
                    type: "audio/wav"
                }
            );

            const url =
                URL.createObjectURL(blob);

            const audio =
                new Audio(url);

            try {

                await audio.play();

            }

            catch (err) {

                console.error(err);

            }

            audio.onended = () => {

                URL.revokeObjectURL(url);

            };

        }

    };

        socket.onclose = () => {

        setStatus("🔴 Emma Offline");

    };

    socket.onerror = () => {

        setStatus("🔴 Connection Error");

    };

}

export function sendMessage(message) {

    if (
        socket &&
        socket.readyState === WebSocket.OPEN
    ) {

        socket.send(message);

    }

}

export function sendAudio(audioBlob) {

    if (
        socket &&
        socket.readyState === WebSocket.OPEN
    ) {

        socket.send(audioBlob);

    }

}

