
songId = location.search.split('songId=')[1];
console.log(`Song id is ${songId}`)
// Poll the server every 2 seconds to check if the song is ready to download.
const pollForCompletion = setInterval(async () => {
    const statusResponse = await fetch(`http://127.0.0.1:5000/check_status/${songId}`);

    if (statusResponse.ok) {
      const status = await statusResponse.text();
      console.log(status)
      if (status === 'complete') {
        clearInterval(pollForCompletion); 
        console.log("Song is ready to download")
        //TODO: Download the file

      }  else { 
        console.log("Song is still processing...")
      }
    }
  }, 2000); // Check every 2 seconds