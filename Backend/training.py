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
import tensorflow as tf
import os
from typing import List
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2'  # Disables Tensorflow's Debugging Information

LOSS_FN = "sparse_categorical_crossentropy"
LEARNING_RATE = 0.001
NUM_UNITS = [256]
BATCH_SIZE = 64
MODEL_FILEPATH = "Model Resources/Model Saves/model.keras"
ERK_DATASET_PATH = "Dataset Resources/KERN/erk"
KERN_DATASET_PATH = "Dataset Resources/KERN"


def build_model(output_units: int, loss_fn: str, num_units: List[int], learning_rate: float,
                verbose: bool = False):
    """
    Builds the LSTM.

    :param output_units: int, The number of notes which the LSTM can generate.
    Represents the number of keys in our training data.
    :param loss_fn: callable, The loss function being used for training.
    :param num_units: list of int, The number of hidden layers in the network,
    in a list format where each element represents a hidden layer.
    :param learning_rate: float, The LSTM's learning rate.
    :param verbose: bool, optional, Enable additional print statements for debug purposes. Default is False.

    :return: list of int, The converted songs as a list of integers.
    """

    if verbose:
        print("Creating LSTM Model")

    # Create model's architecture.
    # Using None here allows us to use as many timestaps as needed. Allows Generation of Melodies of any length.
    input_layer = keras.layers.Input(shape=(None, output_units))


    # Output units represents the vocabulary size that can be generated.
    x = keras.layers.LSTM(num_units[0])(input_layer)  # Pass input into LSTM layer using Functional API
    x = keras.layers.Dropout(.2)(x)  # Add dropout layer to model. (Avoids over-fitting)
    output_layer = keras.layers.Dense(output_units, activation="softmax")(x)

    # Create Model.
    model = keras.Model(input_layer, output_layer)

    # Compile model.
    model.compile(loss=loss_fn,
                  optimizer=keras.optimizers.Adam(learning_rate=learning_rate),
                  metrics=["accuracy"]
                  )

    if verbose:
        model.summary()  # print a model summary.

    return model


def train(loss_fn: str, num_units: List[int], learning_rate: float, epochs: int, batch_size: int,
          model_path: str = MODEL_FILEPATH, flattened_dataset: str = None, verbose: bool = False) -> None:
    """
    A high-level function which performs all the network's training steps.
    Saves the model's weights and biases to a specified file path when all epochs are completed.
    Saves checkpoints after each epoch.

    :param loss_fn: str, The loss function being used for training.
    :param num_units: list of int, The number of hidden layers in the network, in a list format where each element
    represents a hidden layer.
    :param learning_rate: float, The learning rate the model uses.
    :param epochs: int, The number of epochs used to train the model.
    :param batch_size: int, The amount of samples the network sees before running backpropagation.
    :param model_path: str, The path which the model shall be saved to.
    :param flattened_dataset: str, The flattened dataset which the model will train off of.
    :param verbose: bool, optional, Enable additional print statements for debug purposes. Default is False.

    :return: None.
    """

    # Generate Training Sequences
    inputs, targets, vocabulary_size = generate_training_sequences(sequence_length=SEQUENCE_LENGTH,
                                                                   songs_dataset_string=flattened_dataset,
                                                                   verbose=True)

    # Build network (Checking if a checkpoint exists)
    checkpoint_path = "Model Resources/Model Checkpoints/cp-{epoch:04d}.ckpt"
    latest_checkpoint = tf.train.latest_checkpoint("Model Resources/Model Checkpoints")
    if latest_checkpoint:
        if verbose:
            print(f"Loading weights from {latest_checkpoint}")
        model = build_model(output_units=vocabulary_size, loss_fn=loss_fn, num_units=num_units,
                            learning_rate=learning_rate, verbose=verbose)
        model.load_weights(latest_checkpoint)
    else:
        if verbose:
            print("Starting training from scratch...")
        model = build_model(output_units=vocabulary_size, loss_fn=loss_fn, num_units=num_units,
                            learning_rate=learning_rate, verbose=verbose)

    # Checkpoints
    checkpoint_callback = keras.callbacks.ModelCheckpoint(
        filepath=checkpoint_path,
        save_weights_only=False,
        verbose=1
    )

    # Train model
    model.fit(inputs, targets, epochs=epochs, batch_size=batch_size, callbacks=[checkpoint_callback])

    # Save Model
    model.save(model_path)


def main():
    """
    Driver code to do preprocessing steps and train the model.
    """
    epochs = 16


    preprocess(dataset_path=KERN_DATASET_PATH,
               output_path=ENCODED_DATASET_DIR,
               verbose=True
               )

    flattened_dataset = flatten_dataset_to_single_file(encoded_dataset_path=ENCODED_DATASET_DIR,
                                                       output_path=SINGLE_FILE_DATASET_PATH,
                                                       sequence_length=SEQUENCE_LENGTH,
                                                       save=True,
                                                       verbose=True
                                                       )

    create_song_mappings(flattened_songs=flattened_dataset,
                         mapping_path=NOTE_MAPPINGS_PATH,
                         verbose=True
                         )

    train(loss_fn=LOSS_FN,
          num_units=NUM_UNITS,
          learning_rate=LEARNING_RATE,
          epochs=epochs,
          batch_size=BATCH_SIZE,
          model_path=MODEL_FILEPATH,
          flattened_dataset=flattened_dataset,
          verbose=True
          )


if __name__ == "__main__":
    main()
