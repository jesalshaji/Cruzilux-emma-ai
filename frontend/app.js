const button = document.getElementById("connectButton");
const status = document.getElementById("status");
const messages = document.getElementById("messages");

let socket = null;

button.onclick = () => {

    socket = new WebSocket("ws://127.0.0.1:8000/ws/voice");

    socket.onopen = () => {

        status.innerHTML = "🟢 Connected";

    };

    socket.onmessage = (event) => {

        messages.innerHTML += `<p>${event.data}</p>`;

    };

    socket.onclose = () => {

        status.innerHTML = "🔴 Disconnected";

    };

};