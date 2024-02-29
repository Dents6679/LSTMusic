import PySimpleGUI as sg


def main() -> None:
    """
    Driver Code
    """



    primary_column = [
              [sg.Text("Choose a .mid file to extend: "), sg.Input(), sg.FileBrowse(key="-IN-")],
              [sg.Button("Load Song"), sg.Button("Submit", key="-SUBMIT-", disabled=True)],
              [sg.Text("Please input a .mid file to extend.", key="-OUTPUT-")]]


    parameters = [[sg.Text("Length:"), [sg.Text("2 bars", key="-EXTENSION LENGTH TEXT-")]],
                        [sg.Slider(range=(0, 8), orientation="h", size=(10, 20), default_value=2, key="-EXTENSION SLIDER-")],]

    layout = [[sg.Text("LSTMusic - Melody Extender", expand_x=True, font=("Helvetica", 20))],
              [sg.Column(primary_column),
               sg.VSeperator(),
               sg.Column(parameters)
              ]
             ]




    window = sg.Window('LSTMusic Melody Extender', layout)

    while True:
        event, values = window.read()
        if event == sg.WIN_CLOSED:
            break

    window.close()


if __name__ == '__main__':
    main()