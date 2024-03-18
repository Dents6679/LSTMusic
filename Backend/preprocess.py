# Imports & Drive mounting
import os
import music21 as m21
import json
import keras
import numpy as np
from typing import List, Tuple, Any
# Constant Definitions

SEQUENCE_LENGTH = 64  # Represents the fixed length input which the LSTM will use.

os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2'  # Disables Tensorflow's Debugging Information
KERN_DATASET_PATH = "Dataset Resources/KERN"
SINGLE_FILE_DATASET_PATH = "Dataset Resources/single file dataset"
ENCODED_DATASET_DIR = "Dataset Resources/Encoded Dataset"
NOTE_MAPPINGS_PATH = "Dataset Resources/Song Mappings/mappings.json"

ACCEPTABLE_DURATIONS = [
    0.25,  # Sixteenth Note
    0.5,  # Eighth Note
    0.75,  # Dotted Eighth Note
    1,  # Quarter Note
    1.5,  # Dotted Quarter Note
    2,  # Half Note
    3,  # 3 Quarter Note
    4  # Whole note
]

def file_exists(file_path) -> bool:
    """
    Checks if a file exists.
    :param file_path: The file to check.
    :return: If the file exists.
    """
    return os.path.exists(file_path)


def has_files_within(directory_path) -> bool:
    """
    Checks if a directory contains any files.
    :param directory_path: The directory to check.
    :return: If the directory contains any files.
    """
    return len(os.listdir(directory_path)) > 0


def load_songs(dataset_path, verbose=True) -> List[m21.stream.base.Score]:
    """
    Takes a file path and loads all kern and midi songs into music21's representation.
    Ignores all other file types.

    :param dataset_path: str, The file path of the dataset directory.
    :param verbose: bool, optional, Enable additional print statements for debug purposes. Default is False.
    :return: list of music21.stream.base.Score, The list of converted songs.
    :raises NameError: Provides an error if no files are parsed.
    """
    print("Loading Songs...")
    songs = []
    for path, subdirs, files in os.walk(dataset_path):
        for file in files:
            if file[-3:] == "krn" or file[-3:] == "mid":
                # song var represents an m21 score of music.
                song = m21.converter.parse(os.path.join(path, file))
                songs.append(song)
    if len(songs) == 0:
        raise NameError("The provided path does not contain any music files.")
    else:
        if verbose:
            print(f"{len(songs)} Songs loaded!")
        return songs


def has_acceptable_durations(song, acceptable_durations, verbose=True) -> bool:
    """
    Shows whether a Music21 Score consists entirely of acceptable durations.
    Makes LSTM representation simpler while not losing too much musical information.

    :param song: music21.stream.base.Score, The song being checked.
    :param acceptable_durations: list of float, The list of acceptable notes, expressed as a quarter length (fraction of a quarter note).
    :param verbose: bool, optional, Enable additional print statements for debug purposes. Default is False.

    :return: bool, If the song is acceptable or not.

    """
    # Flatten all the song's bars->parts->measures->Notes&rests into a single List.
    for note in song.flatten().notesAndRests:
        if note.duration.quarterLength not in acceptable_durations:
            if verbose: print("A Song has been discarded as it contains illegal durations")
            return False
    return True


def transpose(song, verbose=False) -> Tuple[m21.stream.base.Score, m21.interval.Interval]:
    """
    Transposes a Music21 Score from its current key into C Major or A Minor.

    :param song: music21.stream.base.Score, The song being converted.
    :param verbose: bool, optional, Enable additional print statements for debug purposes. Default is False.

    :return: music21.stream.base.Score, The transposed song.
    """
    # Get key from metadata.
    parts = song.getElementsByClass(m21.stream.Part)  # Get song's parts (instrument tracks)
    part0_measures = parts[0].getElementsByClass(m21.stream.Measure)  # Get the measures (bars) of the first part.
    key = part0_measures[0][4]  # Get the key from the song's first measure at Index 4.

    # Estimate key using Music21 if Key isn't stored in metadata.
    if not isinstance(key, m21.key.Key):
        key = song.analyze("key")

    # Calculate the interval for the transposition required. E.g, Bmaj -> Cmaj
    if key.mode == "major":
        interval = m21.interval.Interval(key.tonic, m21.pitch.Pitch("C"))
    elif key.mode == "minor":
        interval = m21.interval.Interval(key.tonic, m21.pitch.Pitch("A"))

    reversed_interval = m21.interval.Interval.reverse(interval)  # Reversed Interval is Used after a song is generated.

    # Transpose song using calculated interval
    to_note = "C" if key.mode == "major" else "A"
    if verbose:
        print(f"Converting Song from Key {key.tonic} {key.mode} To {to_note} {key.mode}")
    transposed_song = song.transpose(interval)

    return transposed_song, reversed_interval


