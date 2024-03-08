import base64
import threading
from typing import NoReturn
from flask import Flask, request, send_file, jsonify, make_response
from flask_cors import CORS
from generator import Generator, streamify_melody
from training import MODEL_FILEPATH
from preprocess import SEQUENCE_LENGTH
from api_tools import preprocess_api, undo_transpose, GenerationError, has_melody_generated
import time

UPLOAD_FOLDER_PATH = "Uploaded_files"

generator = Generator(MODEL_FILEPATH)
app = Flask(__name__)
CORS(app)


def generate_to_server(base_file_path, file_number) -> NoReturn:
    """
    # Extends a given base melody and saves it to the server with a unique identifier.
    :param base_file_path: the path of the melody to extend.
    :param file_number: the unique identifier of the melody.
    :return: None
    :raises: IOError, GenerationError, Exception
    """

    if base_file_path is None or file_number is None:
        print("Error in after_request: file_path or file_number is None.")

    print("Generating Melody, please wait...")
    try:
        supplied_seed, reverse_transposition = preprocess_api(base_file_path)
        generated_melody = generator.generate_melody(seed=supplied_seed,
                                                     number_of_steps=400,
                                                     # TODO: Make variables temperature and number_of_steps changeable from the frontend.
                                                     max_sequence_length=SEQUENCE_LENGTH,
                                                     temperature=0.7)
    except Exception:
        print(f"Failed generating Melody through LSTM.")
        raise GenerationError("An error has occurred during generation.")

    try:
        output_path = f"Generated Melodies/extended_melody_{file_number}.mid"

        generated_melody_stream = streamify_melody(generated_melody)
        untransposed_melody = undo_transpose(generated_melody_stream, reverse_transposition)
        untransposed_melody.write("midi", output_path)
    except IOError as e:
        print("Failed MIDI conversion & saving.")
        raise e

    print("Generation and post-processing complete, song has been saved..")

    return None

@app.route('/generate_melody', methods=['POST', 'GET'])
def generate_melody():
    """
    Handles melody generation requests.
    Takes a base 64 encoded MIDI file and responds with a message containing the generation's unique ID.
    Also starts a new thread to generate the melody, which is saved to the server.
    :return:
    """

    # Receive melody, preprocess and respond.
    file_number = str(int(time.time()))
    if request.method == 'POST':
        try:
            data_uri = str(request.data)
        except IOError as e:
            print(f"IOError: Failed to find data from fetch request.")
            raise e

        try:
            _, base64_data = data_uri.split(',', 1)
            base64_data = base64_data[:-1]  # Removes leftover ' from API
            decoded_data = base64.b64decode(base64_data)


            file_path = f"{UPLOAD_FOLDER_PATH}/melody_{file_number}.mid"

            with open(file_path, "wb") as fp:
                fp.write(decoded_data)
        except TypeError as e:
            print(f"Failed Decoding Base64 File: {e}")
            raise e

        generation_thread = threading.Thread(target=generate_to_server, args=(file_path, file_number))
        generation_thread.start()

        response_message = f"Generation request received.;{file_number}"  # Create response message
        resp = jsonify({'status': 200, 'message': response_message})  # Create response
        resp.status_code = 200  # Set status code

        return resp





@app.route('/check_status/<song_id>', methods=['POST', 'GET'])
def check_status(song_id):

    if has_melody_generated(song_id):
        print("client has been notified of completion.")
        response = make_response('complete', 200)
        response.mimetype = "text/plain"
        return response
    else:
        response = make_response('waiting', 200)
        response.mimetype = "text/plain"
        return response


@app.route('/download_file/<song_id>')
def download_file(song_id):
    filename = f"Generated Melodies/extended_melody_{song_id}.mid"
    return send_file(filename, as_attachment=True)



if __name__ == '__main__':
    app.run()
