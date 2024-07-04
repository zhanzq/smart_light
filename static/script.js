let audioChunks = [];
let mediaRecorder;
let audioContext = new (window.AudioContext || window.webkitAudioContext)();

document.getElementById('recordButton').addEventListener('click', async () => {
    console.log('Recording start');
    const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
    mediaRecorder = new MediaRecorder(stream, { mimeType: 'audio/webm' });

    mediaRecorder.ondataavailable = event => {
        audioChunks.push(event.data);
    };

    mediaRecorder.onstop = async () => {
        console.log('Recording stopped');
        const audioBlob = new Blob(audioChunks, { type: 'audio/webm' });
        const arrayBuffer = await audioBlob.arrayBuffer();
        const audioBuffer = await audioContext.decodeAudioData(arrayBuffer);
        const resampledBuffer = await resampleAudioBuffer(audioBuffer, 16000);
        const wavBlob = createWavBlob(resampledBuffer);

        const audioUrl = URL.createObjectURL(wavBlob);
        document.getElementById('audioPlayback').src = audioUrl;

        // 上传WAV文件到服务器并获取文件路径
        const formData = new FormData();
        formData.append('audio', wavBlob, 'recording.wav');

        try {
            const uploadResponse = await fetch('/upload', {
                method: 'POST',
                body: formData,
            });

            if (uploadResponse.ok) {
                const uploadResult = await uploadResponse.json();
                const wavPath = uploadResult.path;
                console.log("upload finished");
                // 调用do_asr并显示结果
                const transcript = await doAsr(wavPath);
                const room_info = await doNLU(transcript);
                const room_obj = JSON.parse(room_info);
                document.getElementById('transcript').value = room_info;
                document.getElementById("living_room").src = room_obj.客厅.image_path;
                document.getElementById("bathroom").src = room_obj.卫生间.image_path;
                document.getElementById("bedroom").src = room_obj.卧室.image_path;
                document.getElementById("dining_room").src = room_obj.餐厅.image_path;
            } else {
                console.error('Failed to upload audio file');
            }
        } catch (error) {
            console.error('Error during upload:', error);
        }


        audioChunks = [];
        document.getElementById('recordButton').disabled = false;
        document.getElementById('stopButton').disabled = true;
    };

    mediaRecorder.start();
    document.getElementById('recordButton').disabled = true;
    document.getElementById('stopButton').disabled = false;
});

document.getElementById('stopButton').addEventListener('click', () => {
    audioChunks = [];
    mediaRecorder.stop();
    document.getElementById('recordButton').disabled = false;
    document.getElementById('stopButton').disabled = true;
});

function createWavBlob(audioBuffer) {
    const numberOfChannels = audioBuffer.numberOfChannels;
    const sampleRate = audioBuffer.sampleRate;
    const length = audioBuffer.length * numberOfChannels * 2 + 44;
    const wavBuffer = new ArrayBuffer(length);
    const view = new DataView(wavBuffer);

    // RIFF chunk descriptor
    writeString(view, 0, 'RIFF');
    view.setUint32(4, 36 + audioBuffer.length * numberOfChannels * 2, true);
    writeString(view, 8, 'WAVE');

    // FMT sub-chunk
    writeString(view, 12, 'fmt ');
    view.setUint32(16, 16, true);
    view.setUint16(20, 1, true);
    view.setUint16(22, numberOfChannels, true);
    view.setUint32(24, sampleRate, true);
    view.setUint32(28, sampleRate * numberOfChannels * 2, true);
    view.setUint16(32, numberOfChannels * 2, true);
    view.setUint16(34, 16, true);

    // Data sub-chunk
    writeString(view, 36, 'data');
    view.setUint32(40, audioBuffer.length * numberOfChannels * 2, true);

    // Write PCM samples
    let offset = 44;
    for (let i = 0; i < audioBuffer.length; i++) {
        for (let channel = 0; channel < numberOfChannels; channel++) {
            const sample = audioBuffer.getChannelData(channel)[i];
            view.setInt16(offset, sample * 0x7FFF, true);
            offset += 2;
        }
    }

    return new Blob([view], { type: 'audio/wav' });
}

function writeString(view, offset, string) {
    for (let i = 0; i < string.length; i++) {
        view.setUint8(offset + i, string.charCodeAt(i));
    }
}

async function resampleAudioBuffer(audioBuffer, targetSampleRate) {
    const numberOfChannels = audioBuffer.numberOfChannels;
    const sourceSampleRate = audioBuffer.sampleRate;
    const lengthResampled = Math.round(audioBuffer.length * targetSampleRate / sourceSampleRate);
    const offlineContext = new OfflineAudioContext(numberOfChannels, lengthResampled, targetSampleRate);

    const bufferSource = offlineContext.createBufferSource();
    bufferSource.buffer = audioBuffer;
    bufferSource.connect(offlineContext.destination);
    bufferSource.start(0);

    const renderedBuffer = await offlineContext.startRendering();
    return renderedBuffer;
}

async function doAsr(wavPath) {
    const response = await fetch('/asr', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ path: wavPath })
    });

    const result = await response.json();
    console.log(result);
    return result.transcript;
}

async function doNLU(text) {
    const response = await fetch('/nlu', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ query: text })
    });

    const result = await response.json();
    console.log(result);
    return result.room_info;
}

// // 使用 JavaScript 隐藏元素
// document.getElementById('audioPlayback').style.display = 'none';
// document.getElementById('transcript').style.display = 'none';