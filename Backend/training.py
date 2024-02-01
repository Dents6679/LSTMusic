from preprocess import (preprocess,
                        generate_training_sequences,
                        flatten_dataset_to_single_file,
                        create_song_mappings,
                        SEQUENCE_LENGTH,
                        SINGLE_FILE_DATASET_PATH,
                        ENCODED_DATASET_DIR,
                        NOTE_MAPPINGS_PATH
                        )
import keras

LOSS_FN = "sparse_categorical_crossentropy"
LEARNING_RATE = 0.001
NUM_UNITS = [256]
EPOCHS = 10
BATCH_SIZE = 64
MODEL_FILEPATH = "Model Saves/model.keras"
ERK_DATASET_PATH = "KERN/erk"
KERN_DATASET_PATH = "KERN"


def build_model(output_units, loss_fn, num_units, learning_rate, verbose=False):
    """
    Builds the LSTM.

    :param output_units: int, The number of notes which the LSTM can generate. Represents the number of keys in our training
                         data.
    :param loss_fn: callable, The loss function being used for training.
    :param num_units: list of int, The number of hidden layers in the network, in a list format where each element represents a
                      hidden layer.
    :param learning_rate: float, The LSTM's learning rate.
    :param verbose: bool, optional, Enable additional print statements for debug purposes. Default is False.

    :return: list of int, The converted songs as a list of integers.
    """

    if verbose:
        print("Creating LSTM Model")

    # Create model's architecture.
    input_layer = keras.layers.Input(shape=(None,
                                            output_units))  # Using None allows us to use as manytimestaps as we like. Allows Generation of Melodies of any length.
    # Output units represents the vocabulary size that can be generated.
    x = keras.layers.LSTM(num_units[0])(input_layer)  # Pass input into LSTM layer using Functional API
    x = keras.layers.Dropout(.2)(x)  # Add dropout layer to model. (Avoids overfitting)
    output_layer = keras.layers.Dense(output_units, activation="softmax")(x)

    model = keras.Model(input_layer, output_layer)  # Creates Model.
    # Compile model.
    model.compile(loss=loss_fn,
                  optimizer=keras.optimizers.Adam(lr=learning_rate),
                  metrics=["accuracy"]
                  )

    if verbose:
        model.summary()  # print a model summary.

    return model


def train(loss_fn, num_units, learning_rate, epochs, batch_size, model_path=MODEL_FILEPATH, flattened_dataset=None,
          verbose=False):
    """
    A high-level function which performs all the network's training steps. Saves the model's weights and biases to a specified file path.

    :param loss_fn: callable, The loss function being used for training.
    :param num_units: list of int, The number of hidden layers in the network, in a list format where each element represents a
                      hidden layer.
    :param learning_rate: float, The learning rate the model uses.
    :param epochs: int, The number of epochs used to train the model.
    :param batch_size: int, The amount of samples the network sees before running backpropagation.
    :param model_path: str, The path which the model shall be saved to.
    :param flattened_dataset: list, The flattened dataset which the model will train off of.
    :param verbose: bool, optional, Enable additional print statements for debug purposes. Default is False.

    :return: None.
    """

    # Generate Training Sequences
    inputs, targets, vocabulary_size = generate_training_sequences(sequence_length=SEQUENCE_LENGTH,
                                                                   songs_dataset_string=flattened_dataset, verbose=True)

    # Build network
    model = build_model(output_units=vocabulary_size, loss_fn=loss_fn, num_units=num_units, learning_rate=learning_rate,
                        verbose=verbose)

    # Train model
    model.fit(inputs, targets, epochs=epochs, batch_size=batch_size)

    # Save Model

    model.save(model_path)


if __name__ == "__main__":
    preprocess(dataset_path=KERN_DATASET_PATH, output_path=SINGLE_FILE_DATASET_PATH,
               verbose=True)  # TODO: Change to full dataset, remember to delete everything from the folders once this is changed.
    flattened_dataset = flatten_dataset_to_single_file(encoded_dataset_path=ENCODED_DATASET_DIR,
                                                       output_path=SINGLE_FILE_DATASET_PATH,
                                                       sequence_length=SEQUENCE_LENGTH, save=False, verbose=True)
    song_mappings = create_song_mappings(flattened_songs=flattened_dataset, mapping_path=NOTE_MAPPINGS_PATH,
                                         verbose=True)
    train(loss_fn=LOSS_FN, num_units=NUM_UNITS, learning_rate=LEARNING_RATE, epochs=EPOCHS, batch_size=BATCH_SIZE,
          model_path=MODEL_FILEPATH, flattened_dataset=flattened_dataset, verbose=True)
