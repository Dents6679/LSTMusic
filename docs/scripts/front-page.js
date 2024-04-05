// THANK YOU VERY MUCH TO G200KG FOR MAKING THIS FRONTEND POSSIBLE!
// https://github.com/g200kg/webaudio-pianoroll

// const BACKEND_URL = "http://127.0.0.1:5000"
const BACKEND_URL = "https://dents6679.com/"

// -- Setting up Piano Roll --
const pianoRoll = document.getElementById("piano-roll");
let width = window.innerWidth;
let height = window.innerHeight;


//     ------ Sizing ------
pianoRoll.width = width * 0.8;
pianoRoll.height = height * 0.5;
pianoRoll.kbwidth = width * 0.08; //width of the keyboard



//      ------ Technical ------
pianoRoll.editmode = "dragmono" //ensure that the user can only draw one note at a time
pianoRoll.xrange = 32; //number of ticks available to play/set.
pianoRoll.yrange = 24; //set number of available notes to play
pianoRoll.grid = 4; // setting grid size for grid to be consistent with note length(s).
pianoRoll.timebase = 8 // Set timebase to 8. minimum note length is 1/8th of a note.
pianoRoll.loop = 0; //set loop to false by default

pianoRoll.tempo = 120; //set tempo to 120 by default

pianoRoll.markstart = 0;
pianoRoll.markend = 32;
pianoRoll.xruler = height * 0.02;
pianoRoll.yruler = width * 0.02;

pianoRoll.markstartoffset = -400; // remove start offset marker
pianoRoll.markendoffset = 400; // remove end offset marker



//       ------ Colouring ------
// Grid colouring
pianoRoll.collt = "#323232" // score background (light)
pianoRoll.coldk = "#282828" // score background (dark)
pianoRoll.colgrid = "#666" // grid color

// Note colouring
pianoRoll.colnote = "#ADF9C2" // note color
pianoRoll.colnotesel = "#324938" // selected note colour
pianoRoll.colnoteborder = "#202d23" // Note border colour

pianoRoll.colrulerbg = "#1e1e1e" // ruler background
pianoRoll.colrulerborder = "#1e1e1e00" // ruler border
pianoRoll.colrulerfg = "#fff" // ruler text

// ------  ------
pianoRoll.preload = 2; //preload audio
pianoRoll.redraw();
pianoRoll.style.display = "inline"



//       ------ Code -------




let temperature = 0.6 //set default temperature to 0.6
let isPlaying = false; //set default playing state to false
let outputLength = 4; //set default output length to 4 bars
let timebase= 480;
let actx= new AudioContext();


//Handle window resizing
window.addEventListener('resize', updateRollSize);
function updateRollSize() {
    width = window.innerWidth;
    height = window.innerHeight;
    pianoRoll.width = width * 0.8;
    pianoRoll.height = height * 0.5;
    pianoRoll.kbwidth = width * 0.08;
    pianoRoll.redraw();
}

// Handle temperature slider
let tempSlider = document.getElementById("temp-slider"); //fetch temp slider object
let tempOutput = document.getElementById("temp-number"); //fetch temp output text
tempOutput.innerHTML = String(Number(tempSlider.value)/100); // Display the default temp slider value
tempSlider.oninput = function () {
                                            tempOutput.innerHTML = String(Number(this.value/100));
                                            temperature = Number(this.value/100)
                                       } //update readout whenever it's changed.

// Handle length slider
let lenSlider = document.getElementById("len-slider"); //fetch slider object
let lenOutput = document.getElementById("len-number"); //fetch output text
lenOutput.innerHTML = lenSlider.value; // Display the default slider value
lenSlider.oninput = function () {
                                        lenOutput.innerHTML = this.value;
                                        outputLength = this.value;
                                        } //update readout whenever it's changed.

// Handle tempo slider
let tempoSlider = document.getElementById("bpm-slider"); //fetch slider object
let tempoOutput = document.getElementById("bpm-number"); //fetch output text
tempoOutput.innerHTML = tempoSlider.value; // Display the default slider value
tempoSlider.oninput = function () { tempoOutput.innerHTML = this.value; pianoRoll.tempo = this.value } //update readout whenever it's changed.
pianoRoll.tempo = tempoSlider.value;
//TODO: Might be worth preventing the user from changing the tempo while the song is playing.


// Handle play/pause button & space bar presses.
document.getElementById("play-button").addEventListener("click", () => playPause()) //add event listener to play/pause button

