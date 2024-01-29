import os.path

from preprocess import *
import keras


LOSS_FN = "sparse_categorical_crossentropy"
LEARNING_RATE = 0.001
NUM_UNITS = [256]
EPOCHS = 10
BATCH_SIZE = 64




def build_model(output_units, loss_fn, num_units, learning_rate, verbose=False):
    """
        Builds the LSTM

        Args:

          loss_fn: The loss function being used for training.
          num_units: The number of hidden layers in the network, in a list format where each element represents a hidden layer.
          learning_rate: The LSTM's Learning Rate
          verbose(bool) False: Enable additional print statements, for debug purposes.


        Returns:
            int_songs (list of int): The converted songs as a list of integers.

    """
    if verbose: print("Creating LSTM Model")

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

    if verbose: model.summary()  # print a model summary.

    return model


def train(loss_fn, num_units, learning_rate, epochs, batch_size, model_path=MODEL_FILEPATH, flattened_dataset=None,
          verbose=False):
    """
    A High level Function which performs all the network's training steps. Saves the model's weights and biases to a specified file path.

    Args:
      loss_fn: The loss function being used for training.
      num_units: the number of hidden layers in the network, in a list format where each elements represents a hidden layer.
      learning_rate: the learning rate the model uses.
      epochs: The number of epochs used to train the model.
      batch_size: the amount of samples the network sees before running backpropagation
      model_path: the path which the model shall be saved to.
      flattened_dataset: The Flattened dataset which the model will train off of.
      verbose(bool) False: Enable additional print statements, for debug purposes.


    Returns:
      Nothing.

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
    preprocess(dataset_path=ERK_DATASET_PATH, output_path=SAVE_DIR,
               verbose=True)  # TODO: Change to full dataset, remember to delete everything from the folders once this is changed.
    flattened_dataset = flatten_dataset_to_single_file(encoded_dataset_path=SAVE_DIR,
                                                       output_path=SINGLE_FILE_DATASET_DIR,
                                                       sequence_length=SEQUENCE_LENGTH, save=False, verbose=True)
    song_mappings = create_song_mappings(flattened_songs=flattened_dataset, mapping_path=SONG_MAPPINGS_DIR,
                                         verbose=True)
    train(loss_fn=LOSS_FN, num_units=NUM_UNITS, learning_rate=LEARNING_RATE, epochs=EPOCHS, batch_size=BATCH_SIZE,
          model_path=MODEL_FILEPATH, flattened_dataset=flattened_dataset, verbose=True)
