"""
Upon further investigation, it seems as if the MML format is a bit more complex than I initially thought.
Fortunately though, webaudio-pianoroll's internal song representation is much simpler than the MML format,
So I'll be using that.
"""


possible_events = ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'a-', 'b-', 'd-', 'e-', 'f-', 'g-', 'r']
possible_lengths = ['2', '4', '16']
note_map = {'a': 57, 'b': 59, 'c': 60, 'd': 62, 'e': 64, 'f': 65, 'g': 67}


def note_to_midi(note_char: str, current_octave: int) -> int:
    """
    Converts a note from its MML representation to a MIDI note number.
    :param note_char: The note to convert.
    :param current_octave: The current octave of the note.
    :return: The MIDI note number.
    """
    return note_map[note_char] + (current_octave - 4) * 12


def macro_to_time_series(macro_string: str) -> str:
    time_series = ""
    current_note_length = 1  # The length of the current note in eighth notes
    current_octave = 4
    previous_note_length = 0

    getting_octave = False
    getting_note_length = False

    for i, token in enumerate(macro_string):

        if token == 'o':  # If the token is an octave change
            if getting_note_length:
                # Add the current note to the time series
                getting_note_length = False

            getting_octave = True
            current_octave = int(macro_string[i+1])

        elif getting_octave:  # If the token is a number following an 'o'
            current_octave = int(token)

        elif token in possible_events:  # If the token is a new note or a rest.
            if getting_note_length:

                getting_note_length = False
                # Add the current note to the time series

            # TODO: Add case for & and .
            getting_note_length = True

        elif getting_note_length:
            if token in possible_lengths:
                current_note_length = int(token)



        elif token == '&':
            pass
            # Ignore next note letter but not the length
        elif token == '.':
            pass
            # Halve the length of the previous note and add it to the time series




def attempt_2(mml_string: str) -> str:

    if mml_string[3] != 'o':
        print("Tempo is a value below 100.")
        tempo = mml_string[1:2]
        current_octave = mml_string[4]
        default_note_length = mml_string[6]
        mml_song_data = mml_string[8:]
    else:
        print("Tempo is a value above 99.")
        tempo = mml_string[1:3]
        current_octave = mml_string[5]
        default_note_length = mml_string[7]
        mml_song_data = mml_string[8:]

    if len(mml_song_data) == 0:
        print("An empty song was provided.")
        # TODO: Add a generate from empty call here.

    time_series = ""  # The time series to return.
    getting_octave = False  # Flag for getting the octave.
    getting_length = False  # Flag for getting the length of the note.
    is_flat_note = False  # Flag for checking if the current token is a modifier.
    and_extension = False  # Flag for checking if the current token is an extension using the '&' Symbol.
    current_note_length = 0  # The length of the current note in !!eighth notes!!
    current_note_base = "c"  # The base note of the current note.
    current_note_midi_number = 60  # The midi number of the current note.
    length_stack = ""  # The stack for the length of the note.

    for i, token in enumerate(mml_song_data):
        # Case for getting Octave.
        if token == 'o':
            getting_octave = True
        elif getting_octave:
            current_octave = int(token)
            getting_octave = False

        # If there is a note event.
        elif token in possible_events:
            # Set the note base to the current token.
            current_note_base = token
            # Check if the next token is a flat modifier.
            if mml_song_data[i+1] == '-':
                is_flat_note = True
                continue

            current_note_length = 1 # Set current Note length to default to 1/8 Note for the default case.
            getting_length = True

        elif is_flat_note:
            # If the token is a flat modifier, change the note base, reset the flag and skip the next token.
            current_note_base = current_note_base + '-'
            is_flat_note = False
            current_note_length = 1  # Set current Note length to default to 1/8 Note for the default case.
            getting_length = True


        # Used to get the length of a note extension.
        if getting_length and and_extension:
            length_stack += token
            if token == current_note_base:
                and_extension = False
                continue



        elif getting_length:

            length_stack += token
            if token == "&":
                and_extension = True
                continue
            elif token in possible_events:
                continue





            # Check to see if the next token is still getting the length.
            if mml_song_data[i + 1] == 'o' or mml_song_data[i + 1] in possible_events:
                getting_length = False



        elif token in possible_events:
            time_series += f"{note_to_midi(token, current_octave)} "



        elif token in possible_lengths:
            pass
        elif token == '&':
            pass
        elif token == '.':
            pass










def convert_length_stack(length_string: str) -> int:
    """
    Converts the length stack to a number of 16th notes.
    Output of this fn will be multiplied by "_" when outputting time series.
    :param length_string:
    :return:
    """




def main():
    test_string = "o4abcdefg"
    print(macro_to_time_series(test_string))


if __name__ == '__main__':
    main()