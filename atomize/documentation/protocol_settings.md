---
title: Protocol Settings
nav_order: 6
layout: page
permlink: /protocol_settings/
---
<br/>
- [VXI-11](#vxi-11)
- [RS-232](#rs-232)
- [RS-485](#rs-485)
- [GPIB](#gpib)

---

## VXI-11
Typical ethernet (via VXI-11 or TCP/IP Socket) settings are:

### Computer
```yml
    Address: 192.168.2.1
    Netmask: 255.255.255.0
    Gateway: 255.255.255.0
    DNS: Manual 192.168.2.1
    Routes: Manual
```

### Device
```yml
    Address: 192.168.2.20 (this address should be inserted in the device configuration file)
    Netmask: 255.255.255.0
    Gateway: 192.168.2.1 (the host address)
    DNS: 192.168.2.1 (the host address)
```

---

## RS-232
Typical rs-232 settings are:
```yml
    Baudrate: 9600
    Databits = 8
    Startbits = 1
    Stopbits = one
    Parity = none
    Read termination = r
    Write termination = n
```

Generally, these settings are device specific. Sometimes the user has a possibility to change them on the device, sometimes they are fixed. In both cases correct settings should be specified in the device configuration file. Symbol 'r' in the configuration file means '\r' (carrige return). Symbol 'n' means '\n' (line feed). Their combination should be specified as 'rn' or 'nr' when you use it in the configuration file.

Additionally, there are still two types of devices: DTE and DCE. DTE devices typically (but not always!) have male type connectors, while DCE have female connectors. In order to connect DTE device with computer (also DTE device), one needs to use a null-modem cable. For DCE device the standard cable can be used.

---

## RS-485
Typical rs-232 settings are:
```yml
    Baudrate: 19200
    Databits = 8
    Startbits = 1
    Stopbits = one
    Parity = none
    Slave Address = 1
    Mode = RTU
```
Generally, these settings are device specific. 

---

## GPIB
First of all you need to install gpib library on your computer. For linux one can use [linux-gpib](https://linux-gpib.sourceforge.io/). After successfully installing the gpib library, you must specify the board address (usually 0) and the pad of your device in the config file:
```yml
    Board = 0
    Address = 12
```

The timeout option corresponds to the following dictionarey: { 'Never': 0, '10 us': 1, '30 us': 2, '100 us': 3, '300 us': 4, '1 ms': 5, '3 ms': 6, '10 ms': 7, '30 ms': 8, '100 ms': 9, '300 ms': 10, '1 s': 11, '3 s': 12, '10 s': 13, '30 s': 14, '100 s': 15, '300 s': 16, '1000 s': 17}. A detailed instruction for the linux-gpib library installation can be found [here](https://gist.github.com/ochococo/8362414fff28fa593bc8f368ba94d46a).
