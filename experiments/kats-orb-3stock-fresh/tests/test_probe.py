from datetime import datetime
from pathlib import Path
import importlib.util

MODULE_PATH = Path(__file__).parents[1] / "probe.py"
SPEC = importlib.util.spec_from_file_location("fresh_probe", MODULE_PATH)
probe = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(probe)


def test_timestamp_formats_are_explicit():
    assert probe.parse_timestamp("2024-11-11", "09:15:00") == datetime(2024, 11, 11, 9, 15)
    assert probe.parse_timestamp("11-11-2024", "09:15:00") == datetime(2024, 11, 11, 9, 15)
    assert probe.parse_timestamp("not-a-date", "09:15") is None


def test_option_regex_requires_symbol_strike_and_type():
    match = probe.OPTION_RE.search("NFO:SBIN28NOV24750CE.NFO")
    assert match is not None
    assert match.group(1).upper() == "SBIN"
    assert match.group(3).upper() == "CE"
    assert probe.OPTION_RE.search("SBIN-EQ") is None

