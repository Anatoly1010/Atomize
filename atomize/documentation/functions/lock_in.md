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

### Internal data buffer (SR-810, 830, 850, 844)

These devices can store up to 16383 points from both the Channel 1 and Channel 2 displays in an internal data buffer. The buffer stores the quantities currently shown on the displays, sampled at a common rate. The functions below configure the storage, start/stop a scan, and read the stored points back. The SR-860 and SR-865a do not have this buffer; they use a different data-capture/streaming subsystem (`CAPTURE*` commands). A typical sequence is:

```python
sr830.lock_in_buffer_sample_rate('512 Hz')  # set the sample rate
sr830.lock_in_buffer_mode('1 Shot')         # stop at the end of the buffer
sr830.lock_in_buffer_reset()                # clear the buffer
sr830.lock_in_buffer_start()                # start storage
# ... acquire ...
sr830.lock_in_buffer_pause()                # pause before reading
n = sr830.lock_in_buffer_points()           # number of stored points
ch1 = sr830.lock_in_read_buffer(1)          # read all points from Channel 1
```

---

### lock_in_buffer_sample_rate(*rate) { #lock_in_buffer_sample_rate data-toc-label="lock_in_buffer_sample_rate" }

```python
lock_in_buffer_sample_rate()           # -> str (query)
lock_in_buffer_sample_rate('512 Hz')   # set the sample rate
```

