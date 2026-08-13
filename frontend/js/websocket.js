import {
    addEmmaMessage,
    addBookingConfirmation,
    hideTyping,
    setStatus
} from "./ui.js";


let socket = null;

let audioContext = null;
let nextAudioTime = 0;
let audioStarted = false;


// ============================================================
// AUDIO SETUP
// ============================================================

function getAudioContext() {

    if (!audioContext) {

        audioContext = new AudioContext({
            sampleRate: 24000
        });

    }

    return audioContext;
}


// ============================================================
// PLAY PCM16 AUDIO CHUNK
// ============================================================

async function playPCMChunk(arrayBuffer) {

    const context =
        getAudioContext();


    if (context.state === "suspended") {

        await context.resume();

    }


    const pcm =
        new Int16Array(
            arrayBuffer
        );


    const audioBuffer =
        context.createBuffer(
            1,
            pcm.length,
            24000
        );


    const channelData =
        audioBuffer.getChannelData(0);


    for (
        let i = 0;
        i < pcm.length;
        i++
    ) {

        channelData[i] =
            pcm[i] / 32768;

    }


    const source =
        context.createBufferSource();


    source.buffer =
        audioBuffer;


    source.connect(
        context.destination
    );


    const now =
        context.currentTime;


    if (nextAudioTime < now) {

        nextAudioTime = now;

    }


    source.start(
        nextAudioTime
    );


    nextAudioTime +=
        audioBuffer.duration;


    if (!audioStarted) {

        audioStarted = true;

        console.log(
            "🔊 Emma started speaking"
        );

    }

}


// ============================================================
// CONNECT
// ============================================================

export function connect() {

    socket =
        new WebSocket(
            "ws://127.0.0.1:8000/ws/voice"
        );


    socket.binaryType =
        "arraybuffer";


    setStatus(
        "🟡 Connecting..."
    );


    // ========================================================
    // OPEN
    // ========================================================

    socket.onopen = async () => {

        setStatus(
            "🟢 Emma Online"
        );


        /*
         * Temporary greeting.
         *
         * Later we can make this greeting
         * come through Emma's actual TTS.
         */

        addEmmaMessage(
            "Hello! I'm Emma. How can I help you today?"
        );

    };


    // ========================================================
    // MESSAGE
    // ========================================================

    socket.onmessage =
        async (event) => {

            hideTyping();


            // ==================================================
            // JSON MESSAGE
            // ==================================================

            if (
                typeof event.data === "string"
            ) {

                let data;


                try {

                    data =
                        JSON.parse(
                            event.data
                        );

                }

                catch (error) {

                    console.error(
                        "❌ Invalid JSON from server:",
                        error
                    );

                    return;

                }


                // ==============================================
                // EMMA TEXT
                // ==============================================

                if (
                    data.type === "text"
                ) {

                    addEmmaMessage(
                        data.message
                    );

                }


                // ==============================================
                // DEMO BOOKING CONFIRMATION
                // ==============================================

                else if (
                    data.type ===
                    "booking_confirmed"
                ) {

                    console.log(
                        "📋 Demo booking confirmed:",
                        data.appointment
                    );


                    /*
                     * The UI owns the booking card.
                     *
                     * websocket.js only receives
                     * the event and passes the
                     * appointment data to ui.js.
                     */

                    addBookingConfirmation(
                        data.appointment
                    );

                }


                // ==============================================
                // ERROR
                // ==============================================

                else if (
                    data.type === "error"
                ) {

                    addEmmaMessage(
                        data.message
                    );


                    setStatus(
                        "🟠 Emma temporarily unavailable"
                    );

                }


                // ==============================================
                // UNKNOWN JSON EVENT
                // ==============================================

                else {

                    console.log(
                        "ℹ️ Unknown server event:",
                        data
                    );

                }

            }


            // ==================================================
            // PCM AUDIO
            // ==================================================

            else {

                try {

                    await playPCMChunk(
                        event.data
                    );

                }

                catch (error) {

                    console.error(
                        "❌ Audio playback error:",
                        error
                    );

                }

            }

        };


    // ========================================================
    // CLOSE
    // ========================================================

    socket.onclose =
        (event) => {

            console.log(
                "🔴 WebSocket closed:",
                event.code,
                event.reason
            );


            setStatus(
                "🔴 Emma Offline"
            );

        };


    // ========================================================
    // ERROR
    // ========================================================

    socket.onerror =
        (error) => {

            console.error(
                "❌ WebSocket error:",
                error
            );


            setStatus(
                "🟠 Emma connection error"
            );

        };

}


// ============================================================
// SEND TEXT
// ============================================================

export function sendMessage(
    message
) {

    if (
        socket &&
        socket.readyState ===
        WebSocket.OPEN
    ) {

        socket.send(
            message
        );

    }

    else {

        console.warn(
            "⚠ Emma is not connected."
        );

    }

}


// ============================================================
// SEND AUDIO
// ============================================================

export function sendAudio(
    audioBlob
) {

    if (
        socket &&
        socket.readyState ===
        WebSocket.OPEN
    ) {

        socket.send(
            audioBlob
        );

    }

    else {

        console.warn(
            "⚠ Emma is not connected."
        );

    }

}