const errorId = location.search.split('errorId=')[1];
const errorText = document.getElementById('error-text');

//manually setting error message for testing


switch (errorId) {

    case '1': // Server not Available
        errorText.innerText = 'The backend server is not available right now. Please try again later.';
        document.getElementById('gen-id').style.display = 'none';
        break;
    case '2': // Generation Error
        errorText.innerText = 'An error has occurred while trying to generate your Melody. Please try again.';
        break;
    case '3': // Timeout Error
        errorText.innerText = 'Your Melody could not be generated. Please try again.';
        break;


}


