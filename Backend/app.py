import base64
from flask import Flask, request, send_file
from flask_cors import CORS
from generator import *

app = Flask(__name__)
CORS(app)

generator = Generator(MODEL_FILEPATH)
UPLOAD_FOLDER_PATH = "Uploaded_files"


@app.route('/generate_melody', methods=['POST'])
def generate_melody():
    print("Generating Melody...")

    data_uri = request.json.get('data')
    print(f"data_uri:{data_uri}")

    _, base64_data = data_uri.split(',', 1)
    print(f"base 64 data: {base64_data}")
    decoded_data = base64.b64decode(base64_data)
    print("Decoded base 64 data.")
    file_path = UPLOAD_FOLDER_PATH+"/melody.mid"
    with open(file_path, "wb") as fp:
        print("Saving File...")
        fp.write(decoded_data)
    print(f"file saved to {file_path}")

    supplied_seed, reverse_transposition = preprocess_api(file_path)
    generated_melody = generator.generate_melody(seed=supplied_seed, number_of_steps=400,
                                                 max_sequence_length=SEQUENCE_LENGTH, temperature=0.7)

    # un-transpose melody to match key of original user-submitted melody
    generated_melody_in_original_key = undo_transpose(generated_melody, reverse_transposition)

    print("Melody Generated.")
    generator.save_melody_as_midi(melody=generated_melody_in_original_key, path=MIDI_OUTPUT_PATH)
    print("Melody saved, sending back to Frontend.")

    return send_file(MIDI_OUTPUT_PATH, download_name="melody.mid")


if __name__ == '__main__':
    app.run()
