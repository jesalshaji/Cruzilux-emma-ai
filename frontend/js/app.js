import {
    startRecording,
    stopRecording,
    recording
} from "./audio.js";

import {
    addUserMessage,
    showTyping
} from "./ui.js";

import {
    connect,
    sendMessage,
    sendAudio
} from "./websocket.js";

const sendButton = document.getElementById("sendButton");
const micButton = document.getElementById("micButton");
const input = document.getElementById("messageInput");

window.onload = () => {

    connect();

    input.focus();

};

// -------------------------
// Send Text
// -------------------------

sendButton.onclick = send;

input.addEventListener("keypress", (event) => {

    if (event.key === "Enter") {

        send();

    }

});

function send() {

    const message = input.value.trim();

    if (message === "") return;

    addUserMessage(message);

    showTyping();

    sendMessage(message);

    input.value = "";

}

// -------------------------
// Microphone
// -------------------------

micButton.onclick = async () => {

    try {

        if (!recording()) {

            await startRecording();

            micButton.textContent = "⏹";

        }

        else {

            const audio = await stopRecording();

            micButton.textContent = "🎤";

            showTyping();

            sendAudio(audio);

        }

    }

    catch (err) {

        console.error(err);

    }

};