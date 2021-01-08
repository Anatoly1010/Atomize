# List of available functions for wave generators
```python3
wave_gen_name()
Arguments: none; Output: string(name).
```
The function returns device name.
```python3
wave_gen_frequency(\*frequency)
Arguments: frequency = string ('number + scaling (MHz, kHz, Hz, mHz)'); Output: float (in Hz).
```
This function queries or sets the frequency of the waveform of the wave generator. If there is no argument the function will return the current frequency in Hz. If there is an argument the specified frequency will be set. The function works for all waveforms except Noise and DC.<br/>
Please, refer to a manual of the device for available frequency range.<br/>
```python3
Example: wave_gen_frequency('20 kHz') sets the frequency of the waveform
of the wave generator to 20 kHz.
```
```python3
wave_gen_pulse_width(\*width)
Arguments: width = string ('number + scaling (s, ms, us, ns)'); Output: float (in us).
```
This function queries or sets the width of the pulse of the wave generator. If there is no argument the function will return the current width in us. If there is an argument the specified width will be set. The pulse width can be adjusted from 20 ns to the period minus 20 ns. The function available only for pulse waveforms.<br/>
```python3
Example: wave_gen_pulse_width('20 ms') sets the width of the waveform of the wave
generator to 20 ms.
```
```python3
wave_gen_function(\*function)
Arguments: function = string from a specified dictionary; Output: string.
```
This function queries or sets the type of waveform of the wave generator. The type should be from the following array:<br/>
['Sin', 'Sq', 'Ramp', 'Pulse', 'DC', 'Noise', 'Sinc', 'ERise', 'EFall', 'Card', 'Gauss', 'Arb'].<br/>
```python3
Example: wave_gen_function('Sq') sets the sqare waveform.
```
```python3
wave_gen_amplitude(\*amplitude)
Arguments: amplitude = string ('number + scaling (V, mV)'); Output: float (in mV).
```
This function queries or sets the waveform's amplitude. If there is no argument the function will return the current amplitude in mV. If there is an argument the specified amplitude will be set. The function available for all waveforms except DC.<br/>
```python3
Example: wave_gen_amplitude('200 mV') sets the waveform's amplitude to 200 mV.
```
```python3
wave_gen_offset(\*offset)
Arguments: offset = string ('number + scaling (V, mV)'); Output: float (in mV).
```
This function queries or sets the waveform's offset voltage or the DC level. If there is no argument the function will return the current offset voltage in mV. If there is an argument the specified offset will be set.<br/>
```python3
Example: wave_gen_offset('0.5 V') sets the waveform's offset voltage to 500 mV.
```
```python3
wave_gen_impedance(\*impedance)
Arguments: offset = string ('impedance string (1 M, 50)'); Output: string.
```
This function queries or sets the output load impedance of the wave generator. If there is no argument the function will return the current impedance. If there is an argument the specified impedance will be set.<br/>
```python3
Example: wave_gen_impedance('50') sets the output load impedance of the wave generator
to 50 Ohm.
```
```python3
wave_gen_run()
Arguments: none; Output: none.
```
The function runs the waveform generator. This is the same as pressing the Wave Gen key on the front panel.
```python3
wave_gen_stop()
Arguments: none; Output: none.
```
The function stops the waveform generator. This is the same as pressing the Wave Gen key on the front panel.
```python3
wave_gen_arbitrary_function(list)
Arguments: list of floats ([first_point, second_point, ...]); Output: none.
```
This function downloads an arbitrary waveform in floating-point values format. The values have to be between -1.0 to +1.0.<br/>
```python3
Example: wave_gen_arbitrary_function([0, 0.5, 1, 0.5, 0, -0.5, -1, -0.5, 0])
sets the specified arbitrary waveform.
```
```python3
wave_gen_arbitrary_clear()
Arguments: none; Output: none.
```
The function clears the arbitrary waveform memory and loads it with the default waveform.
```python3
wave_gen_arbitrary_interpolation(\*mode)
Arguments: mode = string (['On', 'Off']); Output: integer.
```
This function enables or disables the interpolation control. If there is no argument the function will return the current interpolation setting (0 means Off; 1 means On). If there is an argument the specified interpolation setting will be set.<br/>
Interpolation specifies how lines are drawn between arbitrary waveform points:<br/>
When ON (1), lines are drawn between points in the arbitrary waveform. Voltage levels change linearly between one point and the next.<br/>
When OFF (0), all line segments in the arbitrary waveform are horizontal. The voltage level of one point remains until the next point.<br/>
```python3
Example: wave_gen_arbitrary_interpolation('On') turns on the interpolation control.
```
```python3
wave_gen_arbitrary_points()
Arguments: none; Output: integer.
```
This function returns the number of points used by the current arbitrary waveform.
```python3
wave_gen_command(command)
Arguments: command = string; Output: none.
```
The function for sending an arbitrary command from a programming guide to the device in a string format. No output is expected.<br/>
```python3
wave_gen_query(command)
Arguments: command = string; Output: string (answer).
```
The function for sending an arbitrary command from a programming guide to the device in a string format. An output in a string format is expected.<br/>
