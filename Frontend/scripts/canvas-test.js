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

pianoRoll.markstart = 0;
pianoRoll.markend = 32;
pianoRoll.xruler = 0;
pianoRoll.yruler = width * 0.02;


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


