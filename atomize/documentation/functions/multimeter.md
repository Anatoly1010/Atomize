# Multimeters

## Devices

| Device                         | Tested   | Connection             |
| ------------------------------ | -------- | ---------------------- |
| **Agilent / Keysight 34410A**  | Untested | GPIB, Ethernet (LAN)   |

## Functions

The `Agilent_34410A` driver supports GPIB and LAN connections. The supplied configuration defaults to GPIB address `22` with a `10000 ms` timeout. For LAN, set `DEFAULT.type` to `ethernet` and edit `ETHERNET.address`; the supplied `TCPIP::169.254.4.10::INSTR` address must match your instrument. USB is not implemented by this driver. On connection the driver checks `*IDN?` and requires a 34410A; it does not issue `*TST?` or reset the instrument.

Setting functions query the instrument when called without an argument, except the fixed auto-zero state for four-wire resistance. Setters return `None`. Settings apply to the currently selected measurement mode. The function reference follows the [34410A user guide](https://www.keysight.com/us/en/assets/9018-05586/user-manuals/9018-05586.pdf) and [programming quick reference](https://www.keysight.com/us/en/assets/9018-61141/programming-guides/9018-61141.pdf).

```python
import atomize.device_modules.Agilent_34410A as agilent

dmm = agilent.Agilent_34410A()
```

If the active device configuration directory already exists and does not contain `Agilent_34410A_config.ini`, copy only this new file from `atomize/device_modules/config/` into the directory returned by `atomize.main.local_config.load_config_device()` and edit its connection settings as needed. Preserve existing machine-specific configuration.

Test mode stores simulated settings and returns zero-valued readings without hardware I/O. The simulated `'External'` trigger proceeds immediately. Invalid arguments raise `AssertionError` in test mode and `ValueError` in a real run. Run the example with `python atomize/script_examples/devices_tests/ask_Agilent_34410A.py test` on Windows, or use `python3` on Linux.

### multimeter_name() { #multimeter_name data-toc-label="multimeter_name" }

```python
multimeter_name()    # -> str; instrument identification
```

This function returns the instrument identification string from `*IDN?`. In test mode it returns the configured device name.

---

### multimeter_mode(*mode) { #multimeter_mode data-toc-label="multimeter_mode" }

```python
multimeter_mode()                 # -> str; current measurement mode
multimeter_mode('DC Voltage')     # select DC voltage
```

This function selects or queries the measurement mode. Allowed values are `'DC Voltage'`, `'AC Voltage'`, `'DC Current'`, `'AC Current'`, `'Resistance 2W'`, `'Resistance 4W'`, `'Capacitance'`, `'Frequency'`, `'Period'`, `'Temperature'`, `'Continuity'`, and `'Diode'`. Range and autorange settings are not supported in `'Temperature'`, `'Continuity'`, or `'Diode'` mode.

Selecting a mode retains its measurement settings. For temperature measurements, configure the probe and temperature units using [`multimeter_command()`](#multimeter_command) before acquiring data.

---

### multimeter_range(*range_value) { #multimeter_range data-toc-label="multimeter_range" }

```python
multimeter_range()          # -> float; current range in SI units
multimeter_range('10 V')    # set DC voltage range to 10 V
```

This function sets or queries the range for the current mode. A setter accepts a numeric SI value or a string with a supported unit. Setting a fixed range disables autoranging. The returned value is a float in volts, amperes, ohms, or farads, depending on the mode. This setting is unavailable in `'Temperature'`, `'Continuity'`, and `'Diode'` modes. Frequency and period use input voltage ranges, so their range values are in volts.

| Mode | Allowed ranges |
| ---- | -------------- |
| `'DC Voltage'` | `100 mV`, `1 V`, `10 V`, `100 V`, `1000 V` |
| `'AC Voltage'` | `100 mV`, `1 V`, `10 V`, `100 V`, `750 V` |
| `'DC Current'`, `'AC Current'` | `100 uA`, `1 mA`, `10 mA`, `100 mA`, `1 A`, `3 A` |
| `'Resistance 2W'`, `'Resistance 4W'` | `100 Ohm`, `1 kOhm`, `10 kOhm`, `100 kOhm`, `1 MOhm`, `10 MOhm`, `100 MOhm`, `1 GOhm` |
| `'Capacitance'` | `1 nF`, `10 nF`, `100 nF`, `1 uF`, `10 uF` |
| `'Frequency'`, `'Period'` | `100 mV`, `1 V`, `10 V`, `100 V`, `750 V` |

Supported unit strings are `mV` and `V` for voltage; `uA`, `mA`, and `A` for current; `Ohm`, `kOhm`, `MOhm`, and `GOhm` for resistance; and `nF`, `uF`, and `F` for capacitance. Only the listed ranges are accepted.

---

### multimeter_autorange(*autorange) { #multimeter_autorange data-toc-label="multimeter_autorange" }

```python
multimeter_autorange()          # -> str; current autorange state
multimeter_autorange('On')      # enable autoranging
```

This function enables, disables, or queries autoranging for the current measurement mode. Allowed setter values are `'On'`, `'Off'`, and `'Once'`. The `'Once'` option selects a range once and then disables autoranging. The getter returns `'On'` or `'Off'`. This setting is unavailable in `'Temperature'`, `'Continuity'`, and `'Diode'` modes.

---

### multimeter_nplc(*nplc) { #multimeter_nplc data-toc-label="multimeter_nplc" }

```python
multimeter_nplc()        # -> float; integration in power-line cycles
multimeter_nplc(1)       # set integration to 1 power-line cycle
```

This function sets or queries the integration time in power-line cycles for `'DC Voltage'`, `'DC Current'`, `'Resistance 2W'`, `'Resistance 4W'`, or `'Temperature'` mode. Allowed values are `0.006`, `0.02`, `0.06`, `0.2`, `1`, `2`, `10`, and `100`.

Setting NPLC selects integration based on the power-line frequency and disables aperture mode. Choose integer power-line cycles for line-frequency noise rejection.

---

### multimeter_integration_time(*integration_time) { #multimeter_integration_time data-toc-label="multimeter_integration_time" }

```python
multimeter_integration_time()            # -> float; aperture in seconds
multimeter_integration_time('100 ms')    # set aperture to 100 ms
```

This function sets or queries the measurement aperture in seconds for `'DC Voltage'`, `'DC Current'`, `'Resistance 2W'`, `'Resistance 4W'`, or `'Temperature'` mode. Setters accept a numeric value in seconds or a string using `s`, `ms`, or `us`. The allowed range is `100 us` to `1 s`.

Setting an aperture selects integration in seconds instead of NPLC. The instrument may quantize the requested value; the getter returns the instrument's value.

---

### multimeter_ac_filter(*ac_filter) { #multimeter_ac_filter data-toc-label="multimeter_ac_filter" }

```python
multimeter_ac_filter()            # -> float; filter frequency in Hz
multimeter_ac_filter('20 Hz')     # set filter to 20 Hz
```

This function sets or queries the AC filter frequency for `'AC Voltage'`, `'AC Current'`, `'Frequency'`, or `'Period'` mode. Setters accept a numeric value in Hz or a string using `Hz` or `kHz`. Allowed values are `3`, `20`, and `200 Hz`. For frequency and period modes the value sets the low-frequency limit.

---

### multimeter_gate_time(*gate_time) { #multimeter_gate_time data-toc-label="multimeter_gate_time" }

```python
multimeter_gate_time()            # -> float; gate time in seconds
multimeter_gate_time('100 ms')    # set gate time to 100 ms
```

This function sets or queries the gate time in `'Frequency'` or `'Period'` mode. Setters accept a numeric value in seconds or a string using `s`, `ms`, or `us`. Allowed values are `1 ms`, `10 ms`, `100 ms`, and `1 s`.

---

### multimeter_auto_zero(*auto_zero) { #multimeter_auto_zero data-toc-label="multimeter_auto_zero" }

```python
multimeter_auto_zero()             # -> str; current auto-zero state
multimeter_auto_zero('On')         # enable auto-zero
multimeter_auto_zero('Once')       # perform one auto-zero cycle
```

This function sets or queries auto-zero in `'DC Voltage'`, `'DC Current'`, or `'Resistance 2W'` mode. Allowed setter values are `'On'`, `'Off'`, and `'Once'`. The `'Once'` option performs one zero measurement and then switches auto-zero off; the getter returns `'On'` or `'Off'`. In `'Resistance 4W'` mode the getter always returns `'On'`, and passing a setter argument is rejected. Temperature auto-zero is controlled through raw SCPI and is not handled by this function.

---

### multimeter_sample_count(*count) { #multimeter_sample_count data-toc-label="multimeter_sample_count" }

```python
multimeter_sample_count()       # -> int; samples per trigger
multimeter_sample_count(10)     # acquire 10 samples per trigger
```

This function sets or queries the number of samples acquired per trigger using `SAMP:COUN`. The allowed range is `1` to `50000`. This setting is the sample count, not the trigger count (`TRIG:COUN`).

---

### multimeter_trigger_source(*source) { #multimeter_trigger_source data-toc-label="multimeter_trigger_source" }

```python
multimeter_trigger_source()               # -> str; current trigger source
multimeter_trigger_source('Immediate')    # start without an external trigger
```

This function sets or queries the trigger source. Allowed values are `'Immediate'`, `'External'`, and `'Bus'`. Use `'Bus'` with [`multimeter_start()`](#multimeter_start), [`multimeter_trigger()`](#multimeter_trigger), and [`multimeter_fetch()`](#multimeter_fetch).

---

### multimeter_trigger_delay(*delay) { #multimeter_trigger_delay data-toc-label="multimeter_trigger_delay" }

```python
multimeter_trigger_delay()           # -> str or float; 'Auto' or seconds
multimeter_trigger_delay('Auto')     # enable automatic delay
multimeter_trigger_delay('10 ms')    # set delay to 10 ms
```

This function sets or queries trigger delay. The getter returns `'Auto'` when automatic delay is enabled and a float in seconds otherwise. Setters accept `'Auto'`, a numeric value in seconds, or a string using `s`, `ms`, or `us`; the allowed numeric range is `0` to `3600 s`.

The delay precedes the first sample after a trigger. Continuity and diode measurements ignore this setting.

---

### multimeter_get_data() { #multimeter_get_data data-toc-label="multimeter_get_data" }

```python
multimeter_get_data()    # -> float for one sample, otherwise 1D numpy.ndarray
```

This function starts an acquisition with `READ?` and returns its readings using the current measurement and trigger settings. It returns a float for one returned reading, or a one-dimensional `numpy.ndarray` for multiple readings. It rejects the `'Bus'` trigger source; use the explicit start, trigger, and fetch sequence for bus-triggered acquisitions.

With `'External'` triggering, the call waits for the external trigger. Set the connection timeout long enough for all triggers, delays, and measurements to complete. The number of returned readings depends on both the sample count and the trigger count; reset sets the trigger count to one. Reading units follow the selected function: volts, amperes, ohms, farads, hertz, seconds, or the configured temperature unit. Continuity returns resistance and diode mode returns voltage.

---

### multimeter_start() { #multimeter_start data-toc-label="multimeter_start" }

```python
multimeter_start()    # arm or start an acquisition
```

This function sends `INIT` to arm an acquisition and clear previous readings. Acquisition begins immediately for the `'Immediate'` source and waits for a trigger for `'External'` or `'Bus'`. It does not wait for completion or return a value. For a bus trigger, call [`multimeter_trigger()`](#multimeter_trigger) after starting and then retrieve the data with [`multimeter_fetch()`](#multimeter_fetch).

---

### multimeter_trigger() { #multimeter_trigger data-toc-label="multimeter_trigger" }

```python
multimeter_trigger()    # issue a software bus trigger
```

This function issues a software trigger when the configured source is `'Bus'`. Call [`multimeter_start()`](#multimeter_start) first. It does not return a value.

---

### multimeter_fetch() { #multimeter_fetch data-toc-label="multimeter_fetch" }

```python
multimeter_fetch()    # -> float for one sample, otherwise 1D numpy.ndarray
```

This function retrieves acquisition data using `FETC?`, without starting another acquisition or erasing the stored readings. It returns a float for one returned reading, or a one-dimensional `numpy.ndarray` for multiple readings. It may wait for completion and can time out if the trigger or acquisition does not complete.

```python
dmm.multimeter_sample_count(10)
dmm.multimeter_trigger_source('Bus')
dmm.multimeter_start()
dmm.multimeter_trigger()
readings = dmm.multimeter_fetch()
```

---

### multimeter_stop() { #multimeter_stop data-toc-label="multimeter_stop" }

```python
multimeter_stop()    # abort the active acquisition
```

This function aborts the active acquisition. It does not return a value.

---

### multimeter_reset() { #multimeter_reset data-toc-label="multimeter_reset" }

```python
multimeter_reset()    # reset the instrument
```

This function sends `*RST` to restore instrument defaults, including DC voltage mode, autoranging, `1` NPLC, trigger count `1`, trigger source `'Immediate'`, automatic trigger delay, sample count `1`, and automatic sample timing. It does not return a value. In test mode it restores simulated settings and clears simulated readings.

---

### multimeter_command(command) { #multimeter_command data-toc-label="multimeter_command" }

```python
multimeter_command('SENS:TEMP:TRAN:TYPE FRTD')    # select a four-wire RTD
multimeter_command('UNIT:TEMP K')               # select kelvins
```

This function sends a nonempty raw SCPI command and does not return a value. Use raw SCPI for temperature probe type, temperature units, and temperature auto-zero configuration; [`multimeter_auto_zero()`](#multimeter_auto_zero) does not control temperature auto-zero. Four-wire temperature measurements always use auto-zero. Only the command's string type and nonempty content are checked; raw SCPI syntax and its effects are not validated or simulated in test mode.

---

### multimeter_query(command) { #multimeter_query data-toc-label="multimeter_query" }

```python
multimeter_query('SENS:TEMP:TRAN:TYPE?')    # -> str in a real run, None in test mode
```

This function sends a nonempty raw SCPI query and returns the response as a string. In test mode it returns `None`. Advanced raw commands are not modeled by the test emulator; raw commands have no simulated effect and queries return `None`.
