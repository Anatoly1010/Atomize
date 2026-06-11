# Oscilloscopes

## Devices

| Device                                       | Tested  | Connection |
| -------------------------------------------- | ------- | ---------- |
| **Keysight InfiniiVision 2000 X-Series**     | 07/2021 | Ethernet   |
| **Keysight InfiniiVision 3000 X-Series**     | 06/2021 | Ethernet   |
| **Keysight InfiniiVision 4000 X-Series**     | Untested| Ethernet   |
| **Tektronix 3000 Series**                    | 09/2022 | Ethernet   |
| **Tektronix 4000 Series**                    | 01/2021 | Ethernet   |
| **Tektronix 5 Series MSO**                   | 12/2023 | Ethernet   |
| **Rigol MSO8000 Series**                     | 01/2026 | Ethernet   |

## Functions

### oscilloscope_name() { #oscilloscope_name data-toc-label="oscilloscope_name" }

```python
oscilloscope_name()    # -> str; device name
```

This function returns device name.

---

### oscilloscope_record_length(*points) { #oscilloscope_record_length data-toc-label="oscilloscope_record_length" }

```python
oscilloscope_record_length()        # -> int (query)
oscilloscope_record_length(4000)    # set number of waveform points to 4000
```

This function queries or sets the number of waveform points to be transferred using [`oscilloscope_get_curve()`](#oscilloscope_get_curve) function. If there is no number of points setting fitting the argument the nearest available value is used and warning is printed.

If one would like to use Keysight oscilloscopes without [averaging](#oscilloscope_acquisition_type) (in normal, peak or high-resolution mode), the number of points in the waveform is usually `[100, 250, 500, 1000, 2000, 5000, 10000]`.

As stated in the programming manual, the number of points acquired cannot be directly controlled. For Keysight 3000 X-series the number of points are usually from the following array: `[100, 250, 500, 1000, 2000, 4000, 8000]`. For Keysight 2000 X-series: `[99, 247, 479, 959, 1919, 3839, 7679]`. For Keysight 4000 X-series the number of points should be checked. There is also a known bug in older firmware versions that causes an incorrect number of points to be returned during the first data collection after changing the data collection settings. Please update the oscilloscope [firmware](https://www.keysight.com/us/en/assets/9922-03906/release-notes/Keysight-3000T-X-Series-Oscilloscope-Release-Notes-07-56.pdf).

For Rigol MSO8000 Series the number of points in the waveform for normal, peak or high-resolution [mode](#oscilloscope_acquisition_type) is `[1000, 10000, 1e5, 1e6, 1e7, 2.5e7, 5e7, 1e8, 1.25e8]`. For the average [mode](#oscilloscope_acquisition_type) the number of points is `[1000, 10000, 1e5, 1e6, 1e7, 2.5e7]`. To use this feature effectively, one should disable the Auto ROLL option.

For Tektronix 3000 Series the available number of points is `[500, 10000]`.

For Tektronix 4000 Series the available number of points is `[1000, 10000, 100000, 1000000, 10000000]`.

---

### oscilloscope_acquisition_type(*ac_type) { #oscilloscope_acquisition_type data-toc-label="oscilloscope_acquisition_type" }

```python
oscilloscope_acquisition_type()             # -> str (query)
oscilloscope_acquisition_type('Average')    # set acquisition type to average mode
```

This function queries or sets the acquisition type. If there is no argument the function will return the current acquisition type. High-resolution (also known as smoothing) mode is used to reduce noise at slower sweep speeds where the digitizer samples faster than needed to fill memory for the displayed time range.

!!! note
    For Tektronix 3000 Series `'Hres'` option is not available.

**Allowed:** `'Normal'`, `'Average'`, `'Hres'`, `'Peak'`
{: .enum }

---

### oscilloscope_number_of_averages(*number_of_averages) { #oscilloscope_number_of_averages data-toc-label="oscilloscope_number_of_averages" }

```python
oscilloscope_number_of_averages()       # -> int (query)
oscilloscope_number_of_averages(2)      # set number of averages to 2
```

This function queries or sets the number of averages. If there is no argument the function will return the current number of averages. If there is an argument the specified number of averages type will be set. If the oscilloscopes is not in the averaging acquisition mode the error message will be printed.

**Range (Keysight):** `2` – `65536`
{: .enum }

**Range (Tektronix 4000 Series):** `2` – `512` in powers of two (some models limited to `128`)
{: .enum }

**Range (Rigol MSO8000):** `2` – `65536` in powers of two
{: .enum }

---

### oscilloscope_timebase(*timebase) { #oscilloscope_timebase data-toc-label="oscilloscope_timebase" }

```python
oscilloscope_timebase()           # -> str (query)
oscilloscope_timebase('20 us')    # set full-scale horizontal time to 20 us (2 us/div)
```

This function queries or sets the full-scale horizontal time for the main window. The range is 10 times the current time-per-division setting. If there is no argument the function will return the full-scale horizontal time. If there is an argument the specified full-scale horizontal time will be set.

For Tektronix 3000 X-series the horizontal scale is discrete and can take on a value in the range of 10 s to 1, 2, or 4 ns (depending on model), in a 1-2-4 sequence, see the array below.

For Tektronix 4000 X-series (at least for the device used for testing), the horizontal scale is discrete and can take on a value from the following array: `[1, 2, 4, 10, 20, 40, 100, 200, 400]` for ns, us, ms, and s scaling. In addtition timescale equals to 800 ns also can be set. If there is no timebase setting fitting the argument the nearest available value is used and warning is printed.

**Output format:** `'number'` + `'s'` | `'ms'` | `'us'` | `'ns'`
{: .enum }

---

### oscilloscope_define_window(**kargs) { #oscilloscope_define_window data-toc-label="oscilloscope_define_window" }

```python
oscilloscope_define_window()                       # -> (int, int) (query)
oscilloscope_define_window(start=1, stop=1000)     # transfer the first 1000 points
```

This function queries or sets the starting data and ending points for waveform transfer. The function should be called with two key arguments, namely `start` and `stop`. `start` is the first data point that will be transferred, which ranges from 1 to the record length. `stop` is the last data point that will be transferred, which ranges from 1 to the record length.

!!! note
    This function is avaliable only for Tektronix 3000 Series, 4000 Series, 5 Series MSO.

---

### oscilloscope_time_resolution() { #oscilloscope_time_resolution data-toc-label="oscilloscope_time_resolution" }

```python
oscilloscope_time_resolution()    # -> str; current time resolution per point
```

This function takes no arguments and returns the time resolution per point.

**Output format:** `'number'` + `'s'` | `'ms'` | `'us'` | `'ns'`
{: .enum }

---

### oscilloscope_start_acquisition() { #oscilloscope_start_acquisition data-toc-label="oscilloscope_start_acquisition" }

```python
oscilloscope_start_acquisition()    # start an acquisition sequence
```

This function starts an acquisition sequence.

For Keysight and Tektronix oscilloscopes previously measured curves are discarded and new data are sampled until the desired number of averages has been reached. This function acquires all the channels currently displayed on the screen of oscilloscopes and should be called before [`oscilloscope_get_curve()`](#oscilloscope_get_curve) function.

For Rigol MSO8000 Series this function clears all the waveforms on the screen and [runs](#oscilloscope_run) the oscilloscope. Note also that for Rigol MSO8000 Series, it is not possible to control the number of averages in the waveform for the `'Average'` [acquisition type](#oscilloscope_acquisition_type). More details are given in the [`oscilloscope_get_curve()`](#oscilloscope_get_curve) function.

---

### oscilloscope_preamble(channel) { #oscilloscope_preamble data-toc-label="oscilloscope_preamble" }

```python
oscilloscope_preamble('CH3')    # -> list; preamble for channel 3
```

This function requests the preamble information for the selected waveform source. The preamble data contains information concerning the vertical and horizontal scaling of the data of the corresponding channel.

**Preamble format (Keysight):** `[format, type, points, count, xincrement, xorigin, xreference, yincrement, yorigin, yreference]`

**Preamble format (Tektronix):** `[data width, bits per point, encoding, format of the binary data, byte order, channel, coupling, vert scale, horiz scale, record length, acq mode, number of points in waveform, point format, horiz units, xincrement, xorigin, displayed?, vert units, vert scale mult factor, yoff, yorigin]`

**Preamble format (Rigol):** `[format, type, points, count, xincrement, xorigin, xreference, yincrement, yorigin, yreference]`

**Allowed channels:** `'CH1'`, `'CH2'`, `'CH3'`, `'CH4'`
{: .enum }

---

### oscilloscope_stop() { #oscilloscope_stop data-toc-label="oscilloscope_stop" }

```python
oscilloscope_stop()    # stop the acquisition
```

This function stops the acquisition. This is the same as pressing the stop key on the front panel.

---

### oscilloscope_run() { #oscilloscope_run data-toc-label="oscilloscope_run" }

```python
oscilloscope_run()    # start repetitive acquisitions
```

This function starts repetitive acquisitions. This is the same as pressing the run key on the front panel.

---

### oscilloscope_get_curve(channel) { #oscilloscope_get_curve data-toc-label="oscilloscope_get_curve" }

```python
oscilloscope_get_curve('CH2')    # -> np.array; data from channel 2 (V)
```

This function returns a waveform (y-axis values only) from specified channel of the oscilloscope. Values are given in volts. At the moment, it expects one argument, namely the channel from which the data should be transferred. The data from two channels can be transferred sequentially.

If you need to get both the x- and y-axis, consider using the [`oscilloscope_get_curve(integral=False)`](#oscilloscope_get_curve-integral) function.

For Rigol MSO8000 Series, it is not possible to control the number of averages in the waveform for the `'Average'` [acquisition type](#oscilloscope_acquisition_type). This function [returns](#oscilloscope_get_curve-mode) the waveform data on the screen or from the internal memory.

**Allowed channels:** `'CH1'`, `'CH2'`, `'CH3'`, `'CH4'`
{: .enum }

---

### oscilloscope_get_curve(channel, mode = 'Normal') { #oscilloscope_get_curve-mode data-toc-label="oscilloscope_get_curve(mode)" }

```python
# return data on screen from channel 2
oscilloscope_get_curve('CH2', mode='Normal')
```

For Rigol MSO8000 Series, there is an additional keyword `'mode' = ['Normal', 'Raw']`, which is used to specify the data return mode. The default option is `'Normal'`. In `'Normal'` mode, the oscilloscope returns the waveform data currently displayed on the screen. In `'Raw'` mode, the oscilloscpe returns the waveform data from the internal memory.

**Allowed mode:** `'Normal'`, `'Raw'`
{: .enum }

---

### oscilloscope_get_curve(channel, integral = False) { #oscilloscope_get_curve-integral data-toc-label="oscilloscope_get_curve(integral)" }

```python
# run acquisition and return integrated data from channel 1
oscilloscope_get_curve('CH1', integral=True)    # -> float; volt-seconds
```

This function runs acquisition and returns the data, integrated over a window in the oscillogram for the indicated channel. The window can be indicated by the [`oscilloscope_window`](#oscilloscope_window) function. The integral is returned in volt-seconds. The default option is `False`.

For Rigol MSO8000 Series, it is not possible to control the number of averages in the waveform for the `'Average'` [acquisition type](#oscilloscope_acquisition_type). This function returns the waveform data on the screen or from the internal memory. There is an additional keyword `'mode' = ['Normal', 'Raw']`, which is used to specify the data return [mode](#oscilloscope_get_curve-mode).

!!! note
    This function is only available for Keysight 2000, 3000, 4000 X-Series and Rigol MSO8000 Series oscilloscopes.

---

### oscilloscope_area(channel) { #oscilloscope_area data-toc-label="oscilloscope_area" }

```python
oscilloscope_area('CH2')    # -> float; area measurement (V·s) for channel 2
```

This function returns a value of area in volt-seconds between the waveform and the ground level for specified channel of the oscilloscope. It expects one argument, namely the channel for which the area should be measured.

!!! note
    This function is available for Keysight 2000, 3000, 4000 X-Series and Rigol MSO8000 Series oscilloscopes.

---

### oscilloscope_sensitivity(*channel) { #oscilloscope_sensitivity data-toc-label="oscilloscope_sensitivity" }

```python
oscilloscope_sensitivity('CH2')             # -> str (query)
oscilloscope_sensitivity('CH2', '100 mV')   # set channel 2 sensitivity to 100 mV/div
```

This function queries (if called with one argument) or sets (if called with two arguments) the sensitivity per division of one of the channels of the oscilloscope. If there is a second argument it will be set as a new sensitivity. If there is no second argument the current sensitivity for specified the channel is returned.

**Output format:** `'number'` + `'V'` | `'mV'`
{: .enum }

---

### oscilloscope_offset(*channel) { #oscilloscope_offset data-toc-label="oscilloscope_offset" }

```python
oscilloscope_offset('CH2')             # -> str (query)
oscilloscope_offset('CH2', '100 mV')   # set channel 2 offset to 100 mV
```

This function queries (if called with one argument) or sets (if called with two arguments) the offset setting of one of the channels of the oscilloscope. If there is a second argument it will be set as a new offset setting. If there is no second argument the current offset setting for the specified channel is returned. The offset range depends on the type of oscilliscope, the vertical scale factor for used channel, and the impedance. Please, refer to device manuals.

**Output format:** `'number'` + `'V'` | `'mV'`
{: .enum }

---

### oscilloscope_horizontal_offset(*h_offset) { #oscilloscope_horizontal_offset data-toc-label="oscilloscope_horizontal_offset" }

```python
oscilloscope_horizontal_offset()            # -> str (query)
oscilloscope_horizontal_offset('100 ms')    # set time base delay to 100 ms
```

This function queries or sets the horizontal delay time (position). This delay is the time between the trigger event and the delay reference point on the screen. If there is no argument the function will return the current delay mode. If there is an argument the specified delay mode will be set. The valid range for delay settings depends on the time/division setting for the main time base.

**Output format:** `'number'` + `'s'` | `'ms'` | `'us'` | `'ns'`
{: .enum }

---

### oscilloscope_coupling(*coupling) { #oscilloscope_coupling data-toc-label="oscilloscope_coupling" }

```python
oscilloscope_coupling('CH2')          # -> str (query)
oscilloscope_coupling('CH2', 'AC')    # set channel 2 coupling to AC
```

This function queries (if called with one argument) or sets (if called with two arguments) the coupling of one of the channels of the oscilloscope. If there is a second argument it will be set as a new coupling. If there is no second argument the current coupling for the specified channel is returned.

!!! note
    For Rigol MSO8000 Series `'AC'` option is only available for `'1 M'` [impedance](#oscilloscope_impedance) setting.

**Allowed:** `'AC'`, `'DC'`
{: .enum }

---

### oscilloscope_impedance(*impedance) { #oscilloscope_impedance data-toc-label="oscilloscope_impedance" }

```python
oscilloscope_impedance('CH2')           # -> str (query)
oscilloscope_impedance('CH2', '1 M')    # set channel 2 impedance to 1 MOhm
```

This function queries (if called with one argument) or sets (if called with two arguments) the impedance of one of the channels of the oscilloscope. If there is a second argument it will be set as a new impedance. If there is no second argument the current impedance for the specified channel is returned.

!!! note
    For Keysight 2000 X-Series the only available option is `'1 M'`.

**Allowed:** `'1 M'`, `'50'`
{: .enum }

---

### oscilloscope_trigger_mode(*mode) { #oscilloscope_trigger_mode data-toc-label="oscilloscope_trigger_mode" }

```python
oscilloscope_trigger_mode()          # -> str (query)
oscilloscope_trigger_mode('Auto')    # set trigger mode to Auto
```

This function queries or sets the trigger mode of the oscilloscope. If there is no argument the function will return the current trigger mode. If there is an argument the specified trigger mode will be set. When `'Auto'` sweep mode is selected, a baseline is displayed in the absence of a signal. If a signal is present but the oscilloscope is not triggered, the unsynchronized signal is displayed instead of a baseline. When `'Normal'` sweep mode is selected and no trigger is present, the instrument does not sweep, and the data acquired on the previous trigger remains on the screen.

**Allowed:** `'Auto'`, `'Normal'`
{: .enum }

---

### oscilloscope_trigger_channel(*channel) { #oscilloscope_trigger_channel data-toc-label="oscilloscope_trigger_channel" }

```python
oscilloscope_trigger_channel()         # -> str (query)
oscilloscope_trigger_channel('CH3')    # set trigger channel to 3
```

This function queries or sets the trigger channel of the oscilloscope. If there is no argument the function will return the current trigger channel (CHANn, EXT, LINE, WGEN, NONE). If all channels are off, the query returns NONE. If there is an argument the specified trigger channel will be set.

The `'Ext'` option triggers the oscilloscope using the EXT TRIG IN signal on the rear panel. The `'Line'` option triggers the oscilloscope at 50% of the rising or falling edge of the AC power source signal. The `'WGen'` argument triggers the oscilloscope at the 50% level of the rising edge of the waveform generator output signal. This option is not available when the DC, NOISe, or CARDiac waveforms of the waveform generator are selected.

!!! note
    For Keysight 4000 X-series arguments `'WGen1'` and `'WGen2'` can be used.

    For Tektronix 3000 Series argument `'WGen'` is not available, whereas there is an additional option of the external trigger mode: `'Ext10'`. The `'Ext'` option sets the trigger source to the regular external trigger input connector with a signal input range of -0.8 V to +0.8 V. Please, note that `'Ext'` is not available in 4 channel TDS3000 Series instruments. The `'Ext10'` option sets the trigger source to the reduced external trigger with a signal input range of -8 V to +8 V. It is also not available in 4 channel TDS3000 Series instruments.

    For Tektronix 4000 Series arguments `'Ext'` and `'WGen'` are not available.

    For Rigol MSO8000 Series arguments `'WGen'` is not available.

**Allowed:** `'CH1'`, `'CH2'`, `'CH3'`, `'CH4'`, `'Ext'`, `'Line'`, `'WGen'`
{: .enum }

---

### oscilloscope_trigger_low_level(*level) { #oscilloscope_trigger_low_level data-toc-label="oscilloscope_trigger_low_level" }

```python
oscilloscope_trigger_low_level('CH2')         # -> str (query)
oscilloscope_trigger_low_level('CH2', 0.5)    # set channel 2 low trigger level to 500 mV
```

This function queries (if called with one argument) or sets (if called with two arguments) the low trigger voltage level voltage of one of the channels of the oscilloscope. If there is a second argument it will be set as a new low trigger voltage level. If there is no second argument the current low trigger voltage level for the specified channel is returned.

!!! note
    For Tektronix 3000 Series and Rigol MSO8000 Series the 'channel string' has no meaning and is kept only for consistency.

    For Tektronix 3000 and 4000 Series also presets `'ECL'` and `'TTL'` can be used as the first argument. `'ECL'` sets the threshold level to a preset ECL high level of -1.3 V. `'TTL'` sets the threshold level to a preset TTL high level of 1.4 V.

**Output format:** `'number'` + `'V'` | `'mV'`
{: .enum }

---

### oscilloscope_read_settings() { #oscilloscope_read_settings data-toc-label="oscilloscope_read_settings" }

```python
oscilloscope_read_settings()    # read all settings from digitizer.param
```

This function reads all the settings from a special text file [digitizer.param](https://github.com/Anatoly1010/Atomize_ITC/tree/master/atomize/control_center).

!!! note
    This function is only available for Keysight 2000, 3000, 4000 X-Series and Rigol MSO8000 Series oscilloscopes.

---

### oscilloscope_window() { #oscilloscope_window data-toc-label="oscilloscope_window" }

```python
oscilloscope_window()    # -> float; integration window of the oscilloscope
```

This function returns the integration window of the oscilloscope. The integration window is used in the [`oscilloscope_get_curve()`](#oscilloscope_get_curve-integral) function and is set via a special text file [digitizer.param](https://github.com/Anatoly1010/Atomize_ITC/tree/master/atomize/control_center).

!!! note
    This function is only available for Keysight 2000, 3000, 4000 X-Series and Rigol MSO8000 Series oscilloscopes.

---

### oscilloscope_command(command) { #oscilloscope_command data-toc-label="oscilloscope_command" }

```python
# cause an acquisition to be captured even though the trigger condition has not been met
oscilloscope_command(':TRIGger:FORCe')
```

This function sends an arbitrary command from a programming guide to the device in a string format. No output is expected.

---

### oscilloscope_query(command) { #oscilloscope_query data-toc-label="oscilloscope_query" }

```python
# query a measurement and output the frequency of the cycle on the screen
# closest to the trigger reference
oscilloscope_query(':MEASure:FREQuency?')    # -> str
```

This function sends an arbitrary command from a programming guide to the device in a string format. An output in a string format is expected.
