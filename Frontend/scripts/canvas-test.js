// THANK YOU VERY MUCH TO G200KG FOR MAKING THIS FRONTEND POSSIBLE!
// https://github.com/g200kg/webaudio-pianoroll
// Lots of love, Tom <3


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
pianoRoll.xrange = 64; //number of ticks available to play/set.
pianoRoll.yrange = 24; //set number of available notes to play
pianoRoll.grid = 8; // setting grid size for grid to be consistent with note length(s).

pianoRoll.markstart = 0;
pianoRoll.markend = 64;
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

// ------ Playhead ------
pianoRoll.preload = 2; //preload audio
pianoRoll.redraw();



//       ------ Code! -------

let temperature = 0.6 //set default temperature to 0.6
let isPlaying = false; //set default playing state to false

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
    console.log("Changed window size.")
    pianoRoll.redraw();
}

// Handle temperature slider
let slider = document.getElementById("temp-slider"); //fetch slider object
let output = document.getElementById("temp-number"); //fetch output text
output.innerHTML = String(Number(slider.value)/100); // Display the default slider value
slider.oninput = function () { output.innerHTML = String(Number(this.value/100)); temperature = Number(this.value/100) } //update readout whenever it's changed.

// Handle play/pause button
document.getElementById("play-button").addEventListener("click", () => playPause()) //add event listener to play/pause button
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


//TODO: Change this callback function to play a piano-like sound.
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
function playMelody() {
    actx.resume();
    pianoRoll.play(actx, Callback);
}


// Handle Reset button
document.getElementById("clear-button").addEventListener("click", clearBoard) //add event listener to board clearing button
function clearBoard(){
    pianoRoll.setMMLString("");
    pianoRoll.cursor = 0;
    temperature = 0.6;
    slider.value = 60;
    output.innerHTML = "0.6";


    if(isPlaying){
       pianoRoll.stop();
        actx.suspend();
        document.getElementById("play-button").innerHTML = "▶";
        isPlaying = false;
    }

}

// Handle Generate button
document.getElementById("generate-button").addEventListener("click", expandMelody) //add event listener to generate button
function expandMelody(){
    let mml = pianoRoll.getMMLString();
    console.log(mml)
    //TODO: Find a way to convert mml to midi
    //TODO: Send Midi to backend to generate a new melody

}
