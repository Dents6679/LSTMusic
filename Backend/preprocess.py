# @title Imports & Drive mounting
import os
import music21 as m21
import json
import keras
import numpy as np


# @title Constant Definitions


ERK_DATASET_PATH = "KERN/erk"
KERN_DATASET_PATH = "KERN"
SINGLE_FILE_DATASET_DIR = "single file dataset"
SAVE_DIR = "Encoded Dataset"
SONG_MAPPINGS_DIR = "Song Mappings/mappings.json"
MODEL_FILEPATH = "Model Saves/model.keras"

SEQUENCE_LENGTH = 64  # Represents the fixed length input which the LSTM will use.

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

# @title Pre-Processing & Encoding

'''
  Takes a file path and loads all kern and midi songs into music21's representation.
  Ignores all other file types.

  Args:
    dataset_path (string): the file path of the dataset directory as a string.
    verbose(bool) False: Enable additional print statements, for debug purposes

  Returns:
    songs (List of music21.stream.base.score): The list of converted songs.

  Raises:
    NameError: Provides an error if no files are parsed.

'''


def load_songs(dataset_path, verbose=True):
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
        if verbose: print(f"{len(songs)} Songs loaded!")
        return songs


'''
  Shows wether a Music21 Score consists entirely of acceptable durations.
  Makes LSTM representation simpler while not losing too much musical information.

  Args:
    Song (music21.stream.base.Score): The song being checked
    AcceptableDurations(List of floats): The list of acceptable notes, expressed as a quarter length (fraction of a quarter note).
    verbose(bool) False: Enable additional print statements, for debug purposes

  Returns:
    is_acceptable (bool): If the song is acceptable or not.

'''


def has_acceptable_durations(song, acceptable_durations, verbose=True):
    # Flatten all the song's bars->parts->measures->Notes&rests into a single List.
    for note in song.flatten().notesAndRests:
        if note.duration.quarterLength not in acceptable_durations:
            if verbose: print("A Song has been discarded as it contains illegal durations")
            return False
    if verbose: print("Song does not contain any illegal durations")
    return True



def undo_transpose(song, interval, verbose=False):
    """
          Un-Transposes a Music21 Stream from its generated key into the song's original key, as provided.

          Args:
            song (music21.stream.Stream): The stream being Converted
            interval (music21.interval.Interval): The interval to transpose the song by.
            verbose(bool) False: Enable additional print statements, for debug purposes

          Returns:
            transposed_song(music21.stream.base.Score): The un-transposed Song.

    """

    if verbose:
        print("Un-Transposing Generated Melody to align with user supplied melody Key.")

    untransposed_song = song.transpose(interval)

    return untransposed_song


def transpose(song, verbose=False):
    """
      Transposes a Music21 Score from its current key into C Major or A Minor.

      Args:
        song (music21.stream.base.Score): The song being Converted
        verbose(bool) False: Enable additional print statements, for debug purposes

      Returns:
        transposed_song(music21.stream.base.Score): The transposed Song.

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
    print(f"Interval is{str(interval)}.")
    transposed_song = song.transpose(interval)


    return transposed_song, reversed_interval





def encode_song(song, time_step=0.25, verbose=False):
    """
      Encodes a music21 Score into a time series String representation

      Encoded data is represented as a File containing the pitch and duration of a note.
      Each item of the File is a 16th of a note.
      pitch = 60, duration = 1.0 -> [60, "_", "_", "_"]

      e.g.
      Args:
        song (music21.stream.base.Score): The song being Encoded
        time_step(float): The length of each time step
        verbose(bool) False: Enable additional print statements, for debug purposes

      Returns:
        encoded_song: The Encoded Song.

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
    encoded_song = " ".join(map(str, encoded_song))

    return encoded_song



def preprocess(dataset_path, output_path, verbose=False):
    """
      Preprocesses all MIDI/KERN files within a provided directory & its subdirectories, writing encoded songs into specified file directory.
      Parses every MIDI file, Checks for acceptable durations, transposes to Cmaj/Amin,

      Args:
        dataset_path (String): The directory of the dataset's root
        output_path(String): The length of each time step
        verbose(bool) False: Enable additional print statements, for debug purposes

    """
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





def preprocess_api(supplied_midi_path, verbose=False):
    """
      Preprocesses a single supplied MIDI Song into a file, typically supplied from the Flask API.

      Args:
        supplied_midi_path (String): The Directory of the file to preprocess
        verbose(bool) False: Enable additional print statements, for debug purposes

      Returns:
        encoded_api_song: The fully preprocessed API song.
        reverse_transposition: The Transposition required to return the song to its original key from when it's inputted.

    """

    # Parse Supplied MIDI song.
    api_supplied_song = m21.converter.parse(supplied_midi_path)

    # Filter out songs with non-acceptable durations (only using 1/16, 1/8, 1/4, 1/2, 1 notes)
    if not has_acceptable_durations(api_supplied_song, ACCEPTABLE_DURATIONS, verbose):
        raise Exception("The provided song contains an invalid Note length.")

    # Transpose Songs into Cmaj/Amin for standardisation
    api_supplied_song, reverse_transposition = transpose(api_supplied_song, verbose)

    # Encode songs with music time series representation
    encoded_api_song = encode_song(song=api_supplied_song, time_step=0.25, verbose=verbose)

    return encoded_api_song, reverse_transposition


