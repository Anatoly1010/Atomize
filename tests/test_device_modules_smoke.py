"""Broad, cheap safety net over every device module.

`test_module_compiles` catches the Termodat-style breakage (a module that
doesn't even parse) across all modules at once. `test_module_instantiates`
goes one step further and constructs each device in test mode (no hardware);
modules whose vendor driver/library isn't installed here are skipped, not
failed.
"""
import importlib
import pathlib
import sys

import pytest

DEVICE_DIR = pathlib.Path(__file__).resolve().parent.parent / "atomize" / "device_modules"

# Infrastructure base classes (class name != filename, not instantiable on their own)
BASE_MODULES = {"base_device", "modbus_device"}

ALL_MODULES = [p.stem for p in sorted(DEVICE_DIR.glob("*.py")) if p.stem != "__init__"]
DEVICE_MODULES = [n for n in ALL_MODULES if n not in BASE_MODULES]

# Intentional, accepted deviations from the class==filename convention.
# PB_ESR_500_pro.py defines class PB_ESR_500_Pro (capital P); ~80 example scripts
# call PB_ESR_500_Pro(), and the file stays lowercase so their lowercase imports
# keep working (Python enforces import case-sensitivity), so the name is kept.
KNOWN_NAME_DEVIATIONS = {
    "PB_ESR_500_pro": "class is PB_ESR_500_Pro (capital P); kept intentionally — "
                      "renaming either side would churn ~80 caller scripts",
}


@pytest.mark.parametrize("name", ALL_MODULES)
def test_module_compiles(name):
    source = (DEVICE_DIR / f"{name}.py").read_text(encoding="utf-8")
    compile(source, f"{name}.py", "exec")   # SyntaxError fails the test


@pytest.mark.parametrize("name", DEVICE_MODULES)
def test_module_instantiates_in_test_mode(name, monkeypatch):
    if name in KNOWN_NAME_DEVIATIONS:
        pytest.xfail(KNOWN_NAME_DEVIATIONS[name])
    # the device reads sys.argv[1] in its __init__ to decide test mode
    monkeypatch.setattr(sys, "argv", ["atomize", "test"])
    # read configs straight from the repo (always complete), not the user copy
    # which is only populated once and may be missing newer device configs
    monkeypatch.setattr("atomize.main.local_config.load_config_device",
                        lambda: str(DEVICE_DIR / "config"))

    try:
        module = importlib.import_module(f"atomize.device_modules.{name}")
    except (ImportError, OSError) as exc:
        pytest.skip(f"driver/dependency unavailable: {exc!r}")

    cls = getattr(module, name, None)
    assert cls is not None, (
        f"module {name} has no class named {name} (class==filename convention)")

    try:
        cls()
    except (ImportError, OSError) as exc:
        pytest.skip(f"driver/dependency unavailable at init: {exc!r}")
    except KeyError as exc:
        # read_conf_util raises KeyError('name') when the config file is
        # missing/empty -- a packaging/env gap, not a code bug. Any other
        # missing key (e.g. a specific_parameters typo) is a real bug -> fail.
        if exc.args and exc.args[0] == "name":
            pytest.skip(f"config file missing or empty for {name} (no DEFAULT.name)")
        raise
    except SystemExit:
        pytest.fail(f"{name}() called sys.exit() during test-mode init")
