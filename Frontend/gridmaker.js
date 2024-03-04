import MidiWriter from 'https://cdn.skypack.dev/midi-writer-js';

var board = []; //Initialise board
const rows = 24; //Number of timings working with
const columns = 16; //Number of semitones we're working with
const keys = ["A", "A#", "B", "C", "C#", "D", "D#", "E", "F", "F#", "G", "G#"].reverse() //reversing because i'm lazy and can't be bothered to retype the keys out
const keys_audio = ["A", "A#", "B", "C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A1", "A#1", "B1", "C1", "C#1", "D1", "D#1", "E1", "F1", "F#1", "G1", "G#1"].reverse()
const midiEncodings = {0:"G#4", 1:"G4", 2:"F#4",3:"F4", 4:"E4",5:"D#4",6:"D4",7:"C#4",8:"C4",9:"B3",10:"A#3",11:"A3",12:"G#3",13:"G3",14:"F#3",15:"F3",16:"E3",17:"D#3",18:"D3",19:"C#3",20:"C3",21:"B2",22:"A#2",23:"A2"}
var clickedTiles = []; //Internal boolean representation.
var bpm = 120;
let currentCol = 0;

//start game boilerplate
window.onload = function () {
    startGame();
}


/**
 * Starts the game by adding event listeners, creating interactive elements, populating board 
 */
function startGame() {

    // giving functionality to buttons & slider
    document.getElementById("generate-button").addEventListener("click", () => sendGenerator() ) //add event listener to generate.
    document.getElementById("play-button").addEventListener("click", () => playMusic(clickedTiles)) //add event listener to play inputted notes.
    document.getElementById("clear-button").addEventListener("click", clearBoard) //add event listener to board clearing button




    //BPM Slider
    var slider = document.getElementById("bpm-slider"); //fetch slider object
    var output = document.getElementById("bpm-number"); //fetch output text
    output.innerHTML = slider.value; // Display the default slider value
    slider.oninput = function () { output.innerHTML = this.value; bpm = this.value } //update readout whenever it's changed.

    // Creating Piano Roll by making a 2d martix of interactive divs, each with an event listener for clicking which swaps visuals, as well as
    // playing any music.

    for (let r = 0; r < rows; r++) {
        let row = []; //create row 
        let clickedRow = []; //create clicked row.

        let note = keys[r % keys.length]; //get note of column.

        let htmlRow = document.createElement("div"); //create row div
        htmlRow.id = "row-" + note; //set ID of row div

    
        for (let c = 0; c < columns; c++) {

            let tile = document.createElement("div"); //create tile div

            tile.id = r.toString() + "-" + c.toString(); //give tile it's name: <div id="r-c"></div>
            tile.addEventListener("click", clickTile); //add clickTile event listener
            tile.addEventListener("click", function () { playNote(keys_audio[r]); }) //add audio playback event listener
            htmlRow.appendChild(tile); //add tile to html row
            row.push(tile); //add tile to js row
            clickedRow.push(false); //push item to 2D boolean grid.
        }
        board.push(row); //push row to 2D div grid outside of function.
        clickedTiles.push(clickedRow); //push row to 2D boolean grid

        document.getElementById("roll").append(htmlRow);

    }

}


/**
 * Function which handles changes when a Tile is clicked (changing GUI, calling note functions)
 */
function clickTile() {

    let tile = this; //get tile that was clicked
    let tileName = tile.id;
    let [row, col] = tileName.split("-").map(x => +x); //parse row and column 


    clickedTiles[row][col] = !clickedTiles[row][col];

    if (tile.className == "") {
        tile.className = "clicked"

    }
    else if (tile.className == "clicked") {
        tile.classList.remove("clicked")
    }

}

/**
 * Function for playing a provided note through the browser.
 * @param {string} note - the note that shal be played 
 */
function playNote(note) {
    const audio = document.getElementById(note); //get note audio from html div
    let noteSpeed = bpm / 120; //calculate playback rate.
    //console.log("played note" + note + " at rate " + noteSpeed) //debugging print statement
    audio.playbackRate = noteSpeed //Changing speed of playback
    audio.play(); //play audio
}



/**
 * Clears the visual board and the js board representation.
 * @returns the state which the board was in before clearing.
 */
function clearBoard() {


    //figuring this out was a pain in the ass, Turns out 2D arrays don't deep copy easily in JS.
    let boardDupe = JSON.parse(JSON.stringify(clickedTiles)); //stringify and parse 2D array to create a deep copy rather than a shallow copy.

    //set JS board to false.
    for (let i = 0; i < clickedTiles.length; i++) {
        for (let j = 0; j < clickedTiles[0].length; j++) {
            clickedTiles[i][j] = false;
        }
    }

    //clear visual board 
    for (let y = 0; y < board.length; y++) {
        for (let x = 0; x < board[0].length; x++) {
            if (board[y][x].className == "clicked") {
                board[y][x].classList.remove("clicked")
            }
        }
    }

    return boardDupe;
}


