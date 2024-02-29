import PySimpleGUI as sg


def main() -> None:
    """
    Driver Code
    """

    layout = [  [sg.Text('Hello world!')]
             ]

    window = sg.Window('Test', layout)

    while True:
        event, values = window.read()
        if event == sg.WIN_CLOSED:
            break

    window.close()


if __name__ == '__main__':
    main()