import json
import keras
from preprocess import SEQUENCE_LENGTH, NOTE_MAPPINGS_PATH
from training import MODEL_FILEPATH
import numpy as np
import music21 as m21

MIDI_OUTPUT_PATH = "Generated Melodies/melody.mid"


def streamify_melody(melody, step_duration=0.25):
    """
    De-encodes a Time Series String into an M21 Stream object.

    :param melody: M21.stream.Stream, The Melody to de-encode
    :param step_duration: float, The Step duration.
    :return stream: Music21.stream.Stream, The M21 Stream representation of the melody.
    """

    # Create music21 stream
    stream = m21.stream.Stream()

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

    return stream  # stream.write("midi", path) will convert this into a MIDI file for later.


def sample_with_temperature(probability_distribution, temperature):
    """
    Picks a sample from a probability distribution, Forcefully increase the entropy of a specified temparature value.
    :param probability_distribution: list of float, The distribution to pick the next note from.
    :param temperature: float, The temperature to use. 1 is the default temp.
    :return index: int, The Index of the sample which will be picked.
    """

    predictions = np.log(probability_distribution) / temperature
    probability_distribution = np.exp(predictions) / np.sum(np.exp(predictions))

    choices = range(len(probability_distribution))  # [0, 1, 2 ,3]
    index = np.random.choice(choices,
                             p=probability_distribution)  # Pick a random index using the probability as weights.

    return index


class Generator:

    def __init__(self, model_path):
        """
        Initialises the Music Generator by loading a trained model.
        :param model_path: str, Path of the saved model.
        """
        self.model_path = model_path
        self.model = keras.models.load_model(model_path)
        with open(NOTE_MAPPINGS_PATH, "r") as fp:
            self._mappings = json.load(fp)

        self._start_symbols = ["/"] * SEQUENCE_LENGTH




    def generate_melody(self, seed, number_of_steps, max_sequence_length, temperature, verbose=False):
        """
        Generates a melody.

        :param seed: str, The seed which kick-starts the melody off, in string time series notation ("64 _ 63 _ _")
        :param number_of_steps: int, The number of steps to generate before stopping.
        :param max_sequence_length: int, Limits the sequence length which the network uses for 'context'. Use Sequence
                                         length due to training, uses SEQUENCE_LENGTH
        :param temperature: float, A Value which impacts the randomness of output symbols are sampled from the network.
        :param verbose: bool, Used to show LSTM predictions or not.
        :return melody: str, The String Representation of the new song.
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
            onehot_seed = keras.utils.to_categorical(seed, num_classes=len(
                self._mappings))
            # TODO: This may cause issues, the length of self mappings may not be the same as a user inputted melody.
            # 3d array of (1, max_sequence_length * vocabulary size)
            onehot_seed = onehot_seed[np.newaxis, ...]

            # Predict the next note. (gives a probability of each symbol in the vocabulary.)
            next_note_probability_distribution = self.model.predict(onehot_seed, verbose=verbose)[0]
            # Could just use the highest probability item here...
            # But, to decrease the 'rigidity' of the output I'm going to use the temperature picked one instead.

            output_int = sample_with_temperature(probability_distribution=next_note_probability_distribution,
                                                 temperature=temperature)

            # Update the adding the sampled int.
            seed.append(output_int)

            # Map sampled, encoded int to it's unencoded value.
            output_symbol = [k for k, v in self._mappings.items() if v == output_int][0]

            # Check if we're at the melody's end
            if output_symbol == "/":
                break

            # Update the Melody
            melody.append(output_symbol)
        if verbose:
            print("Melody Generated")



        return melody


if __name__ == '__main__':
    generator = Generator(MODEL_FILEPATH)
    seed = ""
    melody = generator.generate_melody(seed=seed, number_of_steps=400, max_sequence_length=SEQUENCE_LENGTH,
                                       temperature=0.7)
    generator.save_melody_as_midi(melody)

    melody = generator.generate_melody(seed=seed, number_of_steps=400, max_sequence_length=SEQUENCE_LENGTH,
                                       temperature=0.7)
    generator.save_melody_as_midi(melody)
