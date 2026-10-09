from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from feasibility_probe import normalized, symbol_from_member


def test_symbol_member_matching_is_exact():
    assert symbol_from_member("stocks/SBIN_1m.csv.gz") == "SBIN"
    assert symbol_from_member("DLF_1m.csv.gz") == "DLF"
    assert symbol_from_member("NOTSBIN_1m.csv.gz") is None


def test_master_headers_are_normalized_without_guessing_values():
    assert normalized({"Market Lot": "750", "Instrument Type": "OPTSTK"}) == {
        "MARKETLOT": "750",
        "INSTRUMENTTYPE": "OPTSTK",
    }