def encode_song(song, time_step=0.25, verbose=False) -> str:
    """
    Encodes a music21 Score into a time series String representation.

    Encoded data is represented as a File containing the pitch and duration of a note.
    Each item of the File is a 16th of a note.
    pitch = 60, duration = 1.0 -> [60, "_", "_", "_"]

    :param song: music21.stream.base.Score, The song being encoded.
    :param time_step: float, The length of each time step.
    :param verbose: bool, optional, Enable additional print statements for debug purposes. Default is False.

    :return: str, The encoded song.
    """

    encoded_song = []

    for event in song.flatten().notesAndRests:
        # Handle Notes
        if isinstance(event, m21.note.Note):
            symbol = event.pitch.midi
        # Handle Rests
        elif isinstance(event, m21.note.Rest):
            symbol = "r"

        # Convert Note/Rest into Time Series Notation
        steps = int(event.duration.quarterLength / time_step)
        for step in range(steps):
            if step == 0:
                encoded_song.append(symbol)
            else:
                encoded_song.append("_")

    # Cast encoded song into a string
    encoded_song_string = " ".join(map(str, encoded_song))

    return encoded_song_string


def preprocess(dataset_path, output_path, verbose=False) -> None:
    """
    Preprocesses all MIDI/KERN files within a provided directory & its subdirectories, writing encoded songs into specified file directory.
    Parses every MIDI file, checks for acceptable durations, transposes to Cmaj/Amin.

    :param dataset_path: str, The directory of the dataset's root.
    :param output_path: str, The directory where the encoded songs will be written.
    :param verbose: bool, optional, Enable additional print statements for debug purposes. Default is False.
    """

    # Check if there is an existing pre-processed dataset.

    if has_files_within(output_path):
        check_if_overwriting = input(f"An existing preprocessed dataset containing {len(os.listdir(output_path))} files has been found.\nWould you like to use it? (y/n):\n ")
        if check_if_overwriting.lower() != "n":
            print("Using existing dataset...")
            return


    # Load Data
    songs = load_songs(dataset_path)

    # Filter out songs with non-acceptable durations (only using 1/16, 1/8, 1/4, 1/2, 1 notes).
    for i, song in enumerate(songs):
        if not has_acceptable_durations(song, ACCEPTABLE_DURATIONS, verbose):
            continue

        # Transpose Songs into Cmaj/Amin for standardisation.
        song, _ = transpose(song, verbose)

        # Encode songs with music time series representation.
        encoded_song = encode_song(song=song, time_step=0.25, verbose=verbose)

        # Save Encoded songs into text files.
        save_path = os.path.join(output_path, str(i))
        with open(save_path, "w") as fp:
            fp.write(encoded_song)


def load(file_path) -> str:
    """
    Loads an encoded song from a file.
    :param file_path: str, The directory of the file to load.
    :return: str, The string representation of the file's contents.
    """

    with open(file_path, "r") as fp:
        song = fp.read()
    return song


def flatten_dataset_to_single_file(encoded_dataset_path, output_path, sequence_length, save=False,
                                   verbose=False) -> str:
    """
    Flattens multiple files in a time series string representation into a single String File,
    saving the file while doing so.

    :param encoded_dataset_path: str, The string of the flattened data.
    :param output_path: str, The path to output the JSON file to.
    :param sequence_length: int, The sequence length to use.
    :param save: bool, optional, Whether to save the flattened string or not. Default is False.
    :param verbose: bool, optional, Enable additional print statements for debug purposes. Default is False.

    :return songs: str, The flattened dataset.
    """

    # Check if there is an existing pre-processed dataset.

    if file_exists(output_path):
        check_if_overwriting = input("A pre-existing flattened dataset has been found."
                                     "\nWould you like to use it? (y/n):\n")
        if check_if_overwriting.lower() != "n":
            print("Loading existing flattened dataset...")
            return load(output_path)

    if verbose:
        print("Started song flattening...")

    song_delimiter = "/ " * sequence_length
    songs = ""

    number_of_songs = 0
    # Load Encoded Songs and add delimiters
    for path, _, files in os.walk(encoded_dataset_path):
        for file in files:
            file_path = os.path.join(path, file)
            song = load(file_path)
            songs = songs + song + " " + song_delimiter
            number_of_songs += 1

    songs = songs[:-1]  # Remove the last space on the last song's delimiter.
    is_saved = ""
    if save:
        # Save flattened String to path
        with open(output_path, "w") as fp:
            fp.write(songs)
            is_saved = "and Saved"

    if verbose:
        print(f"Successfully compressed {is_saved} {number_of_songs} songs into 1 String of length {len(songs)}.")
    return songs


def create_song_mappings(flattened_songs, mapping_path, verbose=False):
    """
    Creates a mapping of a song's symbols of its time series string representation to integers, saving it as a JSON file.
    NOTE: This does not encode the symbol, it only creates a mapping for it.

    :param flattened_songs: str, The string of the flattened data.
    :param mapping_path: str, The path to output the JSON file to.
    :param verbose: bool, optional, Enable additional print statements for debug purposes. Default is False.

    :return: dict, Dictionary object of the mappings.
    """

    mappings = {}

    # Identify Vocabulary
    flattened_songs = flattened_songs.split()
    vocabulary = list(set(flattened_songs))

    # Create mappings
    for i, symbol in enumerate(vocabulary):
        mappings[symbol] = i

    # Save Vocabulary to JSON File
    with open(mapping_path, "w") as fp:
        json.dump(mappings, fp, indent=4)
    if verbose:
        print(f"Created JSON file with {len(mappings)} Symbol Mappings.")

    return mappings


