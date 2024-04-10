from preprocess import transpose, encode_song
import music21 as m21
from typing import Tuple, Dict, List
import os


class GenerationError(Exception):
    """Exception raised for errors during AI generation."""

    def __init__(self, message="An error has occurred During generation."):
        self.message = message
        super().__init__(self.message)


class InvalidNoteDurationError(Exception):
    """Exception raised for note length issues."""

    def __init__(self, message="The provided song contains an invalid Note length."):
        self.message = message
        super().__init__(self.message)


def process_api_sequence(sequence: List[Dict[str, int]], song_id: str, verbose: bool = False) -> Tuple[str, int]:
    """
    preprocesses a single api-supplied sequence into a MIDI file.

    :param sequence: The sequence to save as a MIDI file.
    :param song_id: The ID of the song.
    :param verbose: Enable additional print statements for debug purposes. Default is False.
    :return: Tuple, The path of the saved MIDI file and the length to offset the generation by.
    """

    # Turn the sequence into a 2d array
    sequence = [list(event.values()) for event in sequence]
    # Create a new stream
    stream = m21.stream.Stream()


    last_event_end = 0  # Used for keeping track of rest durations
    total_duration = 0  # Used for keeping track of total inputted melody duration. Allows for extension length to work.

    # Work out rests and note durations
    for event_index, event in enumerate(sequence):
        event_start = event[0]
        event_pitch = event[1]
        event_duration = event[2]
        event_duration_in_quarter_lengths = event_duration / 2
        total_duration += event_duration_in_quarter_lengths  # Add length to total duration
        # Handle rests
        if last_event_end < event_start:
            rest_duration_in_quarter_lengths = (event_start - last_event_end)/2
            rest = m21.note.Rest(quarterLength=rest_duration_in_quarter_lengths)
            # Length is halved here to convert to quarter lengths
            stream.append(rest)
            total_duration += rest_duration_in_quarter_lengths  # Add rest length to total duration
        # Handle notes
        note = m21.note.Note(event_pitch, quarterLength=event_duration_in_quarter_lengths)
        stream.append(note)

        last_event_end = event_start + event_duration

    # Save the stream as a MIDI file
    midi_file_path = os.path.join("uploaded-files", f"unextended_melody_{song_id}.mid")
    stream.write("midi", midi_file_path)

    if verbose:
        print(f"Saved MIDI file to {midi_file_path}")

    return midi_file_path, total_duration


def preprocess_midi(midi_path, verbose=False) -> Tuple[str, m21.interval.Interval]:
    """
    Preprocesses a single supplied MIDI Song into a file, typically supplied from the Flask API.

    :param midi_path: str, The directory of the file to preprocess.
    :param verbose: bool, optional, Enable additional print statements for debug purposes. Default is False.

    :return: tuple, (encoded_api_song, reverse_transposition),
             The fully preprocessed API song and the transposition required to return the song to its original key.
    """

    # Parse Supplied MIDI song.
    api_supplied_song = m21.converter.parse(midi_path)

    """
        Turns out the frontend is able to provide note durations that are not in the ACCEPTABLE_DURATIONS list.
        This may cause issues. Some issues still arise, which will be dealt with.
    
    # Filter out songs with non-acceptable durations (only using 1/16, 1/8, 1/4, 1/2, 1 notes)
    if not has_acceptable_durations(api_supplied_song, ACCEPTABLE_DURATIONS, verbose):
        raise InvalidNoteDurationError("The provided song contains an invalid Note length.")
    """

    # Transpose Songs into CMaj/Amin for standardisation
    api_supplied_song, reverse_transposition = transpose(api_supplied_song, verbose)

    # Encode songs with music time series representation
    encoded_api_song = encode_song(song=api_supplied_song, time_step=0.25, verbose=verbose)

    return encoded_api_song, reverse_transposition


def undo_transpose(song, interval, verbose=False) -> m21.stream.base.Score:
    """
    Un-Transposes a Music21 Stream from its generated key into the song's original key, as provided.

    :param song: music21.stream.Stream, The transposed stream to un-transpose.
    :param interval: music21.interval.Interval, The interval to un-transpose the song by.
    :param verbose: bool, optional, Enable additional print statements for debug purposes. Default is False.

    :return: music21.stream.base.Score, The un-transposed song.
    """

    if verbose:
        print("Un-Transposing Generated Melody to align with user supplied melody Key.")

    untransposed_song = song.transpose(interval)

    return untransposed_song


def has_melody_generated(song_id: str) -> bool:
    """
    Checks if the melody has been generated and saved.
    :param song_id: str The ID of the melody.
    :return bool: True if the melody has been generated, False otherwise.
    """
    path = os.path.join("generated-melodies", f"extended_melody_{song_id}.mid")
    return os.path.exists(path)


def add_failed_generation(song_id: str) -> None:
    """
    Adds a failed generation to the failed generations file.
    :param song_id: str The ID of the song.
    :return: None
    """
    with open("failed_generations.txt", "a") as file:
        file.write(f"{song_id}\n")
    file.close()
    return None


def check_failed_generation(song_id: str) -> bool:
    """
    Checks if the generation has failed by reading the top 5 lines.
    :param song_id: str The ID of the song.
    :return: bool True if the generation has failed, False otherwise.
    """

    # Get the top 5 lines of the file
    with open("failed_generations.txt", "r") as file:
        lines = [full_id[:-1:] for full_id in file.readlines()[-5::]]
    file.close()
    # Check if the song_id is in these lines
    return song_id in lines
