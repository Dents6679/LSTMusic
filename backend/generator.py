import json
import keras
from preprocess import SEQUENCE_LENGTH, NOTE_MAPPINGS_PATH
from training import MODEL_FILEPATH
import numpy as np
import music21 as m21
from typing import List

MIDI_OUTPUT_PATH = "generated-melodies/melody.mid"


def streamify_melody(melody: str, step_duration: float = 0.25, tempo: int = 120) -> m21.stream.Stream:
    """
    De-encodes a Time Series String into an M21 Stream object.

    :param melody: The Melody to de-encode
    :param step_duration: The Step duration.
    :param tempo: The tempo of the melody.
    :return stream: The M21 Stream representation of the melody.
    """

    # Create music21 stream
    stream = m21.stream.Stream()
    stream.append(m21.tempo.MetronomeMark(number=tempo))

    # Parse melody's Symbols & Create note/rest objects.
    start_symbol = None
    step_count = 1

    for i, symbol in enumerate(melody):
        # New note/rest case
        if symbol != "_" or i + 1 == len(melody):

            # Ensure the first note/evnet is not being read.
            if start_symbol is not None:
                duration_in_quarter_length = step_duration * step_count
                # Handle Rest
                if start_symbol == "r":
                    m21_event = m21.note.Rest(duration_in_quarter_length)

                # handle Note
                else:
                    m21_event = m21.note.Note(int(start_symbol), quarterLength=duration_in_quarter_length)

                # Add event to stream
                stream.append(m21_event)

                # Reset Step Counter
                step_count = 1

            # Set the starting symbol from the read symbol.
            start_symbol = symbol
        # Prolongation sign case
        else:
            step_count += 1

    return stream


def sample_with_temperature(probability_distribution: List[float], temperature: float) -> int:
    """
    Picks a sample from a probability distribution, Forcefully increase the entropy of a specified temperature value.
    :param probability_distribution: The distribution to pick the next note from.
    :param temperature: The temperature to use. 1 is the default temp.
    :return index: The Index of the sample which will be picked.
    """

    predictions = np.log(probability_distribution) / temperature
    probability_distribution = np.exp(predictions) / np.sum(np.exp(predictions))

    choices = range(len(probability_distribution))  # e.g. [0, 1, 2 ,3]
    index = np.random.choice(choices, p=probability_distribution)  # Pick a random index using probabilities as weights.

    return index


class Generator:

    def __init__(self, model_path: str) -> None:
        """
        Initialises the Music Generator by loading a trained model.
        :param model_path: str, Path of the saved model.
        """
        self.model_path = model_path
        self.model = keras.models.load_model(model_path)
        with open(NOTE_MAPPINGS_PATH, "r") as fp:
            self._mappings = json.load(fp)

        self._start_symbols = ["/"] * SEQUENCE_LENGTH

    def generate_melody(self, seed: str, number_of_steps: int, max_sequence_length: int, temperature: float,
                        verbose: bool = False) -> str:
        """
        Generates a melody.

        :param seed: The seed which kick-starts the melody off, in string time series notation ("64 _ 63 _ _")
        :param number_of_steps: The number of steps to generate before stopping.
        :param max_sequence_length: Limits the sequence length which the network uses for 'context'. Use Sequence
                                    length due to training, uses SEQUENCE_LENGTH
        :param temperature: A Value which impacts the randomness of output symbols are sampled from the network.
        :param verbose: Used to show LSTM predictions or not.
        :return melody: The String Representation of the new song.
        """

        # Create seed with start symbols.
        # The seed here will be provided by the Frontend and is provided by the user.
        seed = seed.split()
        melody = seed  # Initiate melody as seed.
        seed = self._start_symbols + seed

        # Map seed to int representation
        seed = [self._mappings[symbol] for symbol in seed]

        for _ in range(number_of_steps):
            # Limit the seed to the max sequence length
            seed = seed[-max_sequence_length:]

            # One hot encode the Seed.
            onehot_seed = keras.utils.to_categorical(seed, num_classes=len(self._mappings))
            onehot_seed = onehot_seed[np.newaxis, ...]

            # Predict the prbabilities of the next note. (gives a probability of each symbol in the vocabulary.)
            next_note_probability_distribution = self.model.predict(onehot_seed, verbose=verbose)[0]


            # Select a note from the distribution. If the temp is 0, pick the most likely note.
            if temperature == 0:
                output_int = np.argmax(next_note_probability_distribution)
            else:
                output_int = sample_with_temperature(probability_distribution=next_note_probability_distribution,
                                                     temperature=temperature)

            # Update the adding the sampled int.
            seed.append(output_int)

            # Map sampled, encoded int to it's unencoded value.
            output_symbol = [k for k, v in self._mappings.items() if v == output_int][0]

            # End the melody if the system decides it's most likely to end.
            if output_symbol == "/":
                continue

            # Update the Melody
            melody.append(output_symbol)
        if verbose:
            print("Melody Generated")

        return melody


if __name__ == '__main__':
    # Generator Test Code.
    '''
    Annoyingly this code doesn't allow for transposition, so all of the generated 
    parts of the melodies will be in Cmaj/Amin. 
    When using the API, this is handled by the preprocess_api and undo_transpose functions.
    '''

    generator = Generator(MODEL_FILEPATH)
    cheerful_seed = "60 62 60 62 _ 64 _ 62 _ 60 _ 67 _ 67 _ _ _ 65 _ 65 _ 64 _ _ _ 62 _ 62 _ 60 _ _ _"
    jodge_seed = "68 _ _ _ _ _ _ _ 70 _ _ _ 71 _ _ _ 71 _ _ _ 70 _ 68 _ _ _ _ _ _ _"
    my_seed = "50 52 54 56 58 60 62 64 66 68 70 72 74 76 78"
    long_seed = "62 _ 62 _ 62 _ 64 _ _ _ 64 _ 64 _ 67 _ _ _ 67 _ _ _ 66 _ _ _ _ _ _ _ r _ _ _ _ _ _ _"

    seed = my_seed

    melody = generator.generate_melody(seed=seed, number_of_steps=600, max_sequence_length=SEQUENCE_LENGTH,
                                       temperature=0.7)

    melody_stream = streamify_melody(melody)
    melody_stream.write("midi", MIDI_OUTPUT_PATH)
    print("Melody Generated.")
