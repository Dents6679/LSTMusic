const BACKEND_URL = "http://127.0.0.1:5000"
function getQueryParam(name) {
    const urlParams = new URLSearchParams(window.location.search);
    return urlParams.get(name);
}

function loadAndPlayMidi() {
    const songId = getQueryParam("song_id");
    if (songId) {
        const midiUrl = BACKEND_URL + "/download_file/" + songId;
        console.log("Midi URL is:" + midiUrl)

        document.getElementById('midi-player-1').src = midiUrl;
        document.getElementById('midi-visualizer-1').src = midiUrl;

        document.getElementById('midi-player-2').src = midiUrl;
        document.getElementById('midi-visualizer-2').src = midiUrl;

        document.getElementById('midi-player-3').src = midiUrl;
        document.getElementById('midi-visualizer-3').src = midiUrl;
        
    } else {
        // Handle the case where there's no song_id in the query string
        console.error("No song_id provided in the URL");
    }
}

// Call the function to load the MIDI file
loadAndPlayMidi();