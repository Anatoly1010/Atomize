# List of available devices

## Contents
- [Temperature Controllers](#temperature-controllers)<br/>
- [Lock-in Amplifiers](#lock-in-amplifiers)<br/>
- [Oscilloscopes](#oscilloscopes)<br/>
- [Digitizers](#digitizers)<br/>
- [Oscilloscope Wave Generators](#oscilloscope-wave-generators)<br/>
- [Arbitrary Wave Generators](#arbitrary-wave-generators)<br/>
- [Pulse Programmers](#pulse-programmers)<br/>
- [Frequency Counters](#frequency-counters)<br/>
- [Magnetic Field Controllers](#magnetic-field-controllers)<br/>
- [Microwave Bridge Controllers](#microwave-bridge-controllers)<br/>
- [Gaussmeters](#gaussmeters)<br/>
- [Power Supplies](#power-supplies)<br/>
- [Magnet Power Supplies](#magnet-power-supplies)<br/>
- [Delay Generators](#delay-generators)<br/>
- [Moisture Meters](#moisture-meters)<br/>
- [Balance](#balances)<br/>
- [Other](#other)<br/>

## Temperature Controllers
- Lakeshore (GPIB, RS-232)
325; 331; 332; 335; 336; 340; Tested 01/21
- Oxford Instruments (RS-232)
ITC 503; Tested 01/21
- Termodat (RS-485)
11M6; 13KX3; Tested 04/21
- Stanford Research (TCP/IP Socket)
PTC10; Tested 07/21

## Lock-in Amplifiers
- Stanford Research Lock-In Amplifier (GPIB, RS-232)
SR-810; SR-830; SR-850 Tested 02/2021
- Stanford Research Lock-In Amplifier (GPIB, RS-232, Ethernet)
SR-860; SR-865a; Tested 01/2021

## Oscilloscopes
- Keysight InfiniiVision 2000 X-Series (Ethernet)
MSO-X 2004A; MSO-X 2002A; DSO-X 2004A; DSO-X 2002A; MSO-X 2014A; MSO-X 2012A; DSO-X 2014A; DSO-X 2012A; MSO-X 2024A; MSO-X 2022A; DSO-X 2024A; DSO-X 2022A.
- Keysight InfiniiVision 3000 X-Series (Ethernet); Tested 06/2021
MSO-X 3014A; MSO-X 3012A; DSO-X 3014A; DSO-X 3012A; MSO-X 3024A; DSO-X 3024A; MSO-X 3034A; MSO-X 3032A; DSO-X 3034A; DSO-X 3032A; MSO-X 3054A; MSO-X 3052A; DSO-X 3054A; DSO-X 3052A; MSO-X 3104A; MSO-X 3102A; DSO-X 3104A; DSO-X 3102A.
- Keysight InfiniiVision 4000 X-Series (Ethernet)
MSO-X 4022A; MSO-X 4024A; DSO-X 4022A; DSO-X 4024A; MSO-X 4032A; MSO-X 4034A; DSO-X 4032A; DSO-X 4034A; MSO-X 4052A; MSO-X 4054A; DSO-X 4052A; DSO-X 4054A; MSO-X 4104A; DSO-X 4104A; MSO-X 4154A; DSO-X 4154A.
- Tektronix 3000 Series (Ethernet); Tested 09/2022
- Tektronix 4000 Series (Ethernet); Tested 01/2021
- Tektronix 5 Series MSO (Ethernet); Tested 12/2023

## Digitizers
- Spectrum M4I 4450 X8; Tested 08/2021
- Spectrum M4I 2211 X8; Tested 01/2023
The original [library](https://spectrum-instrumentation.com/en/m4i4450-x8) was written by Spectrum.
- [Insys FM214x3GDA](https://www.insys.ru/mezzanine/fm214x3gda) as ADC; Tested 03/2025
The device is available via ctypes. The original library can be found [here](https://github.com/Anatoly1010/Atomize_ITC/tree/master/libs).

## Oscilloscope Wave Generators
- Wave Generator of Keysight InfiniiVision 2000 X-Series (Ethernet)
Available via corresponding oscilloscope module.
- Wave Generator of Keysight InfiniiVision 3000 X-Series (Ethernet)
Available via corresponding oscilloscope module.
- Wave Generator of Keysight InfiniiVision 4000 X-Series (Ethernet)
Available via corresponding oscilloscope module.

## Arbitrary Wave Generators
- Spectrum M4I 6631 X8; Tested 07/2021
The original [library](https://spectrum-instrumentation.com/en/m4i6631-x8) was written by Spectrum.
-  [Insys FM214x3GDA](https://www.insys.ru/mezzanine/fm214x3gda) as DAC; Tested 03/2025
The device is available via ctypes. The original library can be found [here](https://github.com/Anatoly1010/Atomize_ITC/tree/master/libs).

## Pulse Programmers
- Pulse Blaster ESR 500 Pro; Tested 06/2021
The device is available via ctypes. [The original C library](http://www.spincore.com/support/spinapi/using_spin_api_pb.shtml) was written by SpinCore Technologies.
- Pulse  Programmer Micran based on [Insys FMC126P](https://www.insys.ru/fmc/fmc126p); Tested 12/2023
- [Insys FM214x3GDA](https://www.insys.ru/mezzanine/fm214x3gda) as multichannel TTL pulse generator; Tested 03/2025
The Insys device is available via ctypes. The original library can be found [here](https://github.com/Anatoly1010/Atomize_ITC/tree/master/libs).

## Frequency Counters
- Agilent Frequency Counter (GPIB, RS-232)
53181A; 53131A/132A; Tested 01/2021
5343A; GPIB, Tested 02/2023
- Keysight Frequency Counter (GPIB, RS-232, Ethernet)
53230A/220A; Untested

## Magnetic Field Controllers
- Bruker BH15 (GPIB); Tested 01/2021
- Bruker ER032M (GPIB); available via BH15 module
- Bruker ER031M (RS-232 using arduino emulated keyboard); Tested 01/2021
- [Homemade](https://patents.google.com/patent/RU2799103C1/en?oq=RU2799103C1) magnetic field controller (RS-232); Tested 04/2023

## Microwave Bridge Controllers
- Micran X-band MW Bridge (TCP/IP Socket); Tested 06/2021
- Micran X-band MW Bridge v2 (TCP/IP Socket); Tested 12/2022
- Micran Q-band MW Bridge; Tested 12/2023

## Gaussmeters
- Lakeshore 455 DSP (RS-232); Tested 01/2021
- NMR Gaussmeter Sibir 1 (UDP/IP Socket); Tested 04/2024

## Power Supplies
- Rigol DP800 Series (RS-232, Ethernet); Tested 01/2021
- Stanford Research DC205 (RS-232); Untested
- Stanford Research PS300 High Voltage Series (RS-232, GPIB); Untested
PS310, PS325 (GPIB); PS350, PS355, PS365, PS370, PS375 (RS-232, GPIB)

## Magnet Power Supplies
- Cryomagnetics 4G (Ethernet); Testes 11/2023

## Delay Generators
- Stanford Research DG535 (GPIB); Untested

## Moisture Meters
- IVG-1/1 (RS-485); Tested 02/2023

## Balance
- CPWplus 150 (RS-232); Tested 01/2021

## Other
- RODOS-10N Solid-State Relay (Ethernet); Tested 01/2021
- Owen-MK110-220.4DN.4R Discrete IO Module (RS-485); Tested 04/2021
- Cryomagnetics LM-510 Liquid Cryogen Monitor (TCP/IP Socket); Tested 07/2022
- Cryomech CPA2896, CPA1110 Digital Panels (RS-485); Tested 07/2022