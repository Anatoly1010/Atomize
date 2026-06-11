# Protocol Settings

It is possible to list in the terminal available instruments connected to your computer using pyvisa. This feature is available in the Output dock of the Main window by a right-click.

## VXI-11

Typical ethernet (via VXI-11 or TCP/IP Socket) settings are:

### Computer

```ini
Address = 192.168.2.1
Netmask = 255.255.255.0
Gateway = 255.255.255.0
DNS     = Manual 192.168.2.1
Routes  = Manual
```

### Device

```ini
Address = 192.168.2.20    ; this address should be inserted in the device configuration file
Netmask = 255.255.255.0
Gateway = 192.168.2.1     ; the host address
DNS     = 192.168.2.1     ; the host address
```

## RS-232

Typical rs-232 settings are:

```ini
Baudrate          = 9600
Databits          = 8
Startbits         = 1
Stopbits          = one
Parity            = none
Read termination  = r
Write termination = n
```

Generally, these settings are device specific. Sometimes the user has a possibility to change them on the device, sometimes they are fixed. In both cases correct settings should be specified in the device configuration file. Symbol `r` in the configuration file means `\r` (carriage return). Symbol `n` means `\n` (line feed). Their combination should be specified as `rn` or `nr` when you use it in [the configuration file](usage.md). One can use the special feature in the Output dock of the Main tab to open the local directory with the device configuration files.

Additionally, there are still two types of devices: DTE and DCE. DTE devices typically (but not always!) have male type connectors, while DCE have female connectors. In order to connect DTE device with computer (also DTE device), one needs to use a null-modem cable. For DCE device the standard cable can be used.

## RS-485

Typical rs-485 settings are:

```ini
Baudrate      = 19200
Databits      = 8
Startbits     = 1
Stopbits      = one
Parity        = none
Slave Address = 1
Mode          = RTU
```

Generally, these settings are device specific.

## GPIB

First of all you need to install gpib library on your computer. For linux one can use [linux-gpib](https://linux-gpib.sourceforge.io/). After successfully installing the gpib library, you must specify the board address (usually 0) and the pad of your device in [the configuration file](usage.md):

```ini
Board = 0

; linux-gpib backend:
Address = 12
; pyvisa-py backend:
Address = GPIB0::12::INSTR
```

The timeout setting should be set in the `number + SI suffix` format and it corresponds to the following dictionary:

| Timeout  | Value |
| -------- | ----- |
| `10 us`  | 1     |
| `30 us`  | 2     |
| `100 us` | 3     |
| `300 us` | 4     |
| `1 ms`   | 5     |
| `3 ms`   | 6     |
| `10 ms`  | 7     |
| `30 ms`  | 8     |
| `100 ms` | 9     |
| `300 ms` | 10    |
| `1 s`    | 11    |
| `3 s`    | 12    |
| `10 s`   | 13    |
| `30 s`   | 14    |
| `100 s`  | 15    |
| `300 s`  | 16    |
| `1000 s` | 17    |

If there is no timeout setting fitting the argument the nearest available value is used and warning is printed. A detailed instruction for the linux-gpib library installation can be found [here](https://gist.github.com/ochococo/8362414fff28fa593bc8f368ba94d46a). By default device modules use only `@linux-gpib` backend, other cases are directly indicated in the documentation.
