# Digitizers

## Devices

| Device                                                                          | Tested  | Library                                                                                       |
| ------------------------------------------------------------------------------- | ------- | --------------------------------------------------------------------------------------------- |
| **Spectrum M4I 4450 X8**                                                        | 08/2021 | [Spectrum](https://spectrum-instrumentation.com/en/m4i4450-x8)                                |
| **Spectrum M4I 2211 X8**                                                        | 01/2023 | [Spectrum](https://spectrum-instrumentation.com/en/m4i4450-x8)                                |
| **[Insys FM214x3GDA](https://www.insys.ru/mezzanine/fm214x3gda)**               | 03/2025 | [Atomize_ITC libs](https://github.com/Anatoly1010/Atomize_ITC/tree/master/libs)               |
| **L card L-502**                                                                | 03/2022 | [L card](https://www.lcard.ru/products/boards/l-502?qt-ltab=6#qt-ltab)                        |

The original [library](https://spectrum-instrumentation.com/en/m4i4450-x8) was written by Spectrum. The path to the library header files (`pyspcm.py`, `spcm_tools.py`) and the card device node are read from the device configuration file (the `[SPECIFIC]` section, keys `header_dir` and `device`), so they can be set per machine without editing the module:

```ini
[SPECIFIC]
header_dir = /path/to/python/header/of/Spectrum/library
device = /dev/spcm0
```

The Insys device is available via `ctypes`. The original library can be found [here](https://github.com/Anatoly1010/Atomize_ITC/tree/master/libs).

The L card device is available via `ctypes`. The original library can be found [here](https://www.lcard.ru/products/boards/l-502?qt-ltab=6#qt-ltab). The path to the installed library should be provided directly in the device module file.

## Functions

### digitizer_name() { #digitizer_name data-toc-label="digitizer_name" }

```python
digitizer_name()    # -> str; device name
```

This function returns device name.

---

### digitizer_setup() { #digitizer_setup data-toc-label="digitizer_setup" }

```python
digitizer_setup()    # write all settings into the digitizer
```

This function writes all the settings modified by other functions to the digitizer. The function should be called only without arguments. One must initialize the settings before calling [`digitizer_get_curve()`](#digitizer_get_curve).

The default settings (if no other function was called) are the following: Sample clock is 500 MHz (M4I 4450 X8) or 1250 MHz (M4I 2211 X8); Clock mode is `Internal`; Reference clock is 100 MHz; Card mode is `Single`; Trigger channel is `External`; Trigger mode is `Positive`; Number of averages is 2; Trigger delay is 0; Enabled channels are CH0 and CH1; Input mode is `HF` (M4I 4450 X8); Coupling of CH0 and CH1 is `DC`; Impedance of CH0 and CH1 is `50`; Horizontal offset of CH0 and CH1 is 0%; Range of CH0 is `500 mV`; Range of CH1 is `500 mV`; Number of points is 128 (M4I 4450 X8) or 256 (M4I 2211 X8); Posttrigger points is 64.

!!! note
    This function is not available for Insys FM214x3GDA. This is done by
    [`pulser_open()`](pulse_programmer.md#pulser_open) function.

---

### digitizer_get_curve() { #digitizer_get_curve data-toc-label="digitizer_get_curve" }

```python
# Two channels enabled -> 3 arrays
xs, data_ch0, data_ch1 = digitizer_get_curve()

# One channel enabled  -> 2 arrays
xs, data_ch0 = digitizer_get_curve()
```

This function runs acquisition and returns the data obtained. If two channels are enabled by the function [`digitizer_channel()`](#digitizer_channel) the output of the function is three numpy arrays (`xs`, `data_ch0`, `data_ch1`). If one channel is enabled the output of the function is two numpy array (`xs`, `data_ch0`). The `xs` array is returned in s, data arrays are returned in V. The function should be called only without arguments.

In the case of Insys FM214x3GDA one should use the modification of this function [`digitizer_get_curve(points, phases, ...)`](#digitizer_get_curve-points).

---

### digitizer_get_curve(integral=True) { #digitizer_get_curve-integral }

```python
# Two channels -> 2 floats (volt-seconds)
i_ch0, i_ch1 = digitizer_get_curve(integral=True)

# One channel  -> 1 float
i_ch0 = digitizer_get_curve(integral=True)
```

This function runs acquisition and returns the data, integrated over a window in the oscillogram, indicated by the [`digitizer_window`](#digitizer_window) function. If two channels are enabled by the function [`digitizer_channel()`](#digitizer_channel) the output of the function is two numbers (`integral_ch0`, `integral_ch1`). If one channel is enabled the output of the function is one number (`integral_ch0`). The integral is returned in volt-seconds. The default option is `False`.

In the case of Insys FM214x3GDA one should use the modification of this function [`digitizer_get_curve(points, phases, ...)`](#digitizer_get_curve-points).

---

### digitizer_get_curve(points, phases, ...) { #digitizer_get_curve-points }

```python
# Phase-cycled acquisition: 100 points, 2 phases
data_i, data_q = digitizer_get_curve(100, 2)

# With explicit keyword arguments
data_i, data_q = digitizer_get_curve(
    100, 2, live_mode=0, integral=False,
    current_scan=1, total_scan=1, skip_redundant=False)
```

This function starts the data acquisition and [phase cycling](pulse_programmer.md#pulser_acquisition_cycle) the data. The argument `points` indicates the total number of points in the pulse experiment and the argument `phases` corresponds to the total number of phases in the pulse experiment. The data will be phase cycled according to the phase list given in the [`DETECTION` pulse](pulse_programmer.md#pulser_pulse). The details of phase cycling are given in the function [`pulser_acquisition_cycle()`](pulse_programmer.md#pulser_acquisition_cycle). A keyword `integral` allows integrating the data over a given [window](#digitizer_read_settings). The keywords `current_scan` and `total_scan` indicate the current and total number of repetitive scans in the experiment to maximize the efficiency of the Insys FM214x3GDA. The value of the keyword `current_scan` should increase during the experiment.

The keyword `live_mode` controls the accumulation behaviour. In the default mode (`live_mode=0`) every transferred buffer is summed into the running on-board average, so the returned arrays correspond to all the data accumulated so far. In `live_mode=1` the running accumulators are reset on entry and the function returns a snapshot of only the buffers that arrived since the previous call; this is intended for live plotting. The keyword `skip_redundant` affects how repeated packets of the same point are treated: with the default `False` every parsed packet contributes to the running average (correct on-board-averaging semantics), while `True` makes only the first packet of each consecutive run of the same point contribute. If no new buffer has been transferred from the card at the time of execution the function returns `None, None` (see also [`digitizer_at_exit()`](#digitizer_at_exit)).

!!! note "Performance tip"
    Since the function returns `None, None` when no new buffer has been transferred,
    guard the returned data with an `is not None` check and only run the
    (relatively expensive) plotting/processing when fresh data is available:

    ```python
    a, b = digitizer_get_curve(POINTS, PHASES, current_scan = k, total_scan = SCANS)

    if a is not None:
        data[0], data[1] = a, b
        process = general.plot_2d(EXP_NAME, data, ..., pr = process)
    ```

    Skipping the plot call on empty acquisitions avoids redundant work and keeps
    the acquisition loop fast.

---

### digitizer_close() { #digitizer_close data-toc-label="digitizer_close" }

```python
digitizer_close()    # close the digitizer driver
```

This function closes the digitizer driver and should be called only without arguments. The function should always be called at the end of an experimental script.

!!! note
    This function is not available for Insys FM214x3GDA. This is done with
    [`pulser_close()`](pulse_programmer.md#pulser_close).

---

### digitizer_stop() { #digitizer_stop data-toc-label="digitizer_stop" }

```python
digitizer_stop()    # stop the digitizer
```

This function stops the digitizer and should be called only without arguments. The function should always be called before redefining digitizer settings by the [`digitizer_setup()`](#digitizer_setup) function.

!!! note
    This function is not available for Insys FM214x3GDA, L card L-502.
    There is no need to stop these ADC.

---

### digitizer_number_of_points(*points) { #digitizer_number_of_points data-toc-label="digitizer_number_of_points" }

```python
digitizer_number_of_points()       # -> int (query)
digitizer_number_of_points(128)    # set value
```

This function queries or sets the number of points in samples in the returned oscillogram. The number of points should be divisible by 16 samples (M4I 4450 X8) or by 32 samples (M4I 2211 X8), the minimum available value is 32 samples (M4I 4450 X8) or 64 samples (M4I 2211 X8). If there is no setting fitting the argument the nearest available value is used and warning is printed. Default value is 128 (M4I 4450 X8) or 256 (M4I 2211 X8). The difference between number of points and [posttrigger points](#digitizer_posttrigger) should be less than 8000. If it is not the case the nearest available number of points is used and warning is printed.

!!! note
    This function is not available for Insys FM214x3GDA. The number of
    points is controlled by the trigger pulse length.

---

### digitizer_posttrigger(*post_points) { #digitizer_posttrigger data-toc-label="digitizer_posttrigger" }

```python
digitizer_posttrigger()      # -> int (query)
digitizer_posttrigger(64)    # default
```

This function queries or sets the number of posttriger (horizontal offset) points in samples in the returned oscillogram. The number of posttriger points should be divisible by 16 samples (M4I 4450 X8) or by 32 samples (M4I 2211 X8), the minimum available value is 16 samples (M4I 4450 X8) or 32 samples (M4I 2211 X8). In the [`Average`](#digitizer_card_mode) card mode, the maximum available value is [number of points](#digitizer_number_of_points) in the oscillogram minus 16 samples (M4I 4450 X8) or minus 32 samples (M4I 2211 X8). If there is no setting fitting the argument the nearest available value is used and warning is printed. Default value is 64. The difference between [number of points](#digitizer_number_of_points) and posttrigger points should be less than 8000. If it is not the case the nearest available value of posttrigger points is used and warning is printed.

!!! note
    This function is not available for Insys FM214x3GDA, L card L-502.

---

### digitizer_channel(*channel) { #digitizer_channel data-toc-label="digitizer_channel" }

```python
digitizer_channel()                # -> str (query)
digitizer_channel('CH0', 'CH1')    # default: both
digitizer_channel('CH0')           # only CH0
```

This function enables the specified channel or queries enabled channels. If there is no argument the function will return the currently enabled channels. If there is an argument the output from the specified channel will be enabled. Default option is when both channels are enabled.

**Allowed:** `'CH0'`, `'CH1'`
{: .enum }

!!! note
    This function is not available for Insys FM214x3GDA, L card L-502.

---

### digitizer_sample_rate(*s_rate) { #digitizer_sample_rate data-toc-label="digitizer_sample_rate" }

```python
digitizer_sample_rate()       # -> float, MHz (query)
digitizer_sample_rate(500)    # 500 MHz
```

This function queries or sets the digitizer sample rate (in MHz). If there is no argument the function will return the current sample rate. If there is an argument the specified sample rate will be set. If there is no setting fitting the argument the nearest available value is used and warning is printed. Default value is 500 MHz (M4I 4450 X8) or 1250 MHz (M4I 2211 X8).

**Allowed (M4I 4450 X8):** `[500, 250, 125, ..., 0.001907]` MHz
{: .enum }

**Allowed (M4I 2211 X8):** `[1250, 625, 312.5, ..., 0.009536]` MHz
{: .enum }

**Range (M4I 4450 X8):** `1.907 kHz` – `500 MHz`
{: .enum }

**Range (M4I 2211 X8):** `9.536 kHz` – `1250 MHz`
{: .enum }

!!! note
    This function only returns the current sample rate for Insys FM214x3GDA.
    See also [`digitizer_decimation()`](#digitizer_decimation).
    This function is not available for L card L-502.

---

### digitizer_clock_mode(*mode) { #digitizer_clock_mode data-toc-label="digitizer_clock_mode" }

```python
digitizer_clock_mode()              # -> str (query)
digitizer_clock_mode('Internal')    # default
digitizer_clock_mode('External')
```

This function queries or sets the digitizer clock mode. If there is no argument the function will return the current clock mode setting. If there is an argument the specified clock mode will be set.

According to the documentation, the internal sampling clock is generated in default mode by a programmable high precision quartz. The external clock input of the M3i/M4i series is fed through a PLL to the clock system. Therefore the input will act as a reference clock input thus allowing to either use a copy of the external clock or to generate any sampling clock within the allowed range from the reference clock. Due to the fact that the driver needs to know the external fed in frequency for an exact calculation of the sampling rate the reference clock should be set by the [`digitizer_reference_clock()`](#digitizer_reference_clock) function. Default setting is `Internal`.

**Allowed:** `'Internal'`, `'External'`
{: .enum }

!!! note
    This function is not available for Insys FM214x3GDA.

---

### digitizer_reference_clock(*ref_clock) { #digitizer_reference_clock data-toc-label="digitizer_reference_clock" }

```python
digitizer_reference_clock()       # -> int, MHz (query)
digitizer_reference_clock(100)    # default: 100 MHz
```

This function queries or sets the digitizer reference clock (in MHz) for `External` mode of the [`digitizer_clock_mode()`](#digitizer_clock_mode) function. If there is no argument the function will return the current reference clock. If there is an argument the specified reference clock will be set. Default value is 100 MHz.

**Range:** `10 MHz` – `100 MHz`
{: .enum }

!!! note
    This function is not available for Insys FM214x3GDA.

---

### digitizer_card_mode(*mode) { #digitizer_card_mode data-toc-label="digitizer_card_mode" }

```python
digitizer_card_mode()            # -> str (query)
digitizer_card_mode('Single')    # default
digitizer_card_mode('Average')
```

This function queries or sets the digitizer mode. If there is no argument the function will return the current digitizer mode. If there is an argument the specified mode will be set.

According to the documentation, in the `Single` mode data acquisition is carried out to on-board memory for one single trigger event. In `Average` (Multi) mode the memory is segmented and with each trigger condition one segment is acquired. After that the data is transfer to the PC memory and [averaged](#digitizer_get_curve) or [averaged and integrated](#digitizer_get_curve-integral). The number of segments to acquire can be set by the [`digitizer_number_of_averages()`](#digitizer_number_of_averages) function. Default setting is `Single`.

**Allowed:** `'Single'`, `'Average'`
{: .enum }

!!! note
    This function is not available for Insys FM214x3GDA, L card L-502.

---

### digitizer_trigger_channel(*ch) { #digitizer_trigger_channel data-toc-label="digitizer_trigger_channel" }

```python
digitizer_trigger_channel()              # -> str (query)
digitizer_trigger_channel('External')    # default; = Trg0
digitizer_trigger_channel('Software')
```

This function queries or sets the digitizer trigger channel. If there is no argument the function will return the current trigger channel. If there is an argument the specified channel will be used as trigger. Trigger channel `External` corresponds to `Trg0` channel of the digitizer. Default setting is `External`.

**Allowed:** `'Software'`, `'External'`
{: .enum }

!!! note
    This function is not available for Insys FM214x3GDA, L card L-502.

---

### digitizer_trigger_mode(*mode) { #digitizer_trigger_mode data-toc-label="digitizer_trigger_mode" }

```python
digitizer_trigger_mode()              # -> str (query)
digitizer_trigger_mode('Positive')    # default
```

This function queries or sets the digitizer trigger mode. If there is no argument the function will return the current trigger mode. If there is an argument the specified trigger mode will be set. Mode `Positive` corresponds to trigger detection for positive edges (crossing level 0 from below to above). `Negative` to trigger detection for negative edges (crossing level 0 from above to below). `High` to trigger detection for HIGH levels (signal above level 0). `Low` to trigger detection for LOW levels (signal below level 0). Default setting is `Positive`.

**Allowed:** `'Positive'`, `'Negative'`, `'High'`, `'Low'`
{: .enum }

!!! note
    This function is not available for Insys FM214x3GDA, L card L-502.

---

### digitizer_number_of_averages(*averages) { #digitizer_number_of_averages data-toc-label="digitizer_number_of_averages" }

```python
digitizer_number_of_averages()     # -> int (query)
digitizer_number_of_averages(2)    # default
```

This function queries or sets the number of averages for [`Average`](#digitizer_card_mode) card mode. If there is no argument the function will return the current number of averages. If there is an argument the specified number of averages will be set. If a very large number of [points](#digitizer_number_of_points) are set, the maximum available number of averages may be limited by the digitizer memory. This limit is 1 Gs. Default value is 2.

**Max:** `10000`
{: .enum }

!!! note
    This function is not available for L card L-502.

---

### digitizer_trigger_delay(*delay) { #digitizer_trigger_delay data-toc-label="digitizer_trigger_delay" }

```python
digitizer_trigger_delay()           # -> str (query)
digitizer_trigger_delay('32 ns')    # default: '0 ns'
```

This function queries or sets the digitizer trigger delay. If there is no argument the function will return the current trigger delay. If there is an argument the specified trigger delay will be set. The delay step is 16 samples (M4I 4450 X8) or 32 samples (M4I 2211 X8). If an input is not divisible by 16 samples (M4I 4450 X8) or by 32 samples (M4I 2211 X8) the delay will be rounded and a warning message will be printed. Default value is `0 ns`.

!!! note
    This function is not available for Insys FM214x3GDA, L card L-502.

---

### digitizer_input_mode(*mode) { #digitizer_input_mode data-toc-label="digitizer_input_mode" }

```python
digitizer_input_mode()        # -> str (query)
digitizer_input_mode('HF')    # default
digitizer_input_mode('Buffered')
```

This function queries or sets the input mode for the channels of the digitizer. If there is no argument the function will return the current input mode. If there is an argument the specified input mode will be set. The input mode will be used for both channels. According to the documentation, HF mode allows using a high frequency 50 Ohm path to have full bandwidth and best dynamic performance. Buffered mode allows using a buffered path with all features but limited bandwidth and dynamic performance. Default value is `HF`.

**Allowed:** `'HF'`, `'Buffered'`
{: .enum }

!!! note
    This function is not available for M4I 2211 X8, Insys FM214x3GDA, and
    L card L-502.

---

### digitizer_amplitude(*ampl) { #digitizer_amplitude data-toc-label="digitizer_amplitude" }

```python
digitizer_amplitude()        # -> str (query)
digitizer_amplitude(500)     # default: ±500 mV
digitizer_amplitude(1000)    # ±1 V
```

This function queries or sets the input ranges of the digitizer channels. If there is no argument the function will return the range of the digitizer channels. If there is an argument the specified range (in mV) will be set. The given range will be used for both channels. If there is no range setting fitting the argument the nearest available value is used and warning is printed. Default value is `500 mV`.

**Allowed (M4I 4450 X8, `Buffered`):** `200`, `500`, `1000`, `2000`, `5000`, `10000` mV
{: .enum }

**Allowed (M4I 4450 X8, `HF`):** `500`, `1000`, `2500`, `5000` mV
{: .enum }

**Allowed (M4I 2211 X8):** `200`, `500`, `1000`, `2500` mV
{: .enum }

!!! note
    This function is not available for Insys FM214x3GDA, the maximum
    amplitude in this case of about 1500 mV.
    This function is not available for L card L-502.

---

### digitizer_offset(*offset) { #digitizer_offset data-toc-label="digitizer_offset" }

```python
digitizer_offset()                           # -> (str, str)
digitizer_offset('CH0', '1', 'CH1', '50')    # both channels
digitizer_offset('CH0', '1')                 # only CH0
```

This function queries or sets the vertical offset of the digitizer channels. If there is no argument the function will return the offset of the both digitizer channels. If there is an argument the specified offset (as a percentage of the input range) will be set for the specified channel. For M4I 4450 X8 the value of the offset (range × argument) is ALWAYS substracted from the signal. The step is 1%. According to the M4I 4450 X8 documentation, no offset can be used for 1000 mV and 10000 mV range in the [`Buffered` input mode](#digitizer_input_mode). Default value is `0` for both channels.

!!! note
    This function is not available for Insys FM214x3GDA, L card L-502.

---

### digitizer_coupling(*coupling) { #digitizer_coupling data-toc-label="digitizer_coupling" }

```python
digitizer_coupling()                            # -> (str, str)
digitizer_coupling('CH0', 'DC', 'CH1', 'DC')    # default
digitizer_coupling('CH0', 'AC', 'CH1', 'DC')
```

This function queries or sets the coupling of the digitizer channels. If there is no argument the function will return the coupling of the both digitizer channels. If there is an argument the specified coupling will be set for the specified channel. Default value is `DC` for both channels.

**Allowed:** `'AC'`, `'DC'`
{: .enum }

!!! note
    This function is not available for Insys FM214x3GDA, L card L-502.

---

### digitizer_impedance(*impedance) { #digitizer_impedance data-toc-label="digitizer_impedance" }

```python
digitizer_impedance()                            # -> (str, str)
digitizer_impedance('CH0', '50', 'CH1', '50')    # default
digitizer_impedance('CH0', '50', 'CH1', '1 M')
```

This function queries or sets the impedance of the digitizer channels. If there is no argument the function will return the impedance of the both digitizer channels. If there is an argument the specified impedance will be set for the specified channel. Please note that in the [HF input mode](#digitizer_input_mode) impedance is fixed at 50 Ohm. Default value is `50` for both channels.

**Allowed:** `'1 M'`, `'50'`
{: .enum }

!!! note
    This function is not available for M4I 2211 X8, Insys FM214x3GDA, and
    L card L-502. For these digitizers the impedance is fixed at 50 Ohm.

---

### digitizer_decimation(*dec) { #digitizer_decimation data-toc-label="digitizer_decimation" }

```python
digitizer_decimation()     # -> int (query)
digitizer_decimation(1)    # 0.4 ns/point
digitizer_decimation(2)    # 0.8 ns/point
digitizer_decimation(4)    # 1.6 ns/point
```

This function queries or sets the decimation coefficient for Insys FM214x3GDA. If there is no argument the function will return the decimation coefficient of the digitizer. If there is an argument the specified decimation will be set. It can be used instead of the function [`digitizer_sample_rate()`](#digitizer_sample_rate). The values 1, 2, 4 correspond to 0.4 ns/point, 0.8 ns/point, and 1.6 ns/point. The decimation coefficient is also used by the [`digitizer_iq()`](#digitizer_iq) function to build the time axis. This function should be called before [`pulser_open()`](pulse_programmer.md#pulser_open).

**Allowed:** `1`, `2`, `4`
{: .enum }

---

### digitizer_flow(*flow) { #digitizer_flow data-toc-label="digitizer_flow" }

```python
digitizer_flow()         # -> str (query)
digitizer_flow('ADC')    # default
```

This function sets or queries enabled flows of data. If there is no argument the function will return the enabled flow of data of the digitizer. If there is an argument the specified flow will be set. The default option is `ADC`. This function is available only for L card L-502.

**Allowed:** `'ADC'`, `'DIN'`, `'DAC1'`, `'DAC2'`, `'DOUT'`, `'AIN'`, `'AOUT'`
{: .enum }

---

### digitizer_read_settings() { #digitizer_read_settings data-toc-label="digitizer_read_settings" }

```python
digitizer_read_settings()    # read settings from digitizer.param
```

This function reads all the settings from a special text file [`digitizer.param`](https://github.com/Anatoly1010/Atomize_ITC/tree/master/atomize/control_center) and writes them to the digitizer using the [`digitizer_setup()`](#digitizer_setup) function.

!!! note
    This function is not available for L card L-502.

---

### digitizer_window() { #digitizer_window data-toc-label="digitizer_window" }

```python
digitizer_window()    # -> float; integration window
```

This function returns the integration window of the digitizer. The integration window is used in the [`digitizer_get_curve()`](#digitizer_get_curve-integral) function and is set via a special text file [`digitizer.param`](https://github.com/Anatoly1010/Atomize_ITC/tree/master/atomize/control_center).

!!! note
    This function is not available for L card L-502.

---

### digitizer_window_points() { #digitizer_window_points data-toc-label="digitizer_window_points" }

```python
digitizer_window_points()    # -> int; points in the window
```

This function returns the number of points in the digitizer window. The window is used in the [`digitizer_get_curve()`](#digitizer_get_curve-points) function. The number of points in the window can be set as the length of the [`DETECTION` pulse](pulse_programmer.md#pulser_pulse).

!!! note
    This function is available only for Insys FM214x3GDA.

---

### digitizer_at_exit(integral=False) { #digitizer_at_exit data-toc-label="digitizer_at_exit" }

```python
digitizer_at_exit()                 # -> arrays
digitizer_at_exit(integral=True)    # -> integrated arrays
```

This function is available only for Insys FM214x3GDA and is similar to the [`digitizer_get_curve()`](#digitizer_get_curve-integral) function. The main difference is that this function always return the current accumulated arrays, while [`digitizer_get_curve()`](#digitizer_get_curve-integral) may return `np.nan` if no new buffer has been transferred from the card to the computer at the time of execution.

---

### digitizer_iq(arr_i, arr_q, freq, ph, ph1, ph2, integral=False) { #digitizer_iq data-toc-label="digitizer_iq" }

```python
# Software down-conversion of the quadrature data
data_i, data_q = digitizer_iq(data_i, data_q, freq, ph, ph1, ph2)

# With integration over the window
res_i, res_q = digitizer_iq(
    data_i, data_q, freq, ph, ph1, ph2, integral=True)
```

This function performs a software digital down-conversion (IQ demodulation) with phase correction of the quadrature data returned by the [`digitizer_get_curve()`](#digitizer_get_curve-points) function. The arguments `arr_i` and `arr_q` are the in-phase and quadrature arrays (both 1D and 2D arrays are accepted). The complex signal `arr_i + 1j*arr_q` is multiplied by `exp(-1j*(2*pi*freq*t + ph + ph1*t + ph2*t**2))`, where `t` is the time axis built from the current sampling frequency. For Insys FM214x3GDA this frequency is `2.5 GHz` divided by the [decimation](#digitizer_decimation) coefficient; for the Spectrum M4I.4450-X8 and M4I.2211-X8 digitizers it is the configured [sample rate](#digitizer_sample_rate). The argument `freq` (in MHz) is the down-conversion frequency offset, `ph` is the zero-order (constant) phase correction in radians, while `ph1` and `ph2` are the first- and second-order phase-correction coefficients. The first- and second-order terms are applied only if at least one of them is nonzero.

If the keyword `integral` is `True` and the input arrays are 2D, the corrected data is integrated over the [window](#digitizer_window) and two 1D arrays (`res_i`, `res_q`) are returned; otherwise the corrected in-phase and quadrature arrays are returned. If the input arrays contain `np.nan` (no new data) they are returned unchanged.

!!! note
    This function is available for Insys FM214x3GDA and the Spectrum M4I.4450-X8 / M4I.2211-X8 digitizers.

---

### digitizer_expand_phase_cycling(p_input, *pulse_args) { #digitizer_expand_phase_cycling data-toc-label="digitizer_expand_phase_cycling" }

```python
# One pulse cycled +x, -x; receiver derived from the detection spec
result = digitizer_expand_phase_cycling('[x]', '(x)')
# -> {'pulses': [['+x', '-x']], 'receiver': ['+x', '+y']}

# CYCLOPS-style receiver from coefficients and two cycled pulses
result = digitizer_expand_phase_cycling([-1, 2], '[x]', '(x)')
# -> {'pulses': [['+x', '+y', '-x', '-y', '+x', '+y', '-x', '-y'],
#                ['+x', '+x', '+x', '+x', '-x', '-x', '-x', '-x']],
#     'receiver': ['+x', '-y', '-x', '+y', '+x', '-y', '-x', '+y']}
```

This function expands a compact phase-cycling notation into explicit per-pulse phase lists together with the matching receiver (detection) phase cycle. The argument `p_input` specifies the receiver: it is either a phase string/list (used directly as the receiver phase list) or a list/string of coefficients, in which case the receiver phase of each step is computed as the weighted sum of the pulse phase indices (CYCLOPS-style). Each of the `*pulse_args` arguments describes one pulse.

The phase symbols are `'+x'`, `'+y'`, `'-x'`, `'-y'` (the shorthands `+`, `-`, `i`, `-i` are also accepted). A nested `[...]` group expands the enclosed phase into a four-step (quadrature) cycle, a nested `(...)` group into a two-step cycle, and a comma-separated string (e.g. `'+x,-x'`) is treated as an explicit list. The lengths of the individual cycles are combined so that all pulses share a common cycle length.

The function returns a dictionary with two keys: `'pulses'` (a list of phase lists, one per pulse, to be passed to the [`phase_list`](pulse_programmer.md#pulser_pulse) of the corresponding pulse) and `'receiver'` (the phase list of the [`DETECTION` pulse](pulse_programmer.md#pulser_pulse) used to [phase cycle](#digitizer_get_curve-points) the data).

!!! note
    This function is available for Insys FM214x3GDA, Spectrum M4I 4450 X8, and Spectrum M4I 2211 X8.
