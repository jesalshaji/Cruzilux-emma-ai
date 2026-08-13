// ============================================================
// audio.js
// Microphone recording only
//
// WebSocket communication is handled by websocket.js
// ============================================================

let mediaRecorder = null;
let audioChunks = [];
let mediaStream = null;


// ============================================================
// RECORDING STATE
// ============================================================

export function recording() {

    return (
        mediaRecorder !== null &&
        mediaRecorder.state === "recording"
    );

}


// ============================================================
// START RECORDING
// ============================================================

export async function startRecording() {

    // Prevent starting a second recording
    if (recording()) {

        console.warn(
            "⚠ Recording is already active."
        );

        return;

    }


    try {

        console.log(
            "🎤 Requesting microphone..."
        );


        // --------------------------------------------
        // Get microphone access
        // --------------------------------------------

        mediaStream =
            await navigator.mediaDevices.getUserMedia({
                audio: true
            });


        // --------------------------------------------
        // Create MediaRecorder
        // --------------------------------------------

        let options = {};

        /*
         * WebM/Opus is widely supported by modern
         * browsers and is suitable for sending to
         * the backend speech service.
         */

        if (
            MediaRecorder.isTypeSupported(
                "audio/webm;codecs=opus"
            )
        ) {

            options.mimeType =
                "audio/webm;codecs=opus";

        }

        else if (
            MediaRecorder.isTypeSupported(
                "audio/webm"
            )
        ) {

            options.mimeType =
                "audio/webm";

        }


        mediaRecorder =
            new MediaRecorder(
                mediaStream,
                options
            );


        audioChunks = [];


        // --------------------------------------------
        // Collect audio chunks
        // --------------------------------------------

        mediaRecorder.ondataavailable =
            (event) => {

                if (
                    event.data &&
                    event.data.size > 0
                ) {

                    audioChunks.push(
                        event.data
                    );

                }

            };


        // --------------------------------------------
        // Error handling
        // --------------------------------------------

        mediaRecorder.onerror =
            (event) => {

                console.error(
                    "❌ MediaRecorder error:",
                    event.error
                );

            };


        // --------------------------------------------
        // Start
        // --------------------------------------------

        mediaRecorder.start();

        console.log(
            "🎤 Recording started"
        );

    }

    catch (error) {

        console.error(
            "❌ Microphone error:",
            error
        );


        mediaRecorder = null;


        if (mediaStream) {

            mediaStream
                .getTracks()
                .forEach(
                    track => track.stop()
                );

            mediaStream = null;

        }


        throw error;

    }

}


// ============================================================
// STOP RECORDING
// ============================================================

export function stopRecording() {

    return new Promise(
        (resolve, reject) => {

            if (!mediaRecorder) {

                reject(
                    new Error(
                        "No active recording."
                    )
                );

                return;

            }


            if (
                mediaRecorder.state !==
                "recording"
            ) {

                reject(
                    new Error(
                        "Recording is not active."
                    )
                );

                return;

            }


            // ----------------------------------------
            // Save reference
            // ----------------------------------------

            const recorder =
                mediaRecorder;


            // ----------------------------------------
            // When recording finishes
            // ----------------------------------------

            recorder.onstop = () => {

                try {

                    const mimeType =
                        recorder.mimeType ||
                        "audio/webm";


                    const audioBlob =
                        new Blob(
                            audioChunks,
                            {
                                type: mimeType
                            }
                        );


                    console.log(
                        "🎤 Recording stopped"
                    );

                    console.log(
                        "📦 Audio size:",
                        audioBlob.size,
                        "bytes"
                    );

                    console.log(
                        "🎵 Audio type:",
                        audioBlob.type
                    );


                    // --------------------------------
                    // Stop microphone tracks
                    // --------------------------------

                    if (mediaStream) {

                        mediaStream
                            .getTracks()
                            .forEach(
                                track =>
                                    track.stop()
                            );

                    }


                    mediaStream = null;
                    mediaRecorder = null;
                    audioChunks = [];


                    resolve(
                        audioBlob
                    );

                }

                catch (error) {

                    mediaRecorder = null;
                    audioChunks = [];

                    reject(
                        error
                    );

                }

            };


            // ----------------------------------------
            // Stop
            // ----------------------------------------

            recorder.stop();

        }
    );

}