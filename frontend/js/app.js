const sendButton = document.getElementById("sendButton");
const input = document.getElementById("messageInput");
const status = document.getElementById("status");
const messages = document.getElementById("messages");
const typing = document.getElementById("typing");

let socket = null;

// Automatically connect when the page loads
window.onload = () => {

    connect();

    input.focus();

};

// -------------------------
// WebSocket
// -------------------------

function connect() {

    socket = new WebSocket("ws://127.0.0.1:8000/ws/voice");

    socket.onopen = () => {

        status.textContent = "🟢 Emma Online";

        addEmmaMessage(
            "Hello! I'm Emma. How can I help you today?"
        );

    };

    socket.onmessage = (event) => {

        hideTyping();

        addEmmaMessage(event.data);

    };

    socket.onclose = () => {

        status.textContent = "🔴 Offline";

    };

    socket.onerror = () => {

        hideTyping();

        addEmmaMessage(
            "I'm having trouble connecting right now."
        );

    };

}

// -------------------------
// Send Message
// -------------------------

sendButton.onclick = sendMessage;

input.addEventListener("keypress", (event) => {

    if (event.key === "Enter") {

        sendMessage();

    }

});

function sendMessage() {

    if (!socket || socket.readyState !== WebSocket.OPEN)
        return;

    const text = input.value.trim();

    if (text === "")
        return;

    addUserMessage(text);

    showTyping();

    socket.send(text);

    input.value = "";

}

// -------------------------
// UI
// -------------------------

function addUserMessage(text) {

    messages.innerHTML += `
        <div class="user-message">
            <strong>👤 You</strong>
            ${text}
        </div>
    `;

    scrollBottom();

}

function addEmmaMessage(text) {

    messages.innerHTML += `
        <div class="emma-message">
            <strong>🤖 Emma</strong>
            ${text}
        </div>
    `;

    scrollBottom();

}

function showTyping() {

    typing.classList.remove("hidden");

}

function hideTyping() {

    typing.classList.add("hidden");

}

function scrollBottom() {

    messages.scrollTop = messages.scrollHeight;

}