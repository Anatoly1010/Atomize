# List of available functions for other devices

Available devices:
- CPWplus 150 (RS-232); Tested 01/2021
- Solid-State Relay RODOS-10N (Ethernet); Tested 01/2021
- Discrete IO Module Owen-MK110-220.4DN.4R (RS-485); Tested 04/2021

Functions:
- [balance_weight()](#balance_weight)<br/>
- [relay_turn_on(number)](#turn_onnumber)<br/>
- [relay_turn_off(number)](#turn_offnumber)<br/>
- [discrete_io_input_counter(channel)](#discrete_io_input_counterchannel)<br/>
- [discrete_io_input_counter_reset(channel)](#discrete_io_input_counter_resetchannel)<br/>
- [discrete_io_input_state()](#discrete_io_input_state)<br/>
- [discrete_io_output_state(*state)](#discrete_io_output_statestate)<br/>


## Balances
```python3
balance_weight()
Arguments: none; Output: float.
Example: balance_weight() returns the current weight of the balances.
```
This function returns the current weight of the balances and should be called with no argument.

## Other
## Solid-sate relay Rodos-10N (Ethernet)
```python3
relay_turn_on(number)
Arguments: number = integer; Output: none.
Example: relay_turn_on(1) turns on the first channel of solid-state relay.
```
This function turns on the specified channel of the solid-state relay and should be called with one argument. Channel should be specified as integer in the range of 1 to 4.
```python3
relay_turn_off(number)
Arguments: number = integer; Output: none.
Example: relay_turn_off(2) turns off the second channel of solid-state relay.
```
This function turns off the specified channel of the solid-state relay and should be called with one argument. Channel should be specified as integer in the range of 1 to 4.

## Discrete Input-Output Module Owen-MK110-220.4DN.4R (RS-485)
```python3
discrete_io_input_counter(channel)
Arguments: channel = ['1','2','3','4']; Output: integer.
Example: discrete_io_input_counter('1') returns the counter value of the first input.
```
This function returns the counter value of the specified input channel of the discrete IO module. The function requires one argument that should be one of the following: [1','2','3','4'].
```python3
discrete_io_input_counter_reset(channel)
Arguments: channel = ['1','2','3','4']; Output: none.
Example: discrete_io_input_counter_reset('1') resets the counter value of the first input.
```
This function resets the counter of the specified input channel. The function requires one argument that should be one of the following: [1','2','3','4'].
```python3
discrete_io_input_state()
Arguments: none; Output: string ('1234' etc).
Example: discrete_io_input_state() returns the input states of the IO module in the format '1234'
that means inputs 1-4 are on.
```
This function returns the input channel states of the discrete IO module and should be called without argument. The output is in the form ['0','1','2',...'12',...'1234']. The meaning is the following: '0' - all inputs are off, '12' - inputs 1 and 2 are on, and so on.
```python3
discrete_io_output_state(*state)
Arguments: state = string ('1234' etc) or none; Output: none or string ('1234' etc).
Example: discrete_io_output_state('0') turns off all the outputs of the IO module. 
```
This function set or queries the output channel states of the discrete IO module. If an argument is specified the function sets specified state of the output channels. If there is no argument the function returns the current state of the output channels. The argument should be in the form ['0','1','2',...'12',...'1234']. The meaning is the following: '0' - all outputs are off, '12' - outputs 1 and 2 are on, and so on. The output format is the same as the described argument.
