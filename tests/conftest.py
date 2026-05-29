import os
import sys

# Ensure THIS repo's atomize package is imported, not an editable-installed
# fork that may shadow it. Prepending the repo root makes the path-based
# finder resolve `atomize` here. Must run before any `import atomize`, which
# is guaranteed because pytest imports conftest.py before collecting tests.
_REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)

import pytest


class FakeVisa:
    """Stand-in for a pyvisa resource / linux-gpib handle.

    Records every command sent via write()/query() and returns scripted
    responses, so device-module command strings and response parsing can be
    exercised with no hardware. read() feeds the GPIB write->read path.
    """

    def __init__(self, responses=()):
        self.written = []
        self._responses = list(responses)

    def write(self, command):
        self.written.append(command)

    def read(self):
        return self._responses.pop(0)

    def query(self, command):
        self.written.append(command)
        return self._responses.pop(0)


class FakeModbus:
    """Stand-in for a minimalmodbus.Instrument. Records register writes as
    (register, value, decimals, functioncode, signed) tuples and returns
    scripted register reads (default 0)."""

    def __init__(self, registers=None):
        self.writes = []
        self.registers = dict(registers or {})

    def write_register(self, register, value, decimals, functioncode=16, signed=False):
        self.writes.append((register, value, decimals, functioncode, signed))

    def read_register(self, register, decimals, signed=False):
        return self.registers.get(register, 0)


@pytest.fixture(autouse=True)
def _no_sleep(monkeypatch):
    """Neutralize real sleeps so the suite stays fast. Both general.wait() (the
    GPIB write->read settle delay) and Termodat's device_read_signed delay
    ultimately call time.sleep(), so patching time.sleep covers both -- without
    replacing general.wait itself, which the general_functions tests exercise
    for real."""
    import time
    monkeypatch.setattr(time, "sleep", lambda *a, **k: None)


@pytest.fixture
def make_lakeshore():
    """Build a Lakeshore_335 with an injected FakeVisa, bypassing __init__
    (which would read config from disk and open a real connection).

    The duplicated dicts/limits below mirror Lakeshore_335.__init__; this
    duplication is the cost of the __new__ bypass and is exactly what a real
    injection seam in BaseDevice would remove.
    """
    import atomize.device_modules.Lakeshore_335 as ls_mod

    def _make(interface="rs232", responses=(), loop=1, test_flag="None"):
        dev = ls_mod.Lakeshore_335.__new__(ls_mod.Lakeshore_335)
        dev.config = {"interface": interface, "name": "Lakeshore 335"}
        dev.specific_parameters = {"loop": str(loop)}
        dev.loop_config = loop
        dev.heater_dict = {"50 W": 3, "5 W": 2, "0.5 W": 1, "Off": 0}
        dev.lock_dict = {"Local-Locked": 0, "Remote-Locked": 1,
                         "Local-Unlocked": 2, "Remote-Unlocked": 3}
        dev.loop_list = [1, 2]
        dev.sens_dict = {0: "None", 1: "A", 2: "B"}
        dev.temperature_max = 320
        dev.temperature_min = 0.3
        dev.test_flag = test_flag
        dev.status_flag = 1
        dev.device = FakeVisa(responses)
        if test_flag == "test":
            dev.test_temperature = 200.0
            dev.test_set_point = 298.0
            dev.test_lock = "Remote-Locked"
            dev.test_heater_range = "5 W"
            dev.test_heater_percentage = 1.0
            dev.test_sensor = "A"
        return dev

    return _make


@pytest.fixture
def make_owen():
    """Build an Owen_MK110_220_4DN_4R (ModbusDevice subclass) with an injected
    FakeModbus, bypassing __init__ (which would read config and open a real
    minimalmodbus connection)."""
    import atomize.device_modules.Owen_MK110_220_4DN_4R as owen_mod

    _state = {'0': '0', '1': '1', '2': '10', '3': '100', '4': '1000',
              '12': '11', '13': '101', '14': '1001', '23': '110', '24': '1010',
              '34': '1100', '123': '111', '124': '1011', '134': '1101',
              '234': '1110', '1234': '1111'}

    def _make(registers=None, test_flag="None"):
        dev = owen_mod.Owen_MK110_220_4DN_4R.__new__(owen_mod.Owen_MK110_220_4DN_4R)
        dev.config = {"interface": "rs485", "name": "Owen MK110"}
        dev.channel_dict = {"1": 1, "2": 2, "3": 3, "4": 4}
        dev.output_state_dict = dict(_state)
        dev.input_state_dict = dict(_state)
        dev.test_flag = test_flag
        dev.status_flag = 1
        dev.device = FakeModbus(registers)
        if test_flag == "test":
            dev.test_input_state = "0"
            dev.test_output_state = "0"
            dev.test_counter = 1
        return dev

    return _make


@pytest.fixture
def make_termodat():
    """Build a Termodat_11M6 / Termodat_13KX3 (ModbusDevice subclasses) with an
    injected FakeModbus, bypassing __init__."""
    import atomize.device_modules.Termodat_11M6 as t11_mod
    import atomize.device_modules.Termodat_13KX3 as t13_mod

    classes = {"11M6": t11_mod.Termodat_11M6, "13KX3": t13_mod.Termodat_13KX3}
    chans = {"11M6": {"1": 1, "2": 2, "3": 3, "4": 4}, "13KX3": {"1": 1, "2": 2}}

    def _make(model="11M6", registers=None, channels=None, test_flag="None"):
        cls = classes[model]
        dev = cls.__new__(cls)
        dev.config = {"interface": "rs485", "name": f"Termodat {model}"}
        dev.channel_dict = dict(chans[model])
        dev.state_dict = {"On": 1, "Off": 0}
        dev.channels = channels if channels is not None else len(chans[model])
        dev.temperature_max = 750
        dev.temperature_min = 0.3
        dev.proportional_min = 0.1
        dev.proportional_max = 2000
        dev.derivative_min = 0.0
        dev.derivative_max = 999.9
        dev.integral_min = 0
        dev.integral_max = 9999
        dev.test_flag = test_flag
        dev.status_flag = 1
        dev.device = FakeModbus(registers)
        if test_flag == "test":
            dev.test_temperature = 300
            dev.test_set_point = 273
            dev.test_power = 0
            dev.test_loop_state = "Off"
            dev.test_proportional = 70
            dev.test_derivative = 50
            dev.test_integral = 600
        return dev

    return _make
