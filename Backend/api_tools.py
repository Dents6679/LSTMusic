from preprocess import ACCEPTABLE_DURATIONS, has_acceptable_durations, transpose, encode_song
import music21 as m21
from typing import Tuple, List, Any


class GenerationError(Exception):
    """Exception raised for errors during AI generation."""

    def __init__(self, message="Error during Music generation. Please Check that your input is valid."):
        self.message = message
        super().__init__(self.message)


def preprocess_api(supplied_midi_path, verbose=False) -> Tuple[List[int], m21.interval.Interval]:
    """
    Preprocesses a single supplied MIDI Song into a file, typically supplied from the Flask API.

    :param supplied_midi_path: str, The directory of the file to preprocess.
    :param verbose: bool, optional, Enable additional print statements for debug purposes. Default is False.

    :return: tuple, (encoded_api_song, reverse_transposition),
             The fully preprocessed API song and the transposition required to return the song to its original key.
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