# @title Dataset Encoding for LSTM Use


def load(file_path):
    """
      Loads an encoded song from a file.

      Args:
        file_path (String): The Directory of the file to load.
      Returns:
        song(String): The string representation of the file's contents.
    """

    with open(file_path, "r") as fp:
        song = fp.read()
    return song


def flatten_dataset_to_single_file(encoded_dataset_path, output_path, sequence_length, save=False, verbose=False):
    """
      Flattens Multiple files in a time series string representation into a single String File, saving the file while doing so.

      Args:
        encoded_dataset_path (String): The String of the flattened data
        output_path (String): The path out output the JSON file to.
        sequence_length (Int): The sequence length to use.
        save (bool) False: Whether to save the flattened string or not.
        verbose(bool) False: Enable additional print statements, for debug purposes
    """
    if verbose: print("Started song flattening...")
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
      Creates a mapping of a song's symbols of its time series string representation to integers, saving it as a JSON file
      NOTE: This does not encode the symbol, it only creates a mapping for it.

      Args:
        flattened_songs (String): The String of the flattened data
        mapping_path (String): The path out output the JSON file to.
        verbose(bool) False: Enable additional print statements, for debug purposes

      Returns:
        mappings(Dict{string:int}): Dictionary object of the mappings.

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


def convert_songs_to_int(flattened_songs_string, mappings_dictionary=None, verbose=False):
    """
      Converts a flattened song dataset from Time Series string representation into a mapped time series integer representation using a provided Mapping..
      Done to allow LSTM to take integer values.

      Args:
        flattened_songs_string (String): The String Object of the flattened Songs.
        mappings_dictionary(Dict)=None: Use a supplied dictionary made from create_song_mappings()
        verbose(bool) False: Enable additional print statements, for debug purposes

      Returns:
        int_songs (list of int): The converted songs as a list of integers.

    """

    if verbose:
        print("Converting songs to integer representation.")

    int_songs = []

    if mappings_dictionary is None:
        if verbose:
            print("Loading Mappings from JSON file.")

        # Load Mappings from JSON file
        with open(SONG_MAPPINGS_DIR, "r") as fp:
            mappings_dictionary = json.load(fp)

    # Cast songs string into a list
    flattened_songs_string = flattened_songs_string.split()

    # Map songs to integers
    if verbose: print(f"Mapping {len(flattened_songs_string)} symbols to integers.")
    for symbol in flattened_songs_string:
        int_songs.append(mappings_dictionary[symbol])

    return int_songs


def generate_training_sequences(sequence_length, songs_dataset_string=None, mappings_dictionary=None, verbose=False):
    """
      Creates (dataset symbol length - sequence length) number of training sequences.
      Inputs (fixed length sequences) and target outputs (item just after this sequence) for the LSTM from a integer dataset representation.
      e.g. [11, 12, 13, 14, ...] -> i: [11, 12], t: 13; i: [12, 13], t: 14



      Args:
        sequence_length (int): The sequence length which the LSTM will use to predict it's next note.
        songs_dataset_string (String): The String Object of the flattened dataset.
        verbose(bool) False: Enable additional print statements, for debug purposes

      Returns:
        inputs: 3D list of One-hot encoded Training sequences, with each note being classified from the set of available notes from the vocab.
        targets: The Next notes which are expected from each training sequence as a numpy array.
        vocabulary_size: The size of the vocabulary used, Used in LSTM

    """

    if songs_dataset_string is None:
        # Load songs if they're not provided
        if verbose:
            print("Loading String Dataset from File.")

        songs_dataset_string = load(SINGLE_FILE_DATASET_DIR)
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
                                        num_classes=vocabulary_size)  # One-hot encodes Training sequences into a 3D Array representing each note's Class.

    targets = np.array(targets)  # Casting targets list to numpy array for later use.

    return inputs, targets, vocabulary_size


def main():
    # Preprocess and save the dataset
    # preprocess(dataset_path=KERN_DATASET_PATH, output_path=SAVE_DIR, verbose=True)
    # Flatten dataset
    flattened_dataset = flatten_dataset_to_single_file(encoded_dataset_path=SAVE_DIR,
                                                       output_path=SINGLE_FILE_DATASET_DIR,
                                                       sequence_length=SEQUENCE_LENGTH, save=True, verbose=True)
    # Create integer mappings for all symbols from the flattened dataset.
    song_mappings = create_song_mappings(flattened_songs=flattened_dataset, mapping_path=SONG_MAPPINGS_DIR,
                                         verbose=True)
    # Create Inputs and Targets for the LSTM to use.
    inputs, targets = generate_training_sequences(sequence_length=SEQUENCE_LENGTH,
                                                  songs_dataset_string=flattened_dataset, verbose=True)


if __name__ == '__main__':
    main()
