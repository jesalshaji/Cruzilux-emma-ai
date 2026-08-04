const button = document.getElementById("connectButton");
const status = document.getElementById("status");
const messages = document.getElementById("messages");

let socket = null;

button.onclick = () => {

    // Prevent opening multiple connections
    if (socket && socket.readyState === WebSocket.OPEN) {
        return;
    }

    socket = new WebSocket("ws://127.0.0.1:8000/ws/voice");

    socket.onopen = () => {

        status.innerHTML = "🟢 Connected";

        // Send the first message to Emma
        socket.send("Hello Emma");

    };

    socket.onmessage = (event) => {

        messages.innerHTML += `<p><strong>Emma:</strong> ${event.data}</p>`;

        // Scroll to latest message
        messages.scrollTop = messages.scrollHeight;

    };

    socket.onclose = () => {

        status.innerHTML = "🔴 Disconnected";

    };

    socket.onerror = (error) => {

        console.error(error);

        messages.innerHTML +=
            `<p style="color:red;"><strong>Error:</strong> Connection failed.</p>`;

    };

};