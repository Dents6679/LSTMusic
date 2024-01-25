import keras
import json
from preprocess import SEQUENCE_LENGTH, SONG_MAPPINGS_DIR
from training import *
import numpy as np
import music21 as m21

MIDI_OUTPUT_PATH = "Generated Melodies/melody.mid"  # "C:/Users/td336/OneDrive - University of Sussex/Third Year/Individual project/Backend/Generated Melodies/melody.mid"


class Generator:

    def __init__(self, model_path):
        """
        Initialises the Music Generator by loading a trained model.
        :param model_path: Path of the saved model.
        """
        self.model_path = model_path
        self.model = keras.models.load_model(model_path)
        with open(SONG_MAPPINGS_DIR, "r") as fp:
            self._mappings = json.load(fp)

        self._start_symbols = ["/"] * SEQUENCE_LENGTH

    def _sample_with_temperature(self, probability_distribution, temperature):
        '''
        Picks a sample from a probability distribution, Forcefully increase the entropy of a specified temparature value.
        :param probability_distribution: The distribution to pick the next note from.
        :param temperature: The temperature to use. 1 is the default temp.
        :return index: The Index of the sample which will be picked.
        '''

        predictions = np.log(probability_distribution) / temperature
        probability_distribution = np.exp(predictions) / np.sum(np.exp(predictions))

        choices = range(len(probability_distribution))  # [0, 1, 2 ,3]
        index = np.random.choice(choices,
                                 p=probability_distribution)  # Pick a random index using the probability as weights.

        return index

    def save_melody_as_midi(self, melody, step_duration=0.25, path=MIDI_OUTPUT_PATH):

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

        # Write m21 stream to a midi file
        stream.write("midi", path)

    def generate_melody(self, seed, number_of_steps, max_sequence_length, temperature):
        """
        Generates a melody.
        :param seed: The seed which starts the melody off, in string time series notation ("64 _ 63 _ _")
        :param number_of_steps: The number of steps to generate before stopping.
        :param max_sequence_length: Limits the sequence length which the network uses for 'context'. Use Sequence length due to training, uses SEQUENCE_LENGTH
        :param temperature: A Value which impacts the randomness of output symbols are sampled from the network.
        :return:
        """

        # Create seed with start symbols.
        seed = seed.split()
        melody = seed  # Initiate melody as seed.
        seed = self._start_symbols + seed

        # Map seed to int representation
        seed = [self._mappings[symbol] for symbol in
                seed]  # TODO: change this to API fed melody rather than fully random seed.

        for _ in range(number_of_steps):
            # Limit the seed to the max sequence length
            seed = seed[-max_sequence_length:]

            # One hot encode the Seed.
            onehot_seed = keras.utils.to_categorical(seed, num_classes=len(
                self._mappings))  # TODO: This may cause issues, the length of self mappings may not be the same as a user inputted melody.
            # 3d array of (1, max_sequence_length * vocabulary size)
            onehot_seed = onehot_seed[np.newaxis, ...]

            # Predict the next note. (gives a probability of each symbol in the vocabulary.)
            next_note_probability_distribution = self.model.predict(onehot_seed)[0]
            # Could just use the highest probability item here, but to decrease the 'rigidity' of the output I'm gonna use the temparature.

            output_int = self._sample_with_temperature(probability_distribution=next_note_probability_distribution,
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
        print("Your melody has been Generated.")
        return melody


if __name__ == '__main__':
    generator = Generator(MODEL_FILEPATH)
    seed = "60 _ 60 _ 60 _ 56 56 56  62 _ 63 64 _ 65 66 _ 67 _ _ "
    melody = generator.generate_melody(seed=seed, number_of_steps=400, max_sequence_length=SEQUENCE_LENGTH,
                                       temperature=0.7)
    generator.save_melody_as_midi(melody)

    melody = generator.generate_melody(seed=seed, number_of_steps=400, max_sequence_length=SEQUENCE_LENGTH,
                                       temperature=0.7)
    generator.save_melody_as_midi(melody)