def convert_songs_to_int(flattened_songs_string, mappings_dictionary=None, verbose=False) -> List[int]:
    """
    Converts a flattened song dataset from Time Series string representation into a mapped time series integer representation using a provided Mapping.
    Done to allow LSTM to take integer values.

    :param flattened_songs_string: str, The string object of the flattened songs.
    :param mappings_dictionary: dict, optional, Use a supplied dictionary made from create_symbol_mapping(). Default is None.
    :param verbose: bool, optional, Enable additional print statements for debug purposes. Default is False.

    :return: list of int, The converted songs as a list of integers.
    """

    if verbose:
        print("Converting songs to integer representation.")

    int_songs = []

    if mappings_dictionary is None:
        if verbose:
            print("Loading Mappings from JSON file.")

        # Load Mappings from JSON file
        with open(NOTE_MAPPINGS_PATH, "r") as fp:
            mappings_dictionary = json.load(fp)

    # Cast songs string into a list
    flattened_songs_string = flattened_songs_string.split()

    # Map songs to integers
    if verbose:
        print(f"Mapping {len(flattened_songs_string)} symbols to integers.")
    for symbol in flattened_songs_string:
        int_songs.append(mappings_dictionary[symbol])

    return int_songs


def generate_training_sequences(sequence_length, songs_dataset_string=None, mappings_dictionary=None, verbose=False):
    """
    Creates (dataset symbol length - sequence length) number of training sequences.
    Inputs (fixed length sequences) and target outputs (item just after this sequence) for the LSTM from an integer dataset representation.
    e.g. [11, 12, 13, 14, ...] -> i: [11, 12], t: 13; i: [12, 13], t: 14


    :param sequence_length: int, The sequence length which the LSTM will use to predict its next note.
    :param songs_dataset_string: str, The string object of the flattened dataset.
    :param mappings_dictionary: dict, optional, Allows a dictionary mapping to be provided.
    :param verbose: bool, optional, Enable additional print statements for debug purposes. Default is False.

    :return: tuple, (inputs, targets, vocabulary_size),
             inputs: 3D list of one-hot encoded training sequences,
             targets: the next notes which are expected from each training sequence as a numpy array,
             vocabulary_size: the size of the vocabulary used (used in LSTM).
    """

    if songs_dataset_string is None:
        # Load songs if they're not provided
        if verbose:
            print("Loading String Dataset from File.")

        songs_dataset_string = load(SINGLE_FILE_DATASET_PATH)
    # Map songs to their integer representation.
    int_songs = convert_songs_to_int(flattened_songs_string=songs_dataset_string,
                                     mappings_dictionary=mappings_dictionary)

    # Generate the training sequences
    if verbose: print("Creating training sequences...")

    inputs = []
    targets = []

    sequences_amount = len(int_songs) - sequence_length

    for i in range(sequences_amount):
        inputs.append(int_songs[i:i + sequence_length])
        targets.append(int_songs[i + sequence_length])
    if verbose: print(f"Successfully created {sequences_amount} training sequences.")

    # One-hot encode sequences

    # Inputs: 3d list of with shape: num of sequences * sequence_length * vocabulary_size
    # One Hot Encoding
    # [ [0, 1, 2], [1, 1, 2] ] -> [ [ [1,0,0], [0,1,0], [0,0,1] ], [ [0,1,0], [0,1,0], [0,0,1] ] ]
    # Uses a number of items equal to the vocabulary size. Each position after one-hot encoding represents a class.
    # The number of units within the LSTM's input layer will be equal to the vocabulary size of the dataset.
    # This is an easy way to deal with discrete Categorical data in Neural Networks.

    vocabulary_size = len(set(int_songs))
    inputs = keras.utils.to_categorical(inputs,
                                        num_classes=vocabulary_size)  # One-hot encodes Training sequences into a 3D
    # Array representing each note's Class.

    targets = np.array(targets)  # Casting targets list to numpy array for later use.

    return inputs, targets, vocabulary_size


def main():
    # Preprocess and save the dataset
    preprocess(dataset_path=KERN_DATASET_PATH,
               output_path=ENCODED_DATASET_DIR,
               verbose=True)
    # Flatten dataset
    flattened_dataset = flatten_dataset_to_single_file(encoded_dataset_path=ENCODED_DATASET_DIR,
                                                       output_path=SINGLE_FILE_DATASET_PATH,
                                                       sequence_length=SEQUENCE_LENGTH, save=True, verbose=True)
    # Create integer mappings for all symbols from the flattened dataset.
    song_mappings = create_song_mappings(flattened_songs=flattened_dataset,
                                         mapping_path=NOTE_MAPPINGS_PATH,
                                         verbose=True)
    # Create Inputs and Targets for the LSTM to use.
    inputs, targets, vocab_size = generate_training_sequences(sequence_length=SEQUENCE_LENGTH,
                                                              songs_dataset_string=flattened_dataset, verbose=True)


if __name__ == '__main__':
    main()
