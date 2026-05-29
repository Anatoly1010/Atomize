"""Unit tests for the pure helpers in general_functions (no Qt, no LivePlot)."""
import numpy as np
import pytest

import atomize.general_modules.general_functions as general


def test_round_to_closest():
    assert general.round_to_closest(7, 5) == 10
    assert general.round_to_closest(10, 5) == 10
    assert general.round_to_closest(11, 5) == 15
    assert general.round_to_closest(0, 5) == 0


def test_const_shift():
    assert general.const_shift('800 ns', 494) == '1294 ns'
    assert general.const_shift('0 ns', 10) == '10 ns'


def test_numpy_round():
    assert general.numpy_round(7, 5) == 5
    assert general.numpy_round(8, 5) == 10


def test_fmt():
    # width equal to the name length -> no padding
    assert general.fmt('Temp: 300', 5) == 'Temp: 300'
    # no colon -> returned unchanged
    assert general.fmt('no colon', 8) == 'no colon'


def test_format_message_str_strips_newlines():
    assert general._format_message(('hello\nworld',)) == 'helloworld'


def test_format_message_ndarray():
    assert general._format_message((np.array([1, 2, 3]),)) == '[1,2,3]'


def test_wait_test_mode_is_noop(monkeypatch):
    monkeypatch.setattr(general, 'test_flag', 'test')
    assert general.wait('10 ms') is None          # validates unit, does not sleep


def test_wait_test_mode_bad_unit_asserts(monkeypatch):
    monkeypatch.setattr(general, 'test_flag', 'test')
    with pytest.raises(AssertionError):
        general.wait('10 xs')


def test_to_infinity_test_mode_is_bounded(monkeypatch):
    monkeypatch.setattr(general, 'test_flag', 'test')
    assert list(general.to_infinity()) == list(range(50))


def test_scans_test_mode_runs_once(monkeypatch):
    monkeypatch.setattr(general, 'test_flag', 'test')
    assert list(general.scans(5)) == [1]
