const messages = document.getElementById("messages");
const status = document.getElementById("status");
const typing = document.getElementById("typing");

export function setStatus(text) {
    status.textContent = text;
}

export function showTyping() {
    typing.classList.remove("hidden");
}

export function hideTyping() {
    typing.classList.add("hidden");
}

export function addUserMessage(text) {

    messages.innerHTML += `
        <div class="user-message">
            <strong>👤 You</strong>
            ${text}
        </div>
    `;

    scrollToBottom();
}

export function addEmmaMessage(text) {

    messages.innerHTML += `
        <div class="emma-message">
            <strong>🤖 Emma</strong>
            ${text}
        </div>
    `;

    scrollToBottom();
}

function scrollToBottom() {
    messages.scrollTop = messages.scrollHeight;
}