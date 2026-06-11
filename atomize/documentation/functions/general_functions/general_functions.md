# General Functions

To call general functions a corresponding general function module should be imported.

```python
import atomize.general_modules.general_functions as general
```

## Print a string in the main window { #print-a-string-in-the-main-window }

```python
import atomize.general_modules.general_functions as general
general.message('A message to print', 'One more message', ...)
```

---

## Print a string in the main window in the test run { #print-a-string-in-the-main-window-in-the-test-run }

```python
import atomize.general_modules.general_functions as general
general.message_test('A message to print in the test run', 'One more message', ...)
```

---

## Send a message via Telegram bot { #send-a-message-via-telegram-bot }

To call this function Telegram bot token and message chat ID should be specified in the configuration file [MAIN CONFIG PATH](../../usage.md). General function module should be imported. After that the function should be used as follows:

```python
import atomize.general_modules.general_functions as general
general.bot_message('A message to send', 'One more message', ...)
```

---

## Wait for the specified amount of time { #wait-for-the-specified-amount-of-time }

To call this function a corresponding general function module should be imported. Function has one argument, which is a string of number and scaling factor (`ks`, `s`, `ms`, `us`):

```python
import atomize.general_modules.general_functions as general
general.wait('10 ms')
```

---

## Infinite loop { #infinite-loop }

Since all experimental scripts are tested before actually interacting with devices, a standard Python infinite loop like `while True` will stuck in the test mode. Instead, one can use a special function `general.to_infinity()`. This function imitates a standard infinite loop for which the first 50 loops will be checked in the test run.

```python
import atomize.general_modules.general_functions as general

for i in general.to_infinity():
    # DO SOMETHING
    general.message(i)
```

It is also possible to interrupt an infinite loop under certain conditions:

```python
for i in general.to_infinity():
    general.message(i)
    if i > 10:
        break
```

---

## Repeating scans in an experimental script { #repeating-scans }

In addition to an infinite loop, a standard Python loop with repeating scans will also waste extra time in the test mode. To tackle it, one can use a special function `general.scans(number_of_scans)`. This function imitates a standard loop for which only the first loop will be checked in the test run. Please, note that in this case there is no need to declare and iterate a loop iterator, i.e. See the example below for more details.

```python
import atomize.general_modules.general_functions as general

# Run 10 scans
for i in general.scans(10):
    # DO MEASUREMENTS
    general.message(i)
    # the output will be from 1 to 10
```

---

## Constant shift { #constant-shift }

To match the timescales of the DAC and the pulse generator a function `general.const_shift(str(initial_position) + ['ns', 'ms', 'us'], shift_in_ns)` can be used as shown below. The argument `initial_position` should be an integer number.

```python
import atomize.general_modules.general_functions as general
PULSE_AWG_2_START = '250 ns'
# SHIFT THE PULSE POSITION FROM 494 NS TO 744 NS
PULSE_2_START = general.const_shift(PULSE_AWG_2_START, 494)
```
