# List of available functions for other devices

## Frequency counters
### freq_counter_name()
#### Arguments: none; Output: string(name).
The function returns device name.
### freq_counter_get_frequency(channel)
#### Arguments: channel = integer; Output: float.
This function returns a floating point value with the measured frequency. Possible channels and their meaning are the following:<br/>
'1' - channel 1; '2' - channel 2; '3' - channel 3.<br/>

## Magnetic Field Controller
### field_controller_set_field(\*field)
### field_controller_command(command)

## Balances
### balance_weight()

## Other
## Solid-sate Relay RODOS-10N (ethernet)
### turn_on(number)
### turn_off(number)
