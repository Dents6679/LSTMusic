import {BACKEND_URL} from './front-page.js';
let songId = location.search.split('songId=')[1];
let attempts = 0;


document.getElementById('generation-id').textContent = songId; 

// Poll the server every 2 seconds to check if the song is ready to download.
const pollForCompletion = setInterval(async () => {
    const statusResponse = await fetch(BACKEND_URL + '/check_status/' + songId);

    attempts++;
    if (statusResponse.ok) {
      const status = await statusResponse.text();
      console.log(status)
      if (status === 'complete') {
        clearInterval(pollForCompletion); 
        console.log("Song is ready to download")
        window.location.href = "/results.html?song_id=" + songId;

      }  else { 
        console.log("Song is still processing...")
      }
    }

    if (attempts > 15) {
      clearInterval(pollForCompletion);
      console.log("Song took too long to process.")
      window.location.href = "/frontend/error.html";
    }

  }, 2000); // Check every 2 seconds