This function queries or sets the data-buffer sample rate, i.e. how often points are added to the storage buffer. Both displays are sampled at the same rate. The `'Trigger'` value records one sample on every rising edge of the rear-panel trigger input (see [`lock_in_buffer_trigger()`](#lock_in_buffer_trigger)).

**Available values:** `'62.5 mHz'`, `'125 mHz'`, `'250 mHz'`, `'500 mHz'`, `'1 Hz'`, `'2 Hz'`, `'4 Hz'`, `'8 Hz'`, `'16 Hz'`, `'32 Hz'`, `'64 Hz'`, `'128 Hz'`, `'256 Hz'`, `'512 Hz'`, `'Trigger'`
{: .enum }

---

### lock_in_buffer_mode(*mode) { #lock_in_buffer_mode data-toc-label="lock_in_buffer_mode" }

```python
lock_in_buffer_mode()           # -> str (query)
lock_in_buffer_mode('Loop')     # continue storing at the end of the buffer
```

This function queries or sets the end-of-buffer mode. In `'1 Shot'` mode storage stops when the buffer is full. In `'Loop'` mode storage continues from the beginning, keeping the most recent 16383 points; pause storage before reading in this mode to avoid ambiguity about the most recent point.

**Available values:** `'1 Shot'`, `'Loop'`
{: .enum }

---

### lock_in_buffer_trigger_start(*mode) { #lock_in_buffer_trigger_start data-toc-label="lock_in_buffer_trigger_start" }

```python
lock_in_buffer_trigger_start()        # -> str (query)
lock_in_buffer_trigger_start('On')    # start the scan on a rear-panel trigger
```

This function queries or sets the trigger-start mode. When `'On'`, a rising TTL edge on the rear-panel trigger input has the same effect as [`lock_in_buffer_start()`](#lock_in_buffer_start).

**Available values:** `'Off'`, `'On'`
{: .enum }

---

### lock_in_buffer_start() { #lock_in_buffer_start data-toc-label="lock_in_buffer_start" }

```python
lock_in_buffer_start()
```

This function starts or resumes data storage in the internal buffer. It is ignored if storage is already in progress.

---

### lock_in_buffer_pause() { #lock_in_buffer_pause data-toc-label="lock_in_buffer_pause" }

```python
lock_in_buffer_pause()
```

This function pauses data storage. The buffer is not reset.

---

### lock_in_buffer_reset() { #lock_in_buffer_reset data-toc-label="lock_in_buffer_reset" }

```python
lock_in_buffer_reset()
```

This function stops data storage and erases the buffer. It can be sent at any time.

---

### lock_in_buffer_trigger() { #lock_in_buffer_trigger data-toc-label="lock_in_buffer_trigger" }

```python
lock_in_buffer_trigger()
```

This function sends a software trigger, equivalent to a rising edge on the rear-panel trigger input. Useful with a `'Trigger'` sample rate or with trigger-start enabled.

---

### lock_in_buffer_points() { #lock_in_buffer_points data-toc-label="lock_in_buffer_points" }

```python
lock_in_buffer_points()    # -> int; number of stored points
```

This function returns the number of points currently stored in the buffer. Both displays have the same number of points. It can be sent at any time, even while storage is in progress.

---

### lock_in_read_buffer(channel, *bins) { #lock_in_read_buffer data-toc-label="lock_in_read_buffer" }

```python
lock_in_read_buffer(1)           # -> np.array; all points from Channel 1
lock_in_read_buffer(2, 0, 100)   # -> np.array; 100 points from Channel 2 starting at bin 0
```

This function reads stored points from the Channel 1 or 2 display buffer and returns them as a NumPy array (the data are transferred in ASCII floating-point format). The `channel` argument selects the display buffer (`1` or `2`). The optional `bins` arguments are the start bin (`≥ 0`, where bin 0 is the oldest point) and the number of points to read (`≥ 1`); if omitted, the whole buffer is read. In `'Loop'` mode pause storage before reading, since the points are indexed relative to the continually changing most-recent point.

---

### Data capture (SR-860, 865a)

The SR-860 and SR-865a do not have the `SRAT`/`TRCA` display buffer described above. Instead they capture data into an internal buffer (up to 4 MB) using the `CAPTURE*` subsystem. The buffer length is configured in kilobytes (256 data points per kB), the captured quantities are chosen with the configuration (`X`, `XY`, `RT`, `XYRT`), and the rate is set as the maximum rate divided by a power of two. A typical sequence is:

```python
sr865a.lock_in_capture_config('XY')          # capture X and Y
sr865a.lock_in_capture_length(256)           # 256 kB buffer (64 k total points -> 32 k XY pairs)
sr865a.lock_in_capture_rate(0)               # fastest rate (max rate / 2**0)
sr865a.lock_in_capture_start('OneShot', 'Immediate')
# ... wait for the buffer to fill, monitor with lock_in_capture_state()/lock_in_capture_bytes() ...
sr865a.lock_in_capture_stop()
n_kb = sr865a.lock_in_capture_progress()     # captured data in kB
data = sr865a.lock_in_read_capture(0, 64)    # download the buffer as a NumPy float32 array
```

---

### lock_in_capture_length(*length) { #lock_in_capture_length data-toc-label="lock_in_capture_length" }

```python
lock_in_capture_length()       # -> int; buffer length in kB (query)
lock_in_capture_length(256)    # set the buffer length in kB
```

This function queries or sets the capture-buffer length in kilobytes (256 data points per kB). Because the internal blocks are 2 kB, the value must be even; an odd value is rounded up by the device.

**Range:** `1` – `4096`
{: .enum }

---

### lock_in_capture_config(*config) { #lock_in_capture_config data-toc-label="lock_in_capture_config" }

```python
lock_in_capture_config()        # -> str (query)
lock_in_capture_config('XY')    # capture X and Y
```

This function queries or sets which quantities are captured. Capturing more quantities yields fewer points of each for a given buffer length.

**Available values:** `'X'`, `'XY'`, `'RT'`, `'XYRT'`
{: .enum }

---

### lock_in_capture_rate_max() { #lock_in_capture_rate_max data-toc-label="lock_in_capture_rate_max" }

```python
lock_in_capture_rate_max()    # -> float; maximum capture rate in Hz
```

This function returns the maximum allowed capture rate in Hz at the current time constant and sync-filter setting (query only).

---

### lock_in_capture_rate(*n) { #lock_in_capture_rate data-toc-label="lock_in_capture_rate" }

```python
lock_in_capture_rate()     # -> float; actual capture rate in Hz (query)
lock_in_capture_rate(4)    # set the rate to (max rate) / 2**4
```

This function sets or queries the capture rate. When called with an argument `n` (`0` – `20`), the rate is set to the maximum rate divided by `2**n` (`n = 0` is the fastest). The query returns the *actual* rate in Hz, not `n`.

**Range (set):** `0` – `20`
{: .enum }

---

### lock_in_capture_start(acquisition, trigger) { #lock_in_capture_start data-toc-label="lock_in_capture_start" }

```python
lock_in_capture_start('OneShot', 'Immediate')
lock_in_capture_start('Continuous', 'TrigStart')
```

This function starts a new capture, clearing any previously captured data. The `acquisition` argument selects `'OneShot'` (stop when the buffer fills) or `'Continuous'` (wrap around and keep capturing). The `trigger` argument selects `'Immediate'` (start now), `'TrigStart'` (a hardware trigger starts or stops capture), or `'SampPerTrig'` (one sample per hardware trigger). A triggered start requires `'OneShot'`; a triggered stop requires `'Continuous'`.

**acquisition:** `'OneShot'`, `'Continuous'`
{: .enum }

**trigger:** `'Immediate'`, `'TrigStart'`, `'SampPerTrig'`
{: .enum }

---

### lock_in_capture_stop() { #lock_in_capture_stop data-toc-label="lock_in_capture_stop" }

```python
lock_in_capture_stop()
```

This function stops data capture in any mode. Already-captured data is preserved; the remainder of the current 2 kB block is zero-filled.

---

### lock_in_capture_state() { #lock_in_capture_state data-toc-label="lock_in_capture_state" }

```python
lock_in_capture_state()    # -> int; 3-bit state word
```

This function returns the capture state as a 3-bit binary-encoded integer: bit 0 (weight 1) capture in progress, bit 1 (weight 2) capture triggered, bit 2 (weight 4) buffer wrapped.

---

### lock_in_capture_bytes() { #lock_in_capture_bytes data-toc-label="lock_in_capture_bytes" }

```python
lock_in_capture_bytes()    # -> int; bytes of captured data
```

This function returns the number of bytes of non-zero data captured so far. It is live and may be used to monitor the progress of a capture.

---

### lock_in_capture_progress() { #lock_in_capture_progress data-toc-label="lock_in_capture_progress" }

```python
lock_in_capture_progress()    # -> int; captured data in kB
```

This function returns the amount of data written during the most recent capture, in kilobytes. Capture must be stopped before this query.

---

### lock_in_capture_value(sample) { #lock_in_capture_value data-toc-label="lock_in_capture_value" }

```python
lock_in_capture_value(0)    # -> np.array; the 1, 2 or 4 values of the oldest sample
```

This function reads one sample from the capture buffer in ASCII format and returns its `1`, `2` or `4` values (depending on [`lock_in_capture_config()`](#lock_in_capture_config)) as a NumPy array. The `sample` argument is the sample index (`0` is the oldest). Works over all interfaces.

---

### lock_in_read_capture(offset, length) { #lock_in_read_capture data-toc-label="lock_in_read_capture" }

```python
lock_in_read_capture(0, 64)    # -> np.array; 64 kB of the buffer from offset 0
```

This function downloads part of the capture buffer as a binary block and returns it as a NumPy `float32` array. The `offset` and `length` arguments are in kilobytes; `length` is limited to `1` – `64` kB per call, so a large buffer is read in several calls. Capture must be stopped first. This binary download is **not available over the RS-232 interface** — use [`lock_in_capture_value()`](#lock_in_capture_value) there instead.

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