/**
 * Function to encode the user's inputted melody into MIDI.
 * @param {Boolean[][]} boolBoard The user's inputted melody in the form of the boolean matrix which the site uses. 
 * @returns The URI of the generated MIDI file
 */
function encodeMusic(boolBoard) {

    const track = new MidiWriter.Track(); //create new MIDI Track
    track.addEvent(new MidiWriter.ProgramChangeEvent({instrument: 1})); //Change instrument to honky tonk piano
    track.setTempo(bpm); 
    const transposedBoolArray = boolBoard[0].map((_, colIndex) => boolBoard.map(row => row[colIndex])); //Transposes array to ensure notes are played horizontally along the piano roll rather than vertically

    //Collects notes a each time and write them to file
    for (let line = 0; line < transposedBoolArray.length; line++) {
        
        let notesToAdd = [];

        for (let note = 0; note < transposedBoolArray[line].length; note++) {
            
            if(transposedBoolArray[line][note]){
                notesToAdd.push(midiEncodings[note]);
            }
            

        }

        //add any pauses
        if(notesToAdd.length === 0){
        
        }
        else{
        //add notes of this 'line' to the midi track.
        track.addEvent(new MidiWriter.NoteEvent({ pitch: notesToAdd, duration: '4' }));
        }
    }

    const write = new MidiWriter.Writer(track);
    return write.dataUri();

}

function download(uri, name){
    let link = document.createElement("a");
    link.download = name;
    link.href = uri;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
}

function playMusic(boolBoard) {

    currentCol = 0;

    //transpose array so that each 'timing'
    const transposedBoolArray = boolBoard[0].map((_, colIndex) => boolBoard.map(row => row[colIndex])); //dear god this took a while to figure out

    /**
     * Plays a 'line' of notes and calls the next line recursively.
     */
    function playSlide() {

        clearTimeout(playSlide)

        const slide = transposedBoolArray[currentCol];
        for (let i = 0; i < slide.length; i++) {
            if (slide[i]) {
                playNote(keys_audio[i]);
            }
        }
        currentCol++;
        if (currentCol < transposedBoolArray.length) {
            setTimeout(playSlide, 60000 / bpm);
        }
        else {
            currentCol = 0
        }
        //Thank you Layton for helping me massively with the Timings side of This. Javascript Is Weird...
    }

    playSlide();
}




/**
 * Sends Inputted melody to the backend. (needs changing and updating)
 * @param {string} songData - the data to be sent to the backend.
 * @returns the response from the backend in JSON format. 
 */
async function sendFile(songData){
    console.log("Sending song to API");
    try{
        const response = await fetch('http://127.0.0.1:5000/generate_melody',
            {   method: 'POST',
                headers: 
                    {
                        'Content-Type': 'text/plain',
                    },
                body: songData
            }
        )
    }
    catch(error){
        console.log("Error while trying to fetch data.: " + error)
    }

    
    console.log("Response Received")
    
    
    
}


/**
 * Sends Inputted melody to the backend. (needs changing and updating)
 */
async function sendGenerator() {
    
    let b64MidiOutput = String(encodeMusic(clickedTiles));
    sendMessageAndDownload()
    
     
    // let response = await sendFile(b64MidiOutput)
    // console.log('Response is: ' + response)
       
}
    

async function sendMessageAndDownload(base64MidiOutput) {
    const encodedMidi = encodeMusic(clickedTiles);

    //send initial request
    const response = await fetch('http://127.0.0.1:5000/generate_melody', {
        method: 'POST',
        headers: {'Content-Type': 'text/plain',},
        body: encodedMidi
        });

    if (!response.ok){
        throw new Error('Network response was not ok');
    }

    // Get Processing task ID used in file name).
    const responseText = await response.text();
    const responseObject = JSON.parse(responseText);
    const responseMessages = responseObject.message.split(';');
    const message = responseMessages[0];
    const songId = responseMessages[1];
    console.log(message)
    console.log(songId)
    
    // Periodically check processing status
  const pollForCompletion = setInterval(async () => {
    const statusResponse = await fetch(`/check_status/${taskId}`);

    if (statusResponse.ok) {
      const status = await statusResponse.text();
      console.log(status)
      if (status === 'complete') {
        clearInterval(pollForCompletion); 
        console.log("Song is ready to download")
        //TODO: Download the file

      }  else { 
        // Update progress UI?
      }
    }
  }, 2000); // Check every 2 seconds

}
