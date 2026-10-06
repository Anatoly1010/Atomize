# Preamplifiers

## Devices

| Device                                      | Tested   | Connection |
| ------------------------------------------- | -------- | ---------- |
| **Stanford Research Systems SR560**         | Untested | RS-232     |

## Functions

The SR560 interface keeps requested settings in attributes of each `SR_560` instance. Getters return `None` until a value has been set through that instance or loaded by [`preamplifier_reset()`](#preamplifier_reset). Opening a connection does not reset the instrument. The interface does not read replies from the instrument, and it cannot confirm that a command was accepted or detect changes made from the front panel or another controller. Setters return `None` and update the cache after writing the command.

The serial connection uses 9600 baud, 8 data bits, no parity, two stop bits, and CRLF line endings. Set `SPECIFIC.address` in the active device configuration to `0`, `1`, `2`, or `3`, matching the SR560 DIP-switch address. Every command is preceded by `UNLS` and `LISN <address>`.

The first application startup copies device configuration files only when the user configuration directory is missing or empty. If the active directory already exists and lacks `SR_560_config.ini`, copy only that file from `atomize/device_modules/config/` into the directory returned by `atomize.main.local_config.load_config_device()` and edit its serial port as needed; preserve the other active settings. The default port is `ASRL/dev/ttyUSB0::INSTR` for Linux; on Windows, use the appropriate VISA resource, such as `ASRL3::INSTR` for COM3.

```python
import atomize.device_modules.SR_560 as sr560

preamp = sr560.SR_560()
```

Run the example in test mode with `python atomize/script_examples/devices_tests/ask_SR_560.py test` on Windows, or use `python3` on Linux. Test mode uses the same cached getters and checks arguments without opening the serial connection. Invalid settings raise `AssertionError` in test mode and `ValueError` during a real run.

### preamplifier_name() { #preamplifier_name data-toc-label="preamplifier_name" }

```python
preamplifier_name()    # -> str; device name
```

This function returns the configured device name.

---

### preamplifier_gain(*gain) { #preamplifier_gain data-toc-label="preamplifier_gain" }

```python
preamplifier_gain()       # -> int or None; cached gain
preamplifier_gain(20)     # set gain to 20
```

This function sets or returns the cached voltage gain. Allowed values are `1`, `2`, `5`, `10`, `20`, `50`, `100`, `200`, `500`, `1000`, `2000`, `5000`, `10000`, `20000`, and `50000`.

---

### preamplifier_gain_mode(*mode) { #preamplifier_gain_mode data-toc-label="preamplifier_gain_mode" }

```python
preamplifier_gain_mode()                       # -> str or None; cached gain mode
preamplifier_gain_mode('High Dynamic Reserve')  # set gain mode
```

This function sets or returns the cached gain mode. Allowed values are `'Low Noise'`, `'High Dynamic Reserve'`, and `'Calibration'`.

---

### preamplifier_input_source(*source) { #preamplifier_input_source data-toc-label="preamplifier_input_source" }

```python
preamplifier_input_source()       # -> str or None; cached input source
preamplifier_input_source('A-B')  # select A minus B
```

This function sets or returns the cached input source. Allowed values are `'A'`, `'A-B'`, and `'B'`.

---

### preamplifier_input_coupling(*coupling) { #preamplifier_input_coupling data-toc-label="preamplifier_input_coupling" }

```python
preamplifier_input_coupling()       # -> str or None; cached input coupling
preamplifier_input_coupling('AC')   # set AC coupling
```

This function sets or returns the cached input coupling. Allowed values are `'Ground'`, `'DC'`, and `'AC'`. AC coupling always inserts the `0.03 Hz` high-pass filter. When AC coupling is selected, the low-pass filter is limited to a `6 dB/oct` slope.

---

### preamplifier_invert(*invert) { #preamplifier_invert data-toc-label="preamplifier_invert" }

```python
preamplifier_invert()        # -> str or None; cached inversion state
preamplifier_invert('On')    # enable inversion
```

This function sets or returns the cached signal inversion state. Allowed values are `'Off'` and `'On'`.

---

### preamplifier_filter_mode(*mode) { #preamplifier_filter_mode data-toc-label="preamplifier_filter_mode" }

```python
preamplifier_filter_mode()            # -> str or None; cached filter mode
preamplifier_filter_mode('Bandpass')  # set bandpass filtering
```

This function sets or returns the cached filter mode. Allowed values are `'Bypass'`, `'6 dB Low Pass'`, `'12 dB Low Pass'`, `'6 dB High Pass'`, `'12 dB High Pass'`, and `'Bandpass'`.

---

### preamplifier_high_pass_frequency(*frequency) { #preamplifier_high_pass_frequency data-toc-label="preamplifier_high_pass_frequency" }

```python
preamplifier_high_pass_frequency()            # -> str or None; cached frequency
preamplifier_high_pass_frequency('10 Hz')     # set high-pass frequency
```

This function sets or returns the cached high-pass cutoff frequency. Pass a string using `Hz`, `kHz`, or `MHz`. Allowed frequencies are `'0.03 Hz'`, `'0.1 Hz'`, `'0.3 Hz'`, `'1 Hz'`, `'3 Hz'`, `'10 Hz'`, `'30 Hz'`, `'100 Hz'`, `'300 Hz'`, `'1 kHz'`, `'3 kHz'`, and `'10 kHz'`. The getter returns these canonical unit strings. The SR560's AC coupling setting always inserts the `0.03 Hz` high-pass filter.

---

### preamplifier_low_pass_frequency(*frequency) { #preamplifier_low_pass_frequency data-toc-label="preamplifier_low_pass_frequency" }

```python
preamplifier_low_pass_frequency()             # -> str or None; cached frequency
preamplifier_low_pass_frequency('1 MHz')      # set low-pass frequency
```

This function sets or returns the cached low-pass cutoff frequency. Pass a string using `Hz`, `kHz`, or `MHz`. Allowed frequencies are `'0.03 Hz'`, `'0.1 Hz'`, `'0.3 Hz'`, `'1 Hz'`, `'3 Hz'`, `'10 Hz'`, `'30 Hz'`, `'100 Hz'`, `'300 Hz'`, `'1 kHz'`, `'3 kHz'`, `'10 kHz'`, `'30 kHz'`, `'100 kHz'`, `'300 kHz'`, and `'1 MHz'`. The getter returns these canonical unit strings. AC coupling limits the low-pass filter to a `6 dB/oct` slope. The cached value is the last requested setting; it does not represent an effective response measured from the instrument.

---

### preamplifier_vernier(*vernier) { #preamplifier_vernier data-toc-label="preamplifier_vernier" }

```python
preamplifier_vernier()        # -> str or None; cached vernier state
preamplifier_vernier('On')    # enable vernier control
```

This function sets or returns the cached vernier state. Allowed values are `'Off'` and `'On'`.

---

### preamplifier_vernier_gain(*gain) { #preamplifier_vernier_gain data-toc-label="preamplifier_vernier_gain" }

```python
preamplifier_vernier_gain()     # -> int or None; cached vernier gain
preamplifier_vernier_gain(50)   # set vernier gain to 50 percent
```

This function sets or returns the cached vernier gain as a percentage of the selected calibrated gain. Allowed values are the integers from `0` through `100`, inclusive. Enable vernier control separately with `preamplifier_vernier('On')`. The getter initially returns `None` and remains `None` after reset because the manual does not document a reset value for this setting.

---

### preamplifier_blanking(*blanking) { #preamplifier_blanking data-toc-label="preamplifier_blanking" }

```python
preamplifier_blanking()        # -> str or None; cached blanking state
preamplifier_blanking('On')    # enable blanking
```

This function sets or returns the cached blanking state. Allowed values are `'Off'` and `'On'`. The getter initially returns `None` and remains `None` after reset because the driver has no documented reset value for this setting.

---

### preamplifier_overload_reset() { #preamplifier_overload_reset data-toc-label="preamplifier_overload_reset" }

```python
preamplifier_overload_reset()    # initiate overload recovery
```

This function sends the overload reset command, which resets overload for half a second to speed recovery with long filter time constants. It preserves the cached settings and does not return a value.

---

### preamplifier_reset() { #preamplifier_reset data-toc-label="preamplifier_reset" }

```python
preamplifier_reset()    # restore instrument defaults and cache documented values
```

This function sends `*RST`, clears the instance cache, and records the documented default settings: gain `20`, gain mode `'High Dynamic Reserve'`, input source `'A'`, input coupling `'DC'`, inversion `'Off'`, filter mode `'Bypass'`, high-pass frequency `'0.03 Hz'`, low-pass frequency `'1 MHz'`, and vernier `'Off'`. Vernier gain and blanking remain `None` because the driver does not define documented reset defaults for them. The function does not return a value.

---

### preamplifier_command(command) { #preamplifier_command data-toc-label="preamplifier_command" }

```python
preamplifier_command('GAIN 6')    # send the raw command for gain 100
```

This function sends a nonempty raw command string to the SR560 and clears every cached setting because the command may change any of them. Use [`preamplifier_reset()`](#preamplifier_reset) to restore the documented defaults and update the cache after reset; sending `*RST` through this function clears the cache without recording those defaults. The function does not return a value.
