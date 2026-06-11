# Lock-In Amplifiers

## Devices

| Device                             | Tested   | Connection                              |
| ---------------------------------- | -------- | --------------------------------------- |
| **Stanford Research SR-810**       | 02/2021  | GPIB (linux-gpib), RS-232               |
| **Stanford Research SR-830**       | 02/2021  | GPIB (linux-gpib), RS-232               |
| **Stanford Research SR-850**       | 02/2021  | GPIB (linux-gpib), RS-232               |
| **Stanford Research SR-844**       | Untested | GPIB (linux-gpib), RS-232               |
| **Stanford Research SR-860**       | 01/2021  | GPIB (linux-gpib), RS-232, Ethernet     |
| **Stanford Research SR-865a**      | 01/2021  | GPIB (linux-gpib), RS-232, Ethernet     |

## Functions

### lock_in_name() { #lock_in_name data-toc-label="lock_in_name" }

```python
lock_in_name()    # -> str; device name
```

This function returns device name.

---

### lock_in_ref_frequency(*frequency) { #lock_in_ref_frequency data-toc-label="lock_in_ref_frequency" }

```python
lock_in_ref_frequency()             # -> str (query)
lock_in_ref_frequency('100 kHz')    # set reference frequency to 100 kHz
```

This function sets or queries the reference frequency. If called with no argument the current reference frequency is returned. If called with an argument the reference frequency is set. The details about 2F mode are given in the [`lock_in_harmonic()`](#lock_in_harmonic) function.

For SR-860, 865a the query command, [`lock_in_ref_frequency()`](#lock_in_ref_frequency), returns the internal reference frequency whenever the reference mode is either Internal, Dual, or Chop. The query returns the external frequency when operating in External mode.

**Output format:** `'number'` + `'MHz'` | `'kHz'` | `'Hz'` | `'mHz'`
{: .enum }

**Range (SR-810, 830, 850):** `4 mHz` – `102 kHz`
{: .enum }

**Range (SR-860):** `1 mHz` – `500 kHz`
{: .enum }

**Range (SR-865a):** `1 mHz` – `4 MHz`
{: .enum }

**Range (SR-844, 1F mode):** `25 kHz` – `200 MHz`
{: .enum }

**Range (SR-844, 2F mode):** `50 kHz` – `200 MHz`
{: .enum }

---

### lock_in_phase(*degree) { #lock_in_phase data-toc-label="lock_in_phase" }

```python
lock_in_phase()       # -> str (query)
lock_in_phase(100)    # set phase to 100 degrees
```

This function sets or queries the phase of the lock-in in degrees. If there is no argument the function will return the current phase. If called with an argument the specified phase will be set. The phase will be wrapped around at ±180°.

**Range (SR-810, 830):** `-360.000` – `729.999`
{: .enum }

**Range (SR-850):** `-360.000` – `719.999`
{: .enum }

**Range (SR-860, 865a):** `-360000` – `360000`
{: .enum }

**Range (SR-844):** `-360` – `360`
{: .enum }

---

### lock_in_auto_phase() { #lock_in_auto_phase data-toc-label="lock_in_auto_phase" }

```python
lock_in_auto_phase()    # auto-phase the reference
```

This function adjusts the reference phase so that the current measurement has a Y value of zero and an X value equal to the signal magnitude, R. The outputs may take many time constants to reach their new values. Do not send the command again without waiting the appropriate amount of time.

!!! note
    This function is only available for SR-844, SR-860, SR-865.

---

### lock_in_time_constant(*timeconstant) { #lock_in_time_constant data-toc-label="lock_in_time_constant" }

```python
lock_in_time_constant()            # -> str (query)
lock_in_time_constant('100 ms')    # set time constant to 100 ms
```

This function sets or queries the time constant of the lock-in. If there is no argument the function will return the current time constant. If there is an argument the specified time constant will be set. If there is no time constant setting fitting the argument the nearest available value is used and warning is printed.

**Allowed (SR-810, 830, 850):** `10 us`, `30 us`, `100 us`, `300 us`, `1 ms`, `3 ms`, `10 ms`, `30 ms`, `100 ms`, `300 ms`, `1 s`, `3 s`, `10 s`, `30 s`, `100 s`, `300 s`, `1 ks`, `10 ks`, `30 ks`
{: .enum }

**Allowed (SR-860, 865a):** above + `1 us`, `3 us`
{: .enum }

**Allowed (SR-844):** `100 us`, `300 us`, `1 ms`, `3 ms`, `10 ms`, `30 ms`, `100 ms`, `300 ms`, `1 s`, `3 s`, `10 s`, `30 s`, `100 s`, `300 s`, `1 ks`, `10 ks`, `30 ks`
{: .enum }

---

### lock_in_ref_amplitude(*amplitude) { #lock_in_ref_amplitude data-toc-label="lock_in_ref_amplitude" }

```python
lock_in_ref_amplitude()         # -> str (query)
lock_in_ref_amplitude(0.150)    # set modulation level to 150 mV
```

This function queries or sets the level of the modulation frequency. If there is no argument the function will return the current level. If there is an argument the specified level will be set. If the argument is not within the allowed range an error message is printed and the level of 4 mV will be set.

**Output format:** `'number'` + `'V'` | `'mV'`
{: .enum }

**Range (SR-810, 830, 850):** `4 mV` – `5 V`
{: .enum }

**Range (SR-860, 865a):** `1 nV` – `2 V`
{: .enum }

!!! note
    This function is not available for SR-844.

---

### lock_in_get_data(*channel) { #lock_in_get_data data-toc-label="lock_in_get_data" }

```python
lock_in_get_data()           # -> float; X signal in V
lock_in_get_data(1, 2, 3)    # -> X, Y, R in V
```

This function can be used to query measured values from the lock-in amplifier. If no argument is specified the X signal is returned. If a parameter is passed to the function the value at the corresponding channel is returned.

Channel meaning for SR-810, 830, 850, 860, 865a: `1` — X signal in Volts; `2` — Y signal in Volts; `3` — R signal in Volts; `4` — Phase 'theta' of data in degrees; `[1, 2]` — X and Y signals in Volts; `[1, 2, 3]` — X, Y, and R signals in Volts.

**Allowed channels:** `1`, `2`, `3`, `4`
{: .enum }

---

### lock_in_sensitivity(*sensitivity) { #lock_in_sensitivity data-toc-label="lock_in_sensitivity" }

```python
lock_in_sensitivity()           # -> str (query)
lock_in_sensitivity('10 uV')    # set sensitivity to 10 uV
```

This function queries or sets the sensitivity of the lock-in. If there is no argument the function will return the current sensitivity as a string. If there is an argument the specified sensitivity will be set. If there is no sensitivity setting fitting the argument the nearest available value is used and warning is printed.

**Allowed (SR-810, 830, 850):** `2 nV`, `5 nV`, `10 nV`, `20 nV`, `50 nV`, `100 nV`, `200 nV`, `500 nV`, `1 uV`, `2 uV`, `5 uV`, `10 uV`, `20 uV`, `50 uV`, `100 uV`, `200 uV`, `500 uV`, `1 mV`, `2 mV`, `5 mV`, `10 mV`, `20 mV`, `50 mV`, `100 mV`, `200 mV`, `500 mV`, `1 V`
{: .enum }

**Allowed (SR-860, 865a):** above + `1 nV`
{: .enum }

**Allowed (SR-844):** `100 nV`, `300 nV`, `1 uV`, `3 uV`, `10 uV`, `30 uV`, `100 uV`, `300 uV`, `1 mV`, `3 mV`, `10 mV`, `30 mV`, `100 mV`, `300 mV`, `1 V`
{: .enum }

---

### lock_in_auto_sensitivity() { #lock_in_auto_sensitivity data-toc-label="lock_in_auto_sensitivity" }

```python
lock_in_auto_sensitivity()    # automatically set sensitivity
```

This function automatically sets the sensitivity of the instrument. The measured values may take many time constants to return to their steady state values. Do not send the command again without waiting the appropriate amount of time.

!!! note
    This function is only available for SR-844, SR-860, SR-865.

---

### lock_in_ref_mode(*mode) { #lock_in_ref_mode data-toc-label="lock_in_ref_mode" }

```python
lock_in_ref_mode()              # -> str (query)
lock_in_ref_mode('External')    # use external modulation
```

This function queries or sets the modulation mode, i.e. if the internal modulation or an external modulation input is used. If there is no argument the function will return the current modulation mode. If there is an argument the specified modulation mode will be set.

**Allowed (SR-810, 830, 850, 844):** `'Internal'`, `'External'`
{: .enum }

**Allowed (SR-860, 865a):** `'Internal'`, `'External'`, `'Dual'`, `'Chop'`
{: .enum }

---

### lock_in_ref_slope(*mode) { #lock_in_ref_slope data-toc-label="lock_in_ref_slope" }

```python
lock_in_ref_slope()            # -> str (query)
lock_in_ref_slope('PosTTL')    # set reference trigger to TTL rising edge
```

This function queries or sets the reference trigger when using the external reference mode. If there is no argument the function will return the current reference trigger. If there is an argument the specified reference trigger mode will be set. Note that at frequencies below 1 Hz, the a TTL reference must be used. The values correspond to sine zero crossing, TTL rising edge, TTL falling edge, respectively.

**Allowed:** `'Sine'`, `'PosTTL'`, `'NegTTL'`
{: .enum }

!!! note
    This function is not available for SR-844.

---

### lock_in_sync_filter(*mode) { #lock_in_sync_filter data-toc-label="lock_in_sync_filter" }

```python
lock_in_sync_filter()        # -> str (query)
lock_in_sync_filter('On')    # turn on synchronous filtering
```

This function queries or sets the synchronous filter status. If there is no argument the function will return the current status. If there is an argument the specified status will be set. Note that synchronous filtering is turned on only if the detection frequency is less than 200 Hz.

**Allowed:** `'Off'`, `'On'`
{: .enum }

!!! note
    This function is not available for SR-844.

---

### lock_in_lp_filter(*mode) { #lock_in_lp_filter data-toc-label="lock_in_lp_filter" }

```python
lock_in_lp_filter()           # -> str (query)
lock_in_lp_filter('12 dB')    # set low pass filter slope to 12 dB/oct
```

This function queries or sets the low pass filter slope. If there is no argument the function will return the current slope. If there is an argument the specified slope will be set. The values correspond to 6 dB/oct, 12 dB/oct, 18 dB/oct, 24 dB/oct, respectively.

**Allowed:** `'6 dB'`, `'12 dB'`, `'18 dB'`, `'24 dB'`
{: .enum }

**Allowed (SR-844, extra):** `'No'` (No Filter mode)
{: .enum }

---

### lock_in_harmonic(*harmonic) { #lock_in_harmonic data-toc-label="lock_in_harmonic" }

```python
lock_in_harmonic()     # -> int (query)
lock_in_harmonic(2)    # detect at the second harmonic
```

This function queries or sets the detection harmonic. The function will set the lock-in to detect at the specified harmonic of the reference frequency. The value of the detected frequency is limited by 102 kHz. If the argument used requires a detection frequency greater than 102 kHz, then the harmonic number will be set to the largest value available for which the frequency is less than 102 kHz.

For SR-844 the frequency range for the second harmonics detection is limited to 50 kHz to 200 MHz. More details are given in the [`lock_in_ref_frequency()`](#lock_in_ref_frequency) function.

**Range (SR-810, 830):** `1` – `19999`
{: .enum }

**Range (SR-850):** `1` – `32767`
{: .enum }

**Range (SR-860, 865a):** `1` – `99`
{: .enum }

**Range (SR-844):** `1` – `2`
{: .enum }

---

### lock_in_command(command) { #lock_in_command data-toc-label="lock_in_command" }

```python
# Sets the low pass filter slope; parameter 0 selects 6 dB/oct.
lock_in_command('OFSL 0')
```

This function sends an arbitrary command from a programming guide to the device in a string format. No output is expected.

---

### lock_in_query(command) { #lock_in_query data-toc-label="lock_in_query" }

```python
lock_in_query('OFSL?')    # query the low pass filter slope
```

This function sends an arbitrary command from a programming guide to the device in a string format. An output in a string format is expected.
