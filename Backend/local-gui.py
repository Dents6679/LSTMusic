import os

import PySimpleGUI
import PySimpleGUI as sg
from generator import Generator, streamify_melody, MIDI_OUTPUT_PATH
from training import MODEL_FILEPATH
from preprocess import SEQUENCE_LENGTH
from api_tools import preprocess_api, undo_transpose, GenerationError, InvalidNoteDurationError
import time


def handle_local_submission(midi_path: str, output_path: str, temperature: float,
                            extension_length_in_bars: int, window: PySimpleGUI.Window, generator: Generator, verbose: bool = False) -> None:
    # Create File name
    output_path = os.path.join(output_path, "extended_song.mid")
    extension_length = extension_length_in_bars # TODO: Figure out what to multiply this by to make it work with LSTM.
    # Parse file
    try:
        supplied_seed, reverse_transposition = preprocess_api(midi_path=midi_path, verbose=True)
    except Exception as e:
        print("Error parsing file")
        raise e

    # Generate Melody
    try:
        generated_melody = generator.generate_melody(seed=supplied_seed, number_of_steps=400, #TODO: change this to be based on extension length
                                                     max_sequence_length=SEQUENCE_LENGTH, temperature=temperature)
    except Exception as e:
        print("Error generating melody")
        raise GenerationError(f"An error has occurred during Song generation: {e}")

    # Untranspose Melody
    try:
        generated_melody_stream = streamify_melody(generated_melody)
        untransposed_melody = undo_transpose(generated_melody_stream, reverse_transposition)
    except Exception as e:
        print("Error untransposing melody")
        raise e

    # Write to file
    try:
        untransposed_melody.write("midi", output_path)
    except Exception as e:
        print("Error writing file")
        raise e


    

def init_ui() -> PySimpleGUI.Window:
    """
    Initialises sg UI for LSTMusic.
    :return: sg.Window, The window object.
    """
    primary_column = [
        [sg.Text("LSTMusic - Melody Extender", expand_x=True, font=("Helvetica", 20))],
        [sg.Text("File to Extend: "),
         sg.Input(key="-IN FILEPATH-", enable_events=True, disabled=True),
         sg.FileBrowse(key="-IN-", file_types=(("MIDI Files", "*.mid"),))
         ],
        [
            sg.Push(),
            sg.Text("Output Folder:"),
            sg.Input(key="-OUT FILEPATH-", enable_events=True, disabled=True),
            sg.FolderBrowse(key="-OUT-")
         ],
        [sg.Button("Extend!",
                   key="-SUBMIT-",
                   disabled=True,
                   size=(10, 1)
                   )],
        [sg.Text("", key="-OUTPUT-")]
    ]

    parameters = [
        [sg.Text("Parameters", expand_x=True, expand_y=True, font=("Helvetica", 16, "underline"))],
        [sg.Text("")],
        [sg.Text("Temperature:"), sg.Text("0.5", key="-TEMPERATURE TEXT-")],
        [sg.Slider(range=(0.1, 1.0),
                   orientation="h",
                   size=(20, 10),
                   default_value=0.5,
                   disable_number_display=True,
                   resolution=0.01,
                   enable_events=True,
                   key="-TEMPERATURE SLIDER-")],
        [sg.Text("Length:"), sg.Text("2 bars", key="-EXTENSION LENGTH TEXT-")],
        [sg.Slider(range=(2, 16),
                   orientation="h",
                   size=(20, 10),
                   default_value=2,
                   disable_number_display=True,
                   resolution=2,
                   enable_events=True,
                   key="-EXTENSION SLIDER-")]
    ]

    layout = [
        [
            sg.Column(primary_column),
            sg.VSeperator(),
            sg.Column(parameters)
        ]
    ]

    window = sg.Window('LSTMusic Melody Extender', layout)
    return window


def main() -> None:
    """
    Driver Code
    """
    generator = Generator(model_path=MODEL_FILEPATH)
    window = init_ui()

    in_correct = False
    out_correct = False
    melody_submitted = False

    while True:
        event, values = window.read()
        if event == sg.WIN_CLOSED:
            break

        # Update Submission button visibility.
        disable_submit = not (in_correct and out_correct and not melody_submitted)
        print(f"can submit: {disable_submit}")
        window["-SUBMIT-"].update(disabled=disable_submit)

        if event == "-EXTENSION SLIDER-":
            window["-EXTENSION LENGTH TEXT-"].update(f"{int(values['-EXTENSION SLIDER-'])} bars")
        elif event == "-TEMPERATURE SLIDER-":
            window["-TEMPERATURE TEXT-"].update(f"{float(values['-TEMPERATURE SLIDER-'])}")

        elif event == "-IN FILEPATH-":
            # Check if the file is a .mid file.
            if (values["-IN FILEPATH-"][-4:].lower()) == ".mid":
                in_correct = True
                window["-OUTPUT-"].update("File is a valid .mid file. Ready to extend.")

            else:
                in_correct = False
                window["-OUTPUT-"].update("You have not provided a .mid file.\nPlease input a .mid file to extend.")

            continue
        elif event == "-OUT FILEPATH-":
            out_correct = True

        elif event == "-SUBMIT-":
            melody_submitted = True
            window["-OUTPUT-"].update("Extending melody...")
            # TODO: Might be worth multi-threading this part of the code.
            # TODO: Update Error handling to be more specific.
            # Preprocess & Generate file, handling exceptions.
            try:
                handle_local_submission(midi_path=values["-IN FILEPATH-"], output_path=values["-OUT FILEPATH-"],
                                        temperature=float(values["-TEMPERATURE SLIDER-"]),
                                        extension_length_in_bars=int(values["-EXTENSION SLIDER-"]),
                                        window=window, generator=generator, verbose=True)
            except InvalidNoteDurationError as e:
                window["-OUTPUT-"].update(f"Error: {e.message}")
                continue # Skip to next event loop iteration

            except IOError as e:
                window["-OUTPUT-"].update(f"There was an error writing the file.")
                continue

            except Exception as e:
                window["-OUTPUT-"].update(f"Error: {e}")
                continue


            window["-OUTPUT-"].update("Melody extended successfully!")
            melody_submitted = False





    window.close()


if __name__ == '__main__':
    main()