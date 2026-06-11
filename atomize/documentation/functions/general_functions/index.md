# General Functions

Description of available general functions in Atomize, including a module for saving or opening data.

## [Functions](general_functions.md)

| Function | Description |
| -------- | ----------- |
| [`message()`](general_functions.md#print-a-string-in-the-main-window) | Print a string in the main window |
| [`message_test()`](general_functions.md#print-a-string-in-the-main-window-in-the-test-run) | Print a string in the main window in the test run |
| [`bot_message()`](general_functions.md#send-a-message-via-telegram-bot) | Send a message via Telegram bot |
| [`wait()`](general_functions.md#wait-for-the-specified-amount-of-time) | Wait for the specified amount of time |
| [`to_infinity()`](general_functions.md#infinite-loop) | Infinite loop compatible with test mode |
| [`const_shift()`](general_functions.md#constant-shift) | Constant shift of a pulse position |

## [Data management](data_managment.md)

| Function | Description |
| -------- | ----------- |
| [`open_1d(file_path, header=0)`](data_managment.md#open_1d) | Open a file with comma separated values |
| [`open_2d(file_path, header=0)`](data_managment.md#open_2d) | Open a file with a 2D array of comma separated values |
| [`open_2d_appended(file_path, header=0, chunk_size=1)`](data_managment.md#open_2d_appended) | Open a file with a single column array of values from 2D array |
| [`open_file_dialog(directory='')`](data_managment.md#open_file_dialog) | Open file selection dialog |
| [`create_file_dialog(directory='')`](data_managment.md#create_file_dialog) | Create file via save dialog |
| [`create_file_parameters(add_name, directory='')`](data_managment.md#create_file_parameters) | Create data + parameters file pair |
| [`save_header(filename, header='', mode='w')`](data_managment.md#save_header) | Save a header to a file |
| [`save_data(filename, data, header='', mode='w')`](data_managment.md#save_data) | Save a numpy array to a file |
| [`Bruker_Opener().open(path)`](bruker_opener.md#bruker_open) | Read Bruker native files (BES3T / ESP/WinEPR), 1D/2D, real or I/Q |

## Related

| Page | Description |
| ---- | ----------- |
| [Concurrency](concurrency.md) | Running functions in a separate thread |
| [Examples](examples.md)       | Open / save CSV, concurrent plotting |
