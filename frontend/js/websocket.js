import {
    addUserMessage
} from "./ui.js";

import {
    connect,
    sendMessage
} from "./websocket.js";

const input = document.getElementById("messageInput");
const sendButton = document.getElementById("sendButton");

window.onload = () => {

    connect();

    input.focus();

};

sendButton.onclick = send;

input.addEventListener("keypress", (event) => {

    if (event.key === "Enter")
        send();

});

function send() {

    const message = input.value.trim();

    if (message === "")
        return;

    addUserMessage(message);

    sendMessage(message);

    input.value = "";

}