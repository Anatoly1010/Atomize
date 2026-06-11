# Instrument modules

## [Arbitrary waveform generators](functions/awg.md)

| Device                                                                                   | Tested  | Notes                                                                                                                                            |
| ---------------------------------------------------------------------------------------- | ------- | ------------------------------------------------------------------------------------------------------------------------------------------------ |
| Spectrum M4I 6631 X8                                                                     | 07/2021 | [Library](https://spectrum-instrumentation.com/en/m4i6631-x8) by Spectrum                                                                        |
| [Insys FM214x3GDA](https://www.insys.ru/mezzanine/fm214x3gda) (as DAC)                   | 03/2025 | Available via `ctypes`; library in [Atomize_ITC](https://github.com/Anatoly1010/Atomize_ITC/tree/master/libs)                                    |

## [Delay generators](functions/delay_generator.md)

| Device                       | Connection | Tested   |
| ---------------------------- | ---------- | -------- |
| Stanford Research DG535      | GPIB       | Untested |

## [Digitizers](functions/digitizer.md)

| Device                                                                            | Tested  | Notes                                                                                                                                            |
| --------------------------------------------------------------------------------- | ------- | ------------------------------------------------------------------------------------------------------------------------------------------------ |
| Spectrum M4I 4450 X8                                                              | 08/2021 | [Library](https://spectrum-instrumentation.com/en/m4i4450-x8) by Spectrum                                                                        |
| Spectrum M4I 2211 X8                                                              | 01/2021 | [Library](https://spectrum-instrumentation.com/en/m4i4450-x8) by Spectrum                                                                        |
| [Insys FM214x3GDA](https://www.insys.ru/mezzanine/fm214x3gda) (as ADC)            | 03/2025 | Available via `ctypes`; library in [Atomize_ITC](https://github.com/Anatoly1010/Atomize_ITC/tree/master/libs)                                    |
| L card L-502 (as ADC)                                                             | 03/2022 | Available via `ctypes`; [library](https://www.lcard.ru/products/boards/l-502?qt-ltab=6#qt-ltab)                                                  |

## [Frequency counters](functions/freq_counter.md)

| Device                                       | Connection                | Tested   |
| -------------------------------------------- | ------------------------- | -------- |
| Agilent 53181A; 53131A/132A Frequency Counter | GPIB, RS-232              | 02/2021  |
| Agilent 5343A Frequency Counter              | GPIB                      | 02/2023  |
| Keysight 53230A/220A Frequency Counter       | GPIB, RS-232, Ethernet    | Untested |

## [Gaussmeters](functions/gaussmeter.md)

| Device                       | Connection      | Tested  |
| ---------------------------- | --------------- | ------- |
| Lakeshore 455 DSP            | RS-232          | 01/2021 |
| NMR Gaussmeter Sibir 1       | UDP/IP Socket   | 04/2024 |

## [Laser power meters](functions/laser_power_meter.md)

| Device                | Connection | Tested  |
| --------------------- | ---------- | ------- |
| Gentec-EO Solo2       | RS-232     | 12/2025 |

## [Lock-in amplifiers](functions/lock_in.md)

| Device                                                       | Connection             | Tested   |
| ------------------------------------------------------------ | ---------------------- | -------- |
| Stanford Research SR-810, SR-830, SR-850 Lock-In Amplifier   | GPIB, RS-232           | 02/2021  |
| Stanford Research SR-844 Lock-In Amplifier                   | GPIB, RS-232           | Untested |
| Stanford Research SR-860, SR-865a Lock-In Amplifier          | GPIB, RS-232, Ethernet | 01/2021  |

## [Magnetic field controllers](functions/magnet.md)

| Device                                                                                    | Connection                          | Tested  | Notes                       |
| ----------------------------------------------------------------------------------------- | ----------------------------------- | ------- | --------------------------- |
| Bruker BH15                                                                               | GPIB                                | 01/2021 |                             |
| Bruker ER032M                                                                             | GPIB                                | —       | Available via BH15 module   |
| Bruker ER031M                                                                             | RS-232 (arduino emulated keyboard)  | 01/2021 |                             |
| [Homemade magnetic field controller](https://patents.google.com/patent/RU2799103C1/en?oq=RU2799103C1) | RS-232                          | 04/2023 |                             |

## [Magnet power supplies](functions/magnet_power_supply.md)

| Device              | Connection | Tested  |
| ------------------- | ---------- | ------- |
| Cryomagnetics 4G    | Ethernet   | 11/2023 |

## [Microwave bridges](functions/microwave_bridge.md)

| Device                          | Connection      | Tested  |
| ------------------------------- | --------------- | ------- |
| Micran X-band MW Bridge         | TCP/IP Socket   | 06/2021 |
| Micran X-band MW Bridge v2      | TCP/IP Socket   | 12/2022 |
| Micran Q-band MW Bridge         | TCP/IP Socket   | 12/2023 |

## [Moisture meters](functions/moisture_meter.md)

| Device   | Connection | Tested  |
| -------- | ---------- | ------- |
| IVG-1/1  | RS-485     | 02/2023 |

## [Oscilloscopes](functions/oscilloscope.md)

| Device                                | Connection | Tested   |
| ------------------------------------- | ---------- | -------- |
| Keysight InfiniiVision 2000 X-Series  | Ethernet   | 07/2021  |
| Keysight InfiniiVision 3000 X-Series  | Ethernet   | 06/2021  |
| Keysight InfiniiVision 4000 X-Series  | Ethernet   | Untested |
| Tektronix 3000 Series                 | Ethernet   | 09/2022  |
| Tektronix 4000 Series                 | Ethernet   | 01/2021  |
| Tektronix 5 Series MSO                | Ethernet   | 12/2023  |
| Rigol MSO8000 Series                  | Ethernet   | 01/2026  |

## [Power supplies](functions/power_supply.md)

| Device                                                | Connection      | Tested   |
| ----------------------------------------------------- | --------------- | -------- |
| Rigol DP800 Series                                    | RS-232, Ethernet | 01/2021  |
| Stanford Research DC205                               | RS-232          | Untested |
| Stanford Research PS300 High Voltage Series           | RS-232, GPIB    | Untested |

## [Pulse programmers](functions/pulse_programmer.md)

| Device                                                                                                                                  | Tested  | Notes                                                                                                                                                |
| --------------------------------------------------------------------------------------------------------------------------------------- | ------- | ---------------------------------------------------------------------------------------------------------------------------------------------------- |
| Pulse Blaster ESR 500 Pro                                                                                                               | 06/2021 | Available via `ctypes`; original [C library](http://www.spincore.com/support/spinapi/using_spin_api_pb.shtml) by SpinCore Technologies                |
| Pulse Programmer Micran (based on [Insys FMC126P](https://www.insys.ru/fmc/fmc126p))                                                    | 12/2023 |                                                                                                                                                      |
| [Insys FM214x3GDA](https://www.insys.ru/mezzanine/fm214x3gda) (as multichannel TTL pulse generator)                                     | 03/2025 | Available via `ctypes`; library in [Atomize_ITC](https://github.com/Anatoly1010/Atomize_ITC/tree/master/libs)                                        |

## [Synthetizers](functions/synthetizer.md)

| Device    | Connection | Tested  |
| --------- | ---------- | ------- |
| ECC 15K   | RS-232     | 01/2023 |

## [Temperature controllers](functions/temp_controller.md)

| Device                                            | Connection              | Tested  |
| ------------------------------------------------- | ----------------------- | ------- |
| Lakeshore 325, 331, 332, 335, 336, 340            | GPIB, RS-232            | 01/2021 |
| Oxford Instruments ITC 503                        | RS-232                  | 01/2021 |
| Termodat 11M6, 13KX3                              | RS-485                  | 04/2021 |
| Stanford Research PTC10                           | TCP/IP Socket           | 07/2021 |
| Scientific Instruments SCM10                      | TCP/IP Socket, RS-232   | 07/2022 |

## [Vector network analyzers](functions/vector_network_analyzer.md)

| Device                  | Connection | Tested  |
| ----------------------- | ---------- | ------- |
| Planar C2220, S50024    | Socket     | 09/2025 |

## [Waveform generators](functions/wave_generator.md)

| Device                                                          | Connection | Tested   | Notes                                            |
| --------------------------------------------------------------- | ---------- | -------- | ------------------------------------------------ |
| Waveform Generator of Keysight InfiniiVision 2000 X-Series      | Ethernet   | —        | Available via corresponding oscilloscope module  |
| Waveform Generator of Keysight InfiniiVision 3000 X-Series      | Ethernet   | —        | Available via corresponding oscilloscope module  |
| Waveform Generator of Keysight InfiniiVision 4000 X-Series      | Ethernet   | —        | Available via corresponding oscilloscope module  |
| Waveform Generator of Rigol MSO8000 Series                      | Ethernet   | —        | Available via corresponding oscilloscope module  |
| Stanford Research DS345                                         | RS-232     | Untested |                                                  |

## [Other devices](functions/other_device.md)

| Device                                            | Connection      | Tested  |
| ------------------------------------------------- | --------------- | ------- |
| CPWplus 150                                       | RS-232          | 01/2021 |
| RODOS-10N Solid-State Relay                       | Ethernet        | 01/2021 |
| Owen-MK110-220.4DN.4R Discrete IO Module          | RS-485          | 04/2021 |
| Cryomagnetics LM-510 Liquid Cryogen Monitor       | TCP/IP Socket   | 07/2022 |
| Cryomech CPA2896, CPA1110 Digital Panels          | RS-485          | 07/2022 |
