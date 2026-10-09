from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "untouched_validation"))

from source_probe import DEV_END, DEV_START, REQUIRED


def test_development_boundary_is_exact_and_excluded():
    assert DEV_START == "2024-10-15"
    assert DEV_END == "2024-10-31"


def test_required_universe_cannot_silently_change():
    assert REQUIRED == ("SBIN", "DLF", "RELIANCE")

