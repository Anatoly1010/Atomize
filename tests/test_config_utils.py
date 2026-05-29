"""Layer-1 tests: pure config-parsing helpers in config_utils.

No hardware, no device objects -- just .ini in, dict out. These guard the
silent config-parsing regressions that otherwise only surface on the bench.
"""
import textwrap

from pyvisa.constants import StopBits, Parity

import atomize.device_modules.config.config_utils as cutil


def _write_ini(tmp_path, **overrides):
    base = {
        "name": "Test Device", "type": "gpib", "timeout": "3000",
        "gpib_board": "0", "gpib_address": "12",
        "serial_address": "ASRL/dev/ttyUSB0::INSTR", "baudrate": "57600",
        "databits": "7", "parity": "odd", "stopbits": "one",
        "read_termination": "rn", "write_termination": "rn",
        "ethernet_address": "",
    }
    base.update(overrides)
    content = textwrap.dedent(f"""\
        [DEFAULT]
        name = {base['name']}
        type = {base['type']}
        timeout = {base['timeout']}

        [GPIB]
        board = {base['gpib_board']}
        address = {base['gpib_address']}

        [SERIAL]
        address = {base['serial_address']}
        baudrate = {base['baudrate']}
        databits = {base['databits']}
        parity = {base['parity']}
        stopbits = {base['stopbits']}
        read_termination = {base['read_termination']}
        write_termination = {base['write_termination']}

        [ETHERNET]
        address = {base['ethernet_address']}
        """)
    p = tmp_path / "dev_config.ini"
    p.write_text(content)
    return str(p)


def test_basic_fields(tmp_path):
    cfg = cutil.read_conf_util(_write_ini(tmp_path))
    assert cfg["name"] == "Test Device"
    assert cfg["interface"] == "gpib"
    assert cfg["gpib_address"] == 12
    assert cfg["board_address"] == 0


def test_gpib_timeout_maps_to_index(tmp_path):
    # 3000 ms is in the GPIB timeout table -> index 12
    cfg = cutil.read_conf_util(_write_ini(tmp_path, timeout="3000"))
    assert cfg["timeout"] == 12


def test_gpib_timeout_snaps_to_nearest(tmp_path):
    # 2500 -> nearest of {1000, 3000}: |2500-3000|=500 < |2500-1000|=1500 -> 3000 -> 12
    cfg = cutil.read_conf_util(_write_ini(tmp_path, timeout="2500"))
    assert cfg["timeout"] == 12


def test_non_gpib_timeout_passthrough(tmp_path):
    # for non-gpib transports the raw ms value is kept (not snapped/indexed)
    cfg = cutil.read_conf_util(_write_ini(tmp_path, type="rs232", timeout="3000"))
    assert cfg["timeout"] == 3000


def test_parity_mapping(tmp_path):
    assert cutil.read_conf_util(_write_ini(tmp_path, parity="odd"))["parity"] == Parity.odd
    assert cutil.read_conf_util(_write_ini(tmp_path, parity="even"))["parity"] == Parity.even
    assert cutil.read_conf_util(_write_ini(tmp_path, parity="none"))["parity"] == Parity.none


def test_stopbits_mapping(tmp_path):
    assert cutil.read_conf_util(_write_ini(tmp_path, stopbits="one"))["stopbits"] == StopBits.one
    assert cutil.read_conf_util(_write_ini(tmp_path, stopbits="two"))["stopbits"] == StopBits.two
    assert cutil.read_conf_util(
        _write_ini(tmp_path, stopbits="onehalf"))["stopbits"] == StopBits.one_and_a_half


def test_termination_mapping(tmp_path):
    cfg = cutil.read_conf_util(_write_ini(tmp_path, read_termination="rn", write_termination="r"))
    assert cfg["read_termination"] == "\r\n"
    assert cfg["write_termination"] == "\r"


def test_gpib_address_enet_string_kept(tmp_path):
    # a non-integer address starting with 'G' (e.g. ENET-GPIB) is kept as a string
    cfg = cutil.read_conf_util(_write_ini(tmp_path, gpib_address="G123"))
    assert cfg["gpib_address"] == "G123"


def test_search_keys_dictionary():
    d = {"50 W": 3, "5 W": 2, "0.5 W": 1, "Off": 0}
    assert cutil.search_keys_dictionary(d, 2) == "5 W"
    assert cutil.search_keys_dictionary(d, 0) == "Off"
    assert cutil.search_keys_dictionary(d, 99) is None
