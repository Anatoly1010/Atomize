"""Characterization tests for Owen_MK110_220_4DN_4R (ModbusDevice subclass).

Exercises the real (test_flag != 'test') path through an injected FakeModbus:
register addresses, decimals, the unsigned write function code (16), and the
bit-pattern parsing of the input/output state words. No hardware.
"""


def test_name(make_owen):
    dev = make_owen()
    assert dev.discrete_io_name() == "Owen MK110"


def test_input_counter_reads_register(make_owen):
    # channel '1' -> register 63 + 1 = 64
    dev = make_owen(registers={64: 7})
    assert dev.discrete_io_input_counter("1") == 7


def test_input_counter_reset_writes_register(make_owen):
    dev = make_owen()
    dev.discrete_io_input_counter_reset("2")           # register 63 + 2 = 65
    assert dev.device.writes == [(65, 0, 0, 16, False)]  # functioncode 16, unsigned


def test_input_state_bit_parsing(make_owen):
    # register 51 -> 5 -> bin '101' -> input_state_dict reverse-lookup -> '13'
    dev = make_owen(registers={51: 5})
    assert dev.discrete_io_input_state() == "13"


def test_output_state_write(make_owen):
    # '13' -> output_state_dict['13'] == '101' -> int('101', 2) == 5 -> register 50
    dev = make_owen()
    dev.discrete_io_output_state("13")
    assert dev.device.writes == [(50, 5, 0, 16, False)]


def test_output_state_read(make_owen):
    dev = make_owen(registers={50: 5})
    assert dev.discrete_io_output_state() == "13"


def test_testmode_no_io(make_owen):
    dev = make_owen(test_flag="test")
    assert dev.discrete_io_input_counter("1") == 1
    assert dev.device.writes == []                     # test mode performs no I/O


def test_input_counter_bad_channel_asserts(make_owen):
    import pytest
    dev = make_owen(test_flag="test")
    with pytest.raises(AssertionError):
        dev.discrete_io_input_counter("9")
