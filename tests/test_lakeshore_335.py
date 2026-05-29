"""Layer-2 characterization tests: Lakeshore_335 command construction and
response parsing, exercised through an injected FakeVisa (no hardware).

These lock in the EXACT command strings and parsed return values of the real
(test_flag != 'test') path -- the part the built-in test mode never touches.
Run them before refactoring onto BaseDevice and again after: green means the
refactor (including the bytes/str decode normalization) preserved behavior.
"""
import pytest


# --- command construction + response parsing (real path) ---

def test_name_rs232_returns_str(make_lakeshore):
    dev = make_lakeshore("rs232", responses=["Lakeshore 335 answer"])
    assert dev.tc_name() == "Lakeshore 335 answer"
    assert dev.device.written == ["*IDN?"]


def test_name_gpib_decodes_bytes(make_lakeshore):
    dev = make_lakeshore("gpib", responses=[b"LSCI,MODEL335"])
    assert dev.tc_name() == "LSCI,MODEL335"          # gpib path .decode()s the answer
    assert dev.device.written == ["*IDN?"]


def test_temperature_channel_a(make_lakeshore):
    dev = make_lakeshore("rs232", responses=["298.5"])
    assert dev.tc_temperature("A") == 298.5
    assert dev.device.written == ["KRDG? A"]


def test_temperature_channel_b(make_lakeshore):
    dev = make_lakeshore("rs232", responses=["77.0"])
    assert dev.tc_temperature("B") == 77.0
    assert dev.device.written == ["KRDG? B"]


def test_temperature_ethernet(make_lakeshore):
    # ethernet routes device_query through .query() (same path as rs232)
    dev = make_lakeshore("ethernet", responses=["298.5"])
    assert dev.tc_temperature("A") == 298.5
    assert dev.device.written == ["KRDG? A"]


def test_setpoint_write(make_lakeshore):
    dev = make_lakeshore("rs232", loop=1)
    dev.tc_setpoint(298.0)
    assert dev.device.written == ["SETP 1,298.0"]


def test_setpoint_read(make_lakeshore):
    dev = make_lakeshore("rs232", responses=["298.0"], loop=1)
    assert dev.tc_setpoint() == 298.0
    assert dev.device.written == ["SETP? 1"]


def test_heater_range_write(make_lakeshore):
    dev = make_lakeshore("rs232", loop=1)
    dev.tc_heater_range("5 W")                       # heater_dict['5 W'] == 2
    assert dev.device.written == ["RANGE 1,2"]


def test_heater_range_read(make_lakeshore):
    dev = make_lakeshore("rs232", responses=["2"], loop=1)
    assert dev.tc_heater_range() == "5 W"
    assert dev.device.written == ["RANGE? 1"]


def test_sensor_read_rs232(make_lakeshore):
    # 'OUTMODE?1' -> '1,2,0'; rs232 parses index [2] == '2' -> sens_dict[2]
    dev = make_lakeshore("rs232", responses=["1,2,0"], loop=1)
    assert dev.tc_sensor() == "B"
    assert dev.device.written == ["OUTMODE?1"]


def test_lock_read_remote_unlocked(make_lakeshore):
    # LOCK? -> '0,123' (lock=0), MODE? -> '1' (remote=1) -> flag 3 -> 'Remote-Unlocked'
    dev = make_lakeshore("rs232", responses=["0,123", "1"], loop=1)
    assert dev.tc_lock_keyboard() == "Remote-Unlocked"
    assert dev.device.written == ["LOCK?", "MODE?"]


def test_lock_set_remote_locked(make_lakeshore):
    dev = make_lakeshore("rs232")
    dev.tc_lock_keyboard("Remote-Locked")            # flag 1 -> LOCK 1,123 then MODE 1
    assert dev.device.written == ["LOCK 1,123", "MODE 1"]


# --- test-mode (canned) characterizations ---

def test_testmode_temperature_no_io(make_lakeshore):
    dev = make_lakeshore(test_flag="test")
    assert dev.tc_temperature("A") == 200.0
    assert dev.device.written == []                  # test mode performs no I/O


def test_testmode_setpoint_roundtrip(make_lakeshore):
    dev = make_lakeshore(test_flag="test")
    dev.tc_setpoint(250.0)
    assert dev.tc_setpoint() == 250.0


# --- argument-validation guards (test mode) ---

def test_setpoint_out_of_range_asserts(make_lakeshore):
    dev = make_lakeshore(test_flag="test")
    with pytest.raises(AssertionError):
        dev.tc_setpoint(500.0)                       # above temperature_max (320)


def test_temperature_bad_channel_asserts(make_lakeshore):
    dev = make_lakeshore(test_flag="test")
    with pytest.raises(AssertionError):
        dev.tc_temperature("Z")
