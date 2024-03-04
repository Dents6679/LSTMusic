import base64
from flask import Flask, request, send_file, jsonify, make_response, g
from flask_cors import CORS
from generator import Generator, streamify_melody, MIDI_OUTPUT_PATH
from training import MODEL_FILEPATH
from preprocess import SEQUENCE_LENGTH
from api_tools import preprocess_api, undo_transpose, GenerationError, has_melody_generated
import time
import copy

app = Flask(__name__)
CORS(app)

generator = Generator(MODEL_FILEPATH)
UPLOAD_FOLDER_PATH = "Uploaded_files"



@app.route('/generate_melody', methods=['POST', 'GET'])
def generate_melody():

    # POST for sending melody
    file_number = str(int(time.time()))
    if request.method == 'POST':
        try:
            data_uri = str(request.data)
        except IOError as e:
            print(f"IOError: Failed to find data from fetch request: {e}")
            return jsonify({'status': 400, 'message': 'Failed to find data from fetch request.'})

        try:
            _, base64_data = data_uri.split(',', 1)
            base64_data = base64_data[:-1] # Removes leftover ' from API
            decoded_data = base64.b64decode(base64_data)


            file_path = f"{UPLOAD_FOLDER_PATH}/melody_{file_number}.mid"
            g.file_path = copy.copy(file_path)
            g.file_number = copy.copy(file_number)

            with open(file_path, "wb") as fp:
                fp.write(decoded_data)
        except TypeError as e:
            print(f"Failed Decoding Base64 File: {e}")
            return jsonify({'status': 400, 'message': 'Failed to decode base64 file.'})


        response_message = f"Generation request received.;{file_number}"

        resp = jsonify({'status': 200, 'message': response_message})
        resp.status_code = 200

        return resp


@app.teardown_request
def teardown_request(response):
    if request.path == '/generate_melody':
        file_path = getattr(g, 'file_path', None)
        file_number = getattr(g, 'file_number', None)

        if file_path is None or file_number is None:
            print("Error in after_request: file_path or file_number is None.")

        print("Generating Melody, please wait...")
        try:
            supplied_seed, reverse_transposition = preprocess_api(file_path)
            generated_melody = generator.generate_melody(seed=supplied_seed, number_of_steps=400,
                                                         # TODO: Make this a variable changeable from the frontend.
                                                         max_sequence_length=SEQUENCE_LENGTH, temperature=0.7)
        except Exception:
            print(f"Failed generating Melody through LSTM.")
            return jsonify({'status': 500, 'message': 'Failed to generate melody.'})

        try:
            output_path = f"Generated Melodies/extended_melody_{file_number}.mid"

            generated_melody_stream = streamify_melody(generated_melody)
            untransposed_melody = undo_transpose(generated_melody_stream, reverse_transposition)
            untransposed_melody.write("midi", output_path)
        except IOError:
            print("Failed MIDI conversion & saving.")
            return jsonify({'status': 500, 'message': 'Failed to save melody.'})

        print("Generation and post-processing complete, song has been saved..")

    return response


@app.route('/check_status/<song_id>', methods=['POST', 'GET'])
def check_status(song_id):
    print(f"Checking Status of Generation: {song_id}")
    if has_melody_generated(song_id):
        print("client has been notified of completion.")
        response = make_response('complete', 200)
        response.mimetype = "text/plain"
        return response
    else:
        print("still Waiting...")
        response = make_response('waiting', 200)
        response.mimetype = "text/plain"
        return response

@app.route('/download_file/<song_id>')
def download_file(song_id):
    filename = f"Generated Melodies/extended_melody_{song_id}.mid"
    return send_file(filename, as_attachment=True)



if __name__ == '__main__':
    app.run()