document.addEventListener("keydown", debounce(function(event) {
    if (event.code === "Space") {
        playPause();
    }
}, 200)); //debounce spacebar presses to prevent accidental double presses

/**
 * Debounces a function to prevent accidental double presses.
 * @param func The function to debounce
 * @param delay The delay in ms to debounce the function by.
 * @returns {(function(): void)|*}
 */
function debounce(func, delay) {
    let debounceTimer;
    return function() {
        const context = this;
        const args = arguments;
        clearTimeout(debounceTimer);
        debounceTimer = setTimeout(() => func.apply(context, args), delay);
    }
}

/**
 * Plays/pauses the melody.
 */
function playPause(){

    if(isPlaying){
        document.getElementById("play-button").innerHTML = "▶";
        pianoRoll.stop();
        actx.suspend();
    }

    else if(!isPlaying){
        document.getElementById("play-button").innerHTML = "❚❚";
        playMelody();

    }

    isPlaying = !isPlaying;
}




//TODO: Change this callback function to play a piano-like sound?
/**
 * Callback function for playing notes.
 * @param ev - event object
 */
function Callback(ev){
	var o=actx.createOscillator();
	var g=actx.createGain();
	o.type="sawtooth";
	o.detune.value=(ev.n-69)*100;

	g.gain.value=0;
	o.start(actx.currentTime);
	g.gain.setTargetAtTime(0.2,ev.t,0.005);
	g.gain.setTargetAtTime(0,ev.g,0.1);
	o.connect(g);
	g.connect(actx.destination);
}

/**
 * Plays the melody from the piano roll.
 */
function playMelody() {
    actx.resume();
    pianoRoll.play(actx, Callback);
}


// Handle Reset button
document.getElementById("clear-button").addEventListener("click", clearRoll) //add event listener to board clearing button
/**
 * Clears the piano roll of all notes.
 */
function clearRoll(){
    pianoRoll.setMMLString("");
    pianoRoll.cursor = 0;
    temperature = 0.6;
    tempSlider.value = 60;
    tempOutput.innerHTML = "0.6";


    if(isPlaying){
       pianoRoll.stop();
        actx.suspend();
        document.getElementById("play-button").innerHTML = "▶";
        isPlaying = false;
    }

}

// Handle Back to start Button
document.getElementById("back-button").addEventListener("click", backToStart)

/**
 * Resets the cursor to the start of the melody.
 */
function backToStart(){
    pianoRoll.cursor = 0;
    if(isPlaying){
        pianoRoll.stop();
        actx.suspend();
        document.getElementById("play-button").innerHTML = "▶";
        isPlaying = false;
    }

}


// Handle Generate button
document.getElementById("generate-button").addEventListener("click", requestMelodyExpansion) //add event listener to generate button

/**
 * Sends a request to the backend to expand the melody.
 */
async function requestMelodyExpansion(){
    const mml = pianoRoll.getMMLString();



    const sequenceData = pianoRoll.sequence;
    const stringifiedSequenceData = JSON.stringify(sequenceData);


    const requestBody = stringifiedSequenceData+ ";;;" + temperature + ";;;" + outputLength;
    try {
        const response = await fetch(BACKEND_URL + '/generate_melody_new',
            {
                method: 'POST',
                headers:
                    {
                        'Content-Type': 'text/plain',
                    },
                body: requestBody
            }
        )
        // Get response data and redirect to waiting page
        const responseText = await response.text();
        const responseObject = JSON.parse(responseText);
        const responseMessages = responseObject.message.split(';');
        const songId = responseMessages[1];
        window.location.href = "waiting.html?songId=" + songId;

        if (!response.ok){
        throw new Error('Network response was not ok');
        }
    }
    catch(error) {
        console.error('Fetch request failed:', error);
        window.location.href = "error.html?errorId=1"; // Redirect to error.html with errorId=1
    }






}

//Handle "About" button
const popupOverlay = document.getElementById('popupOverlay');
const closePopupButton = document.getElementById('close-button');

document.getElementById("about-text").addEventListener("click", () => openPopup())



//open popup fn
function openPopup() {
    popupOverlay.style.display = 'block';
}

//close popup fn
function closePopup() {
    popupOverlay.style.display = 'none';
}


// Close about section when the close button is clicked
closePopupButton.addEventListener('click', closePopup);

//close about section when clicking outside the popup content
popupOverlay.addEventListener('click', function (event) {
    if (event.target === popupOverlay) {
        closePopup();
    }
});

