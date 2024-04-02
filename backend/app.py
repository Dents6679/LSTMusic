import base64
import threading
from typing import NoReturn
from flask import Flask, request, send_file, jsonify, make_response
from flask_cors import CORS
from generator import Generator, streamify_melody
from training import MODEL_FILEPATH
from preprocess import SEQUENCE_LENGTH
from api_tools import preprocess_midi, undo_transpose, GenerationError, has_melody_generated, process_api_sequence, \
    add_failed_generation, check_failed_generation
import time
import json

UPLOAD_FOLDER_PATH = "uploaded-files"

generator = Generator(MODEL_FILEPATH)
app = Flask(__name__)
CORS(app)


def generate_to_server(base_file_path: str, file_number: str, temperature: float, extension_length: int) -> NoReturn:
    """
    Extends a given base melody and saves it to the server with a unique identifier.
    defined as a separate function for use in a separate thread to allow for main thread to respond to client.
    :param temperature: The temperature to use while generating the melody.
    :param extension_length: The length of the melody to generate in LSTM event units.
    :param base_file_path: the path of the MIDI melody to extend.
    :param file_number: the unique identifier of the melody, used for output.
    :return: None
    :raises: IOError, GenerationError, Exception
    """

    if base_file_path is None or file_number is None:
        print("Error in after_request: file_path or file_number is None.")

    print("Generating Melody, please wait...")
    try:
        supplied_seed, reverse_transposition = preprocess_midi(base_file_path)
        generated_melody = generator.generate_melody(seed=supplied_seed,
                                                     number_of_steps=extension_length,
                                                     max_sequence_length=SEQUENCE_LENGTH,
                                                     temperature=temperature)
    except Exception as e:
        # Prevent melody from being saved if generation fails.
        add_failed_generation(file_number)
        raise GenerationError(f"Failed to generate melody: {e}")



    try:
        output_path = f"generated-melodies/extended_melody_{file_number}.mid"
        generated_melody_stream = streamify_melody(generated_melody)
        untransposed_melody = undo_transpose(generated_melody_stream, reverse_transposition)
        untransposed_melody.write("midi", output_path)

    except IOError as e:
        print(f"Failed MIDI conversion & saving.")
        raise e

    except Exception as e:
        print(f"Failed to save melody to server.")
        raise e

    print("Generation and post-processing complete, song has been saved..")
    return None




@app.route('/generate_melody_new', methods=['POST', 'GET'])
def generate_melody_new():
    """
        Handles melody generation requests from the new frontend.
        takes raw text containing the MML music representation and other generation parameters,
        and responds with a message containing the generation's unique ID.

        Also starts a new thread to generate the melody, which is saved to the server.
        :return:
    """

    # Generate unique Melody ID and prepare melody file path.
    song_id = str(int(time.time()))


    # Get data from request.
    try:
        response_data = str(request.data)
    except IOError as e:
        print(f"IOError: Failed to find data from fetch request.")
        raise e

    response_items = response_data.split(';;;')
    temperature = float(response_items[1])

    # Decode MML and save it as a MIDI file to server.
    raw_sequence = response_items[0][2::]

    sequence = json.loads(raw_sequence)

    # TODO: Save the sequence as a MIDI file to the server.
    unextended_midi_file_path = process_api_sequence(sequence, song_id=song_id, verbose=True)

    # Calculate Extension Length for LSTM, Measured in 'series events' which represent a 16th of a note.
    extension_length_in_bars = int(response_items[2][:-1])
    extension_length_for_lstm = extension_length_in_bars * 16  # Convert to 16th notes

    # Start Melody Generation

    generation_thread = threading.Thread(target=generate_to_server, args=(unextended_midi_file_path,
                                                                          song_id,
                                                                          temperature,
                                                                          extension_length_for_lstm))
    generation_thread.start()


    # Create & return response message
    response_message = f"Generation request received.;{song_id}"  # Create response message
    resp = jsonify({'status': 200, 'message': response_message})  # Create response
    resp.status_code = 200  # Set status code

    return resp


@app.route('/check_status/<song_id>', methods=['POST', 'GET'])
def check_status(song_id):

    if check_failed_generation(song_id):
        response = make_response('failed', 200)
        response.mimetype = "text/plain"
        return response

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
    filename = f"generated-melodies/extended_melody_{song_id}.mid"
    return send_file(filename, as_attachment=True)


if __name__ == '__main__':
    app.run()
