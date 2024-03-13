# <u>LSTMusic</u>
## What is LSTMusic?

---
My Final year University Project.

Takes a melody, does a bit of AI magic, and spits it out quite a bit longer!

## Usage

---
Visit [LSTMusic]().

I've aimed for the site to be as self-explanatory as possible, but here's a quick guide if you're struggling:
1. Input a melody to the site's Piano roll.
2. Click the 'Extend' button.
3. Wait for the site to extend your melody.
4. View and play using your extended melody using the playback buttons.

## Special Thanks
Turns out other people are much better at making certain things than I am, despite my best efforts.


This project would not have been possible without the following libraries, frameworks and online resources:
### Frontend
- [GitHub Pages](https://pages.github.com/) - A free hosting service provided by GitHub.
- [WebAudio-PianoRoll](https://github.com/g200kg/webaudio-pianoroll) - A JavaScript library for creating interactive piano roll interfaces.
- [html-midi-player](https://github.com/cifkao/html-midi-player) - A JavaScript library for playing & displaying MIDI files in the browser.


### Backend
- [TensorFlow](https://www.tensorflow.org/) - An open-source machine learning library which I've used.
- [Magenta](https://magenta.tensorflow.org/) - A research project exploring the role of machine learning as a tool, and the primary inspiration of this project.
- 

### Everything in-between
- [Flask](https://flask.palletsprojects.com/en/2.0.x/) - The Python web framework used.

## FAQ.

---

### Where does the name 'LSTMusic' come from?
LSTMusic derives its name from LSTM, which stands for Long Short-Term Memory, a type of Recurrent Neural Network used in this project for music generation.

### What is the purpose of this project?
This project serves as a demonstration of the skills and knowledge which I have picked up during my time at University.
\
This project has also given me a chance to pick up new skills related to web development, including 
frontend dev, backend development, API design, and deployment.
us, I believe that this project is a good reflection of the skills and knowledge I have acquired during my course.

## Limitations

---

- Polyphonic melodies aren't supported, so songs with only one note at a time can be inputted and extended.
- Generated music is not guaranteed to be musically coherent or pleasant to listen to.
- Generated music has a heavy bias towards classical music, as the model was trained on a dataset of classical music. 
- The site is not optimised for mobile devices.
- The site is not optimised for screen readers or other assistive technologies.
- There is a shocking lack of security features, so please don't break anything. ❤️