# List of available functions for oscilloscopes

## oscilloscope_name()
### Arguments: none; Output: string(name).
The function returns device name.
## scope_record_length(\*points)
## oscilloscope_acquisition_type(\*ac_type)
### Arguments: ac_type = integer (0,1,2 or 3); Output: integer.
This function queries or sets the acquisition type for Keysight 3000 oscilloscopes. If there is no argument the function will return the current acquisition type. If there is an argument the specified acquisition type will be set. Possible acquisition types and their meaning are the following:<br/>
'0' - Normal; '1' - Average; '2' - High-resolution (also known as smoothing). This mode is used to reduce noise at slower sweep speeds where the digitizer samples faster than needed to fill memory for the displayed time range; '3' - Peak detect.<br/>
Example: oscilloscope_acquisition_type('1') sets the acquisition type to the average mode.
## oscilloscope_number_of_averages(\*number_of_averages)
### Arguments: number_of_averages = integer (2-65536); Output: integer.
This function queries or sets the number of averages in the range of 2 to 65536 in the averaging acquisition mode (for Keysight 3000 oscilloscopes). If there is no argument the function will return the current number of averages. If there is an argument the specified number of averages type will be set. If the oscilloscopes is not in the averaging acquisition mode the error message will be printed.<br/>
Example: oscilloscope_number_of_averages('2') sets the number of averages to 2.
## oscilloscope_timebase(\*timebase)
### Arguments: timebase = string ('number + scaling (s, ms, us, ns)'); Output: float (in us).
This function queries or sets the full-scale horizontal time for the main window. The range is 10 times the current time-per-division setting. If there is no argument the function will return the full-scale horizontal time in us. If there is an argument the specified full-scale horizontal time will be set.<br/>
Example: oscilloscope_timebase('20 us') sets the full-scale horizontal time to 20 us (2 us per divison).
## oscilloscope_time_resolution()
### Arguments: none; Output: float.
This function takes no arguments and returns the time resolution per point in us.<br/>
Example: oscilloscope_time_resolution() returs the current time resolution per point in us.
## scope_start_acquisition()
## scope_read_preamble(channel)
## oscilloscope_stop()
### Arguments: none; Output: none.
The function stops the acquisition. This is the same as pressing the stop key on the front panel.
## oscilloscope_run()
### Arguments: none; Output: none.
The function starts repetitive acquisitions. This is the same as pressing the run key on the front panel.
## scope_get_curve(channel)
## scope_wave_freq(\*freq) Keysight 3034T
## scope_wave_width(\*width) Keysight 3034T
