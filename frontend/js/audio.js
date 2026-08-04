let mediaRecorder = null;
let audioChunks = [];
let isRecording = false;

/**
 * Start recording from the microphone.
 */
export async function startRecording() {

    if (isRecording) {
        return;
    }

    const stream = await navigator.mediaDevices.getUserMedia({
        audio: true,
    });

    mediaRecorder = new MediaRecorder(stream);

    audioChunks = [];

    mediaRecorder.ondataavailable = (event) => {

        if (event.data.size > 0) {
            audioChunks.push(event.data);
        }

    };

    mediaRecorder.start();

    isRecording = true;

    console.log("🎤 Recording started");
}

/**
 * Stop recording and return the recorded audio.
 */
export function stopRecording() {

    return new Promise((resolve) => {

        if (!mediaRecorder) {
            resolve(null);
            return;
        }

        mediaRecorder.onstop = () => {

            const audioBlob = new Blob(audioChunks, {
                type: "audio/webm"
            });

            isRecording = false;

            console.log("🛑 Recording stopped");

            resolve(audioBlob);

        };

        mediaRecorder.stop();

    });

}

export function recording() {
    return isRecording;
}

export async function getAudioBlob() {

    return await stopRecording();

}