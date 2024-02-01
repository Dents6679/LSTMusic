import base64
from flask import Flask, request, send_file, jsonify
from flask_cors import CORS
from generator import Generator, streamify_melody, MIDI_OUTPUT_PATH
from training import MODEL_FILEPATH
from preprocess import SEQUENCE_LENGTH
from api_tools import preprocess_api, undo_transpose, GenerationError
import time

app = Flask(__name__)
CORS(app)

generator = Generator(MODEL_FILEPATH)
UPLOAD_FOLDER_PATH = "Uploaded_files"


@app.route('/generate_melody', methods=['POST', 'GET'])
def generate_melody():
    # POST for sending melody
    if request.method == 'POST':


        try:
            data_uri = str(request.data)
        except IOError as e:
            print(f"IOError: Failed to find data from fetch request: {e}")



        try:
            _, base64_data = data_uri.split(',', 1)
            base64_data = base64_data[:-1] # Removes leftover ' from API
            decoded_data = base64.b64decode(base64_data)

            file_path = UPLOAD_FOLDER_PATH+"/melody.mid"
            with open(file_path, "wb") as fp:
                fp.write(decoded_data)
        except TypeError as e:
            print(f"Failed Decoding Base64 File: {e}")

        print("Generating Melody, please wait...")
        try:
            supplied_seed, reverse_transposition = preprocess_api(file_path)
            generated_melody = generator.generate_melody(seed=supplied_seed, number_of_steps=400,
                                                         max_sequence_length=SEQUENCE_LENGTH, temperature=0.7)
        except Exception:
            print(f"Failed generating Melody through LSTM.")


        try:
            generated_melody_stream = streamify_melody(generated_melody)
            untransposed_melody = undo_transpose(generated_melody_stream, reverse_transposition)
            untransposed_melody.write("midi", MIDI_OUTPUT_PATH)
        except IOError:
            print("Failed MIDI conversion & saving.")

        print("Generation and post-processing complete, song has been saved..")


        message = {'status': 200,
                   'message': 'okay'}

        resp = jsonify(message)
        resp.status_code = 200
        print(resp)
        time.sleep(3)

        return resp


@app.route('/show_melody', methods=['GET'])
def get_file():
    if request.method == 'GET':
        message = {'status': 200,
                   'message': 'okay'}

        resp = jsonify(message)
        resp.status_code = 200

        return send_file(MIDI_OUTPUT_PATH, 'melody.mid')


if __name__ == '__main__':
    app.run()
