"""Characterization tests for Termodat_11M6 / Termodat_13KX3 (ModbusDevice).

These modules previously did not even compile (nested-quote syntax errors plus
an `elif self.test_flag != 'test'` typo that made their test branches dead).
The migration fixed those, so these tests also lock in the now-working test
branches. Exercised via an injected FakeModbus -- no hardware.
"""
import pytest


def test_temperature_11m6(make_termodat):
    # register 368, signed read, + 273.16, rounded to 1 decimal
    dev = make_termodat("11M6", registers={368: 26.84})
    assert dev.tc_temperature("1") == 300.0


def test_temperature_13kx3(make_termodat):
    # 13KX3 offsets by 273.15 (not .16)
    dev = make_termodat("13KX3", registers={368: 26.85})
    assert dev.tc_temperature("1") == 300.0


def test_setpoint_write_fc6_signed(make_termodat):
    dev = make_termodat("11M6")
    dev.tc_setpoint("1", 300.0)                     # register 369, value - 273.16
    assert len(dev.device.writes) == 1
    reg, val, dec, fc, signed = dev.device.writes[0]
    assert (reg, dec, fc, signed) == (369, 1, 6, True)
    assert val == pytest.approx(300.0 - 273.16)


def test_setpoint_read(make_termodat):
    dev = make_termodat("11M6", registers={369: 26.84})
    assert dev.tc_setpoint("1") == 300.0


def test_proportional_write_fc6_unsigned(make_termodat):
    dev = make_termodat("11M6")
    dev.tc_proportional("1", 7.0)                   # register 386, value * 10
    assert dev.device.writes == [(386, 70.0, 0, 6, False)]


def test_proportional_read(make_termodat):
    dev = make_termodat("11M6", registers={386: 70})
    assert dev.tc_proportional("1") == 7.0          # raw / 10


def test_sensor_write(make_termodat):
    dev = make_termodat("11M6")
    dev.tc_sensor("1", "On")                        # state 'On' -> 1, register 384
    assert dev.device.writes == [(384, 1, 0, 6, False)]


def test_sensor_read(make_termodat):
    dev = make_termodat("11M6", registers={384: 1})
    assert dev.tc_sensor("1") == "On"


# --- the branches that were broken before the migration ---

def test_testmode_proportional_returns_canned(make_termodat):
    dev = make_termodat("11M6", test_flag="test")
    assert dev.tc_proportional("1") == 70           # was dead code (elif != 'test')
    assert dev.device.writes == []


def test_testmode_proportional_out_of_range_asserts(make_termodat):
    dev = make_termodat("11M6", test_flag="test")
    with pytest.raises(AssertionError):
        dev.tc_proportional("1", 9999.0)            # 99990 > proportional_max


def test_testmode_integral_bad_channel_asserts(make_termodat):
    dev = make_termodat("13KX3", test_flag="test")
    with pytest.raises(AssertionError):
        dev.tc_integral("9", 100)                   # '9' not a valid channel
