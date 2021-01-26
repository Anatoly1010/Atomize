# List of available functions for other devices

Available devices:
- CPWplus 150 (RS-232); Tested 01/2021
- Solid-state Relay RODOS-10N (Ethernet); Tested 01/2021

[balance_weight()](#balance_weight)<br/>
[turn_on(number)](#turn_onnumber)<br/>
[turn_off(number)](#turn_offnumber)<br/>

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
turn_on(number)
Arguments: number = integer; Output: none.
Example: turn_on(1) turns on the first channel of solid-state relay.
```
This function turns on the specified channel of the solid-state relay and should be called with one argument. Channel should be specified as integer in the range of 1 to 4.
```python3
turn_off(number)
Arguments: number = integer; Output: none.
Example: turn_on(2) turns off the second channel of solid-state relay.
```
This function turns off the specified channel of the solid-state relay and should be called with one argument. Channel should be specified as integer in the range of 1 to 4.