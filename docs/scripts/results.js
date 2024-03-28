// const BACKEND_URL = "http://127.0.0.1:5000"
const BACKEND_URL = "https://dents6679.pythonanywhere.com/"
const songId = location.search.split('song_id=')[1];

//Add download functionality to the download button
document.getElementById('download-button').addEventListener('click', function() {
    // const downloadUrl = BACKEND_URL + "/download_file/" + songId;
    // window.open(downloadUrl, '_blank');
    const link = document.createElement("a");

    link.setAttribute("download", "melody.mid");
    link.href = BACKEND_URL + "/download_file/" + songId;
    document.body.appendChild(link);
    link.click();
    link.remove();
});






function loadAndPlayMidi() {

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