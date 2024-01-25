from flask import Flask, request, send_file
from flask_cors import CORS
from generator import *
import os

app = Flask(__name__)
# CORS(app)

generator = Generator(MODEL_FILEPATH)
UPLOAD_FOLDER_PATH = "Uploaded_files"

@app.route('/generate_melody', methods=['POST'])
def generate_melody():
    print("Generating Melody...")
    file = request.files['file']
    filename = file.filename
    file_path = os.path.join(UPLOAD_FOLDER_PATH, filename)

    file.save(file_path)

    supplied_seed = preprocess_API(file_path)
    generated_melody = generator.generate_melody(seed=supplied_seed, number_of_steps=400,
                                                 max_sequence_length=SEQUENCE_LENGTH, temperature=0.7)
    print("Melody Generated.")
    generator.save_melody_as_midi(melody=generated_melody, path=MIDI_OUTPUT_PATH)
    print("Melody saved, sending back to Frontend.")

    return send_file(MIDI_OUTPUT_PATH, download_name="melody.mid")


if __name__ == '__main__':
    app.run()
