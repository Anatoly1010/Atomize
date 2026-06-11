# Pulse Programmers

## Devices

| Device                                                                 | Tested  | Library                                                                                       |
| ---------------------------------------------------------------------- | ------- | --------------------------------------------------------------------------------------------- |
| **Pulse Blaster ESR 500 Pro**                                          | 06/2021 | [SpinCore SpinAPI](http://www.spincore.com/support/spinapi/using_spin_api_pb.shtml)           |
| **[Insys FM214x3GDA](https://www.insys.ru/mezzanine/fm214x3gda)** (as multichannel TTL pulse generator) | 03/2025 | [Atomize_ITC libs](https://github.com/Anatoly1010/Atomize_ITC/tree/master/libs)               |
| **Pulse Blaster Micran**                                               | 12/2023 | —                                                                                             |

The device is available via `ctypes`. [The original C library](http://www.spincore.com/support/spinapi/using_spin_api_pb.shtml) was written by SpinCore Technologies.

The Insys device is available via `ctypes`. The original library can be found [here](https://github.com/Anatoly1010/Atomize_ITC/tree/master/libs).

## Functions

### pulser_name() { #pulser_name data-toc-label="pulser_name" }

```python
pulser_name()    # -> str; device name
```

This function returns device name.

---

### pulser_pulse(**kargs) { #pulser_pulse data-toc-label="pulser_pulse" }

```python
# Default DETECTION pulse, no phase cycling
pulser_pulse()

# A named microwave pulse at 100 ns, length 100 ns
pulser_pulse(
    name='P0', channel='MW',
    start='100 ns', length='100 ns',
    delta_start='0 ns', length_increment='0 ns')
```

The keyword arguments:

| Keyword            | Default       | Description                                                   |
| ------------------ | ------------- | ------------------------------------------------------------- |
| `name`             | `'P0'`        | name of the pulse                                             |
| `channel`          | `'DETECTION'` | channel string (`CH0`, `CH1`, …, `CH20`)                      |
| `start`            | `'0 ns'`      | start time of the pulse (`ns`, `us`, `ms`, `s`)               |
| `length`           | `'100 ns'`    | length of the pulse (`ns`, `us`, `ms`, `s`)                   |
| `delta_start`      | `'0 ns'`      | start time increment of the pulse (`ns`, `us`, `ms`, `s`)     |
| `length_increment` | `'0 ns'`      | pulse length increment (`ns`, `us`, `ms`, `s`)                |
| `phase_list`       | `[]`          | phase cycling sequence (`+x`, `-x`, `+y`, `-y`)               |

This function sets a pulse with specified parameters. The default argument is `name = 'P0'`, `channel = 'DETECTION'`, `start = '0 ns'`, `length = '100 ns'`, `delta_start = '0 ns'`, `length_increment = '0 ns'`, `phase_list = []`. The pulse sequence will be checked for overlap. In the auto defence mode (default option; can be changed in the config file) channels `AMP_ON` and `LNA_PROTECT` will be added automatically according to the delays indicated in the config file. In this mode `AMP_ON` and `LNA_PROTECT` pulses will be joined in one pulse if the distance between them is less than 12 ns (can be changed in the config file).

**Allowed channels:** `'DETECTION'`, `'TRIGGER'`, `'AMP_ON'`, `'LNA_PROTECT'`, `'MW'`, `'-X'`, `'+Y'`, `'TRIGGER_AWG'`, `'AWG'`, `'LASER'`, `'SYNT2'`, `'CH10'`, …, `'CH20'`
{: .enum }

**Allowed phase_list values:** `'+x'`, `'-x'`, `'+y'`, `'-y'`
{: .enum }

**Output format (time args):** `'number'` + `'ns'` | `'us'` | `'ms'` | `'s'`
{: .enum }

**Range (Pulse Blaster ESR 500 Pro):** pulse length `10 ns` – `1900 ns`; sequence ≈ `10 s` max
{: .enum }

**Range (Insys FM214x3GDA):** pulse length `3.2 ns` – `1900 ns`; sequence ≈ `10 s` max
{: .enum }

In the case of Insys FM214x3GDA `start`, `length`, `delta_start`, and `length_increment` will be rounded to a multiple of 3.2.

In the case of Pulse Blaster ESR 500 Pro and Pulse Blaster Micran the `DETECTION` pulse may carry a `phase_list`. This list declares the acquisition phase cycle and is used by [`pulser_acquisition_cycle()`](#pulser_acquisition_cycle) whenever that function is called without an explicit `acq_cycle` argument; passing `acq_cycle` directly still overrides it. Alternatively, the acquisition phases can be indicated directly in [`pulser_acquisition_cycle()`](#pulser_acquisition_cycle) and the `DETECTION` pulse left without a `phase_list`. The plain `TRIGGER` channel must always have an empty `phase_list`. In the case of Insys FM214x3GDA a `phase_list` of `DETECTION` pulse is used to [phase cycle](digitizer.md#digitizer_get_curve-points) the data.

---

### pulser_update() { #pulser_update data-toc-label="pulser_update" }

```python
pulser_update()    # commit pulse-sequence changes to the programmer
```

This function updates a pulse sequence and sends instructions to the pulse programmer. It has to be called after changes have been applied to pulses either via any of the pulser functions or by changing a pulse property directly. Only by calling the function the changes are committed and the real pulses will change.

---

### pulser_next_phase() { #pulser_next_phase data-toc-label="pulser_next_phase" }

```python
pulser_next_phase()    # advance all pulses to the next phase
```

This function switches all pulses to the next phase. The phase sequence is declared in the [`pulser_pulse()`](#pulser_pulse) in the form of `phase_list = ['-y', '+x', '-x', '+x', ...]`. By repeatedly calling the function one can run through the complete list of phases for the pulses. The length of all phase lists specified for different MW pulses has to be the same. This function also immediately updates the pulse sequence, as it is done by calling [`pulser_update()`](#pulser_update). The first call of the function corresponds to the first phase in the `phase_list` argument of the [`pulser_pulse()`](#pulser_pulse).

---

### pulser_acquisition_cycle(data1, data2, acq_cycle=None) { #pulser_acquisition_cycle data-toc-label="pulser_acquisition_cycle" }

```python
# Two-step phase cycle (+x, -x)
i, q = pulser_acquisition_cycle(
    np.array([1, 0]), np.array([0, 1]),
    acq_cycle=['+x', '-x'])

# acq_cycle omitted: the phase_list of the DETECTION pulse is used
i, q = pulser_acquisition_cycle(np.array([1, 0]), np.array([0, 1]))
```

This function can be used to shorten the syntax for acquisition in the case of phase cycling. The arguments are (i) two numpy arrays from a quadrature detector, (ii) array of mathematical operations to perform. Data arrays can be both 2D and 1D, representing, respectively, the case of raw oscillograms or integrated data. The length of `acq_cycle` array and the 1D arrays or the amount of the individual oscillograms in the 2D array should be equal. The data arrays will be treated inside the function as a complex number:

```python
answer = np.zeros( data1.shape ) + 1j*np.zeros( data2.shape )
```

The symbol at the index `J` of the `acq_cycle` array means that the corresponding values from the data arrays will be added with the following factor to the resulting array:

**Allowed operations:** `'+x'`, `'-x'`, `'+y'`, `'-y'`
{: .enum }

| Symbol | Factor | Operation                                       |
| ------ | ------ | ----------------------------------------------- |
| `+x`   | `+1`   | `answer = answer + data1[J] + 1j*data2[J]`      |
| `-x`   | `-1`   | `answer = answer - data1[J] - 1j*data2[J]`      |
| `+y`   | `+1j`  | `answer = answer + 1j*data1[J] - data2[J]`      |
| `-y`   | `-1j`  | `answer = answer - 1j*data1[J] + data2[J]`      |

The output of the function is the real and imaginary parts of the `answer` array after complete cycle of mathematical transformations. These can be both 1D and 2D arrays, depending on the shape of the input data arrays.

For Pulse Blaster ESR 500 Pro and Pulse Blaster Micran the `acq_cycle` argument is optional. When it is omitted (or an empty list is given) the function falls back to the `phase_list` declared on the [`DETECTION` pulse](#pulser_pulse); an explicitly supplied `acq_cycle` always takes precedence.

Although this function is available for Insys FM214x3GDA, it is better to use a modified version of [`digitizer_get_curve()`](digitizer.md#digitizer_get_curve-points). In this case acquisition phases should be given directly in the phase list key argument of the [`DETECTION` pulse](#pulser_pulse). For Insys FM214x3GDA the function has a modified signature `pulser_acquisition_cycle(data1, data2, points, phases, adc_window, acq_cycle=['+x'], lo=None, hi=None)` and is normally called internally by [`digitizer_get_curve()`](digitizer.md#digitizer_get_curve-points): the data is taken from the running on-board accumulators (the legacy `data1` and `data2` arguments are accepted but ignored), and the keywords `lo` and `hi` indicate the range of points to recompute. The factor table above applies to the `acq_cycle` argument in the same way.

---

### pulser_repetition_rate(*r_rate) { #pulser_repetition_rate data-toc-label="pulser_repetition_rate" }

```python
pulser_repetition_rate()          # -> str (query)
pulser_repetition_rate('2 Hz')    # set to 2 Hz
```

This function queries (if called without argument) or sets (if called with one argument) the repetition rate of the pulse sequence. If there is an argument it will be set as a repetition rate. If there is no argument the current repetition rate is returned as a string. The maximum available repetition rate depends on the total length of the pulse sequence.

**Max:** `5 MHz`
{: .enum }

---

### pulser_shift(*pulses) { #pulser_shift data-toc-label="pulser_shift" }

```python
pulser_shift()    # shift all active pulses by their delta_start
pulser_shift('P0', 'P1') # shift only the named pulses
```

This function can be called with either no argument or with a list of comma separated pulse names (i.e. `'P0'`, `'P1'`). If no argument is given the start time of all pulses that have a nonzero `delta_start` and are currently active (do not have a length of 0) are shifted by their corresponding `delta_start` value. If there is one argument or a list of comma separated pulse names only the start time of the listed pulses are changed. Calling this function also resets the phase (if specified in the argument `phase_list` of the [`pulser_pulse()`](#pulser_pulse)) to the first phase in the `phase_list`.

---

### pulser_increment(*pulses) { #pulser_increment data-toc-label="pulser_increment" }

```python
pulser_increment()        # increment all active pulses by their length_increment
pulser_increment('P0')    # increment only the named pulses
```

This function can be called with either no argument or with a list of comma separated pulse names (i.e. `'P0'`, `'P1'`). If no argument is given the lengths of all pulses that have a nonzero `length_increment` and are currently active (do not have a length of 0) are incremented by their corresponding `length_increment` value. If there is one argument or a list of comma separated pulse names only the lengths of the listed pulses are changed. Calling this function also resets the phase (if specified in the argument `phase_list` of the [`pulser_pulse()`](#pulser_pulse)) to the first phase in the `phase_list`.

---

### pulser_redefine_start(*, name, start) { #pulser_redefine_start data-toc-label="pulser_redefine_start" }

```python
pulser_redefine_start(name='P0', start='100 ns')

# Multiple pulses at once
pulser_redefine_start(name=['P0', 'P1'], start=['0 ns', '320 ns'])
```

This function should be called with two keyword arguments, namely `name` and `start`. The first argument specifies the name of the pulse as a string. The second argument defines a new value of pulse start as a string in the format `number + [' ms', ' us', ' ns']`. Arguments can be either single strings or lists, for example: `name = ['P0', 'P1']`, `start = ['0 ns', '320 ns']`. The main purpose of the function is non-uniform sampling. Please note, that the function does not update the pulse programmer. The [`pulser_update()`](#pulser_update) function should be called to apply changes.

In the case of Insys FM214x3GDA `start` will be rounded to a multiple of 3.2.

---

### pulser_redefine_delta_start(*, name, delta_start) { #pulser_redefine_delta_start data-toc-label="pulser_redefine_delta_start" }

```python
pulser_redefine_delta_start(name='P0', delta_start='10 ns')

# Multiple pulses
pulser_redefine_delta_start(
    name=['P0', 'P1'], delta_start=['0 ns', '32 ns'])
```

This function should be called with two keyword arguments, namely `name` and `delta_start`. The first argument specifies the name of the pulse as a string. The second argument defines a new value of `delta_start` as a string in the format `number + [' ms', ' us', ' ns']`. Arguments can be either single strings or lists, for example: `name = ['P0', 'P1']`, `delta_start = ['0 ns', '32 ns']`. The main purpose of the function is non-uniform sampling. Please note, that the function does not update the pulse programmer. The [`pulser_update()`](#pulser_update) function should be called to apply changes.

In the case of Insys FM214x3GDA `delta_start` will be rounded to a multiple of 3.2.

---

### pulser_redefine_length_increment(*, name, length_increment) { #pulser_redefine_length_increment data-toc-label="pulser_redefine_length_increment" }

```python
pulser_redefine_length_increment(name='P2', length_increment='2 ns')

# Multiple pulses
pulser_redefine_length_increment(
    name=['P0', 'P1'], length_increment=['0 ns', '3.2 ns'])
```

This function should be called with two keyword arguments, namely `name` and `length_increment`. The first argument specifies the name of the pulse as a string. The second argument defines a new value of length increment as a string in the format `number + [' ms', ' us', ' ns']`. Arguments can be either single strings or lists, for example: `name = ['P0', 'P1']`, `length_increment = ['0 ns', '3.2 ns']`. The main purpose of the function is non-uniform sampling. Please note, that the function does not update the pulse programmer. The [`pulser_update()`](#pulser_update) function should be called to apply changes.

In the case of Insys FM214x3GDA `length_increment` will be rounded to a multiple of 3.2.

---

### pulser_reset() { #pulser_reset data-toc-label="pulser_reset" }

```python
pulser_reset()                       # default
pulser_reset(internal_cycle=True)    # for use with pulser_instruction_from_file
```

The function switches the pulse programmer back to the initial state (including phase) in which it was in at the start of the experiment. This function can be called only without arguments. It includes the complete functionality of [`pulser_pulse_reset()`](#pulser_pulse_reset), but also immediately updates the pulse programmer as it is done by calling [`pulser_update()`](#pulser_update).

The additional keyword `internal_cycle` can be used in combination with the [`pulser_instruction_from_file()`](#pulser_instruction_from_file) function to achieve correct update of the pulse programmer. The default option is `False`.

**Allowed internal_cycle:** `True`, `False`
{: .enum }

!!! note
    This function is not available for Insys FM214x3GDA. The function
    [`pulser_pulse_reset()`](#pulser_pulse_reset) can be used instead.

---

### pulser_pulse_reset(*pulses) { #pulser_pulse_reset data-toc-label="pulser_pulse_reset" }

```python
pulser_pulse_reset()        # reset all pulses (incl. phases)
pulser_pulse_reset('P1')    # reset only the named pulses
```

This function switches the pulse programmer back to the initial state in which it was in at the start of the experiment. This function can be called with either no argument or with a list of comma separated pulse names. If no argument is given all pulses are reset to their initial states (including phases). The function does not update the pulser, if you want to reset all pulses and also update the pulser use the function [`pulser_reset()`](#pulser_reset) instead.

The additional keyword `internal_cycle` can be used in combination with the [`pulser_instruction_from_file()`](#pulser_instruction_from_file) function to achieve correct update of the pulse programmer. The default option is `False`.

**Allowed internal_cycle:** `True`, `False`
{: .enum }

---

### pulser_stop() { #pulser_stop data-toc-label="pulser_stop" }

```python
pulser_stop()    # stop the pulse programmer
```

This function stops the pulse programmer. The function should always be called at the end of an experimental script in the case of Pulse Blaster ESR 500 Pro.

!!! note
    This function is not available for Insys FM214x3GDA. The function
    [`pulser_close()`](#pulser_close) must be used instead.

---

### pulser_state() { #pulser_state data-toc-label="pulser_state" }

```python
pulser_state()    # -> str; current programmer state
```

This function queries the pulse programmer state and should be called only without arguments.

!!! note
    This function is only available for Pulse Blaster ESR 500 Pro.

---

### pulser_visualize() { #pulser_visualize data-toc-label="pulser_visualize" }

```python
pulser_visualize()    # opens a 2D plot of the current pulse sequence
```

This function visualizes the pulse sequence as 2D plot and should be called only without arguments.

---

### pulser_pulse_list() { #pulser_pulse_list data-toc-label="pulser_pulse_list" }

```python
pulser_pulse_list()    # -> list of str; the declared pulse sequence
```

This function should be called only without arguments and it returns the declared pulse sequence as an array.

---

### pulser_open() { #pulser_open data-toc-label="pulser_open" }

```python
pulser_open()    # open the board for use
```

This function should be called only without arguments and is only available for Insys FM214x3GDA and Pulse Blaster Micran. In the case of Insys FM214x3GDA, the function should be used after defining pulses and repetition rate with [`pulser_pulse()`](#pulser_pulse) and [`pulser_repetition_rate()`](#pulser_repetition_rate).

---

### pulser_close() { #pulser_close data-toc-label="pulser_close" }

```python
pulser_close()    # gracefully close the board
```

This function should be called only without arguments and is only available for Insys FM214x3GDA and Pulse Blaster Micran. The function must be used at the end of an experimental script to gracefully close the board.

---

### pulser_default_synt(num) { #pulser_default_synt data-toc-label="pulser_default_synt" }

```python
pulser_default_synt(1)    # select synthesizer 1
pulser_default_synt(2)    # select synthesizer 2
```

This function should be called only with one argument and selects the default sources for microwave pulse generation.

**Allowed:** `1`, `2`
{: .enum }

!!! note
    This function is only available for Insys FM214x3GDA.

---

### pulser_phase_reset() { #pulser_phase_reset data-toc-label="pulser_phase_reset" }

```python
pulser_phase_reset()    # reset the phase index to zero
```

This function resets the phase index to zero in order to start phase cycling once again.

!!! note
    This function is only available for Pulse Blaster ESR 500 Pro and
    Pulse Blaster Micran.

---

### pulser_instruction_from_file(flag, filename) { #pulser_instruction_from_file data-toc-label="pulser_instruction_from_file" }

```python
pulser_instruction_from_file(1, filename='instructions.out')
```

This special function reads the instructions for pulse programmer from the specified file. The keyword argument `filename` corresponds to the file to read. `1` means that the instructions will be read from the file.

**Allowed flag:** `0`, `1`
{: .enum }

!!! note
    This function is only available for Pulse Blaster ESR 500 Pro and
    Pulse Blaster Micran.

---

### pulser_clear() { #pulser_clear data-toc-label="pulser_clear" }

```python
pulser_clear()    # clear the device module's pulse array and status flags
```

This is a special function for clearing pulse array `{self.pulse_array}` and other status flags of the device module. The function is usually used in GUI applications that use the device module.

---

### pulser_full_stop() { #pulser_full_stop data-toc-label="pulser_full_stop" }

```python
pulser_full_stop()    # zero out all pulse instructions
```

This is a special function for a complete stop of the pulse programmer, which means all the pulse instructions will be set to zero.

!!! note
    This function is only available for Pulse Blaster Micran.

---

### pulser_test_flag(flag) { #pulser_test_flag data-toc-label="pulser_test_flag" }

```python
pulser_test_flag('None')    # normal mode
pulser_test_flag('test')    # test mode
```

This is a special function for changing test mode. The function is usually used in GUI applications that use the device module.

**Allowed:** `'None'`, `'test'`
{: .enum }
