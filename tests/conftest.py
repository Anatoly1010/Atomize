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


@pytest.fixture(autouse=True)
def _no_sleep(monkeypatch):
    """general.wait() really sleeps outside test mode; neutralize it so the
    50 ms GPIB write->read settle delay inside device_query doesn't slow the
    suite. Targeted so message()/plot() semantics are untouched."""
    import atomize.general_modules.general_functions as general
    monkeypatch.setattr(general, "wait", lambda *a, **k: None)


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
