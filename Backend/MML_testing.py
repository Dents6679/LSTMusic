
possible_events = ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'a-', 'b-', 'd-', 'e-', 'f-', 'g-', 'r']
possible_lengths = ['2', '4', '16']

def note_to_midi(note_char, current_octave):

    note_map = {'a': 57, 'b': 59, 'c': 60, 'd': 62, 'e': 64, 'f': 65, 'g': 67}
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

        elif getting_octave: # If the token is a number following an 'o'
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





def main():



    test_string = "o4abcdefg"
    print(macro_to_time_series(test_string))


if __name__ == '__main__':
    main()