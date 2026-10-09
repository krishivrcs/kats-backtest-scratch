import importlib.util
import ast
import math
import sys
import unittest
from datetime import date, datetime, time, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

MODULE = Path(__file__).with_name("strict_integrity.py")
SPEC = importlib.util.spec_from_file_location("strict_integrity", MODULE)
s = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = s
SPEC.loader.exec_module(s)
IST = ZoneInfo("Asia/Kolkata")
DAY = date(2024, 6, 25)


def bar(minute=15, **overrides):
    values = dict(timestamp=datetime.combine(DAY, time(9, minute), IST), open=100.0,
                  high=101.0, low=99.0, close=100.5, volume=10.0)
    values.update(overrides)
    return s.Bar(**values)


def row(offset, **overrides):
    dt = datetime.combine(DAY, time(9, 15), IST) + timedelta(minutes=offset)
    values = {"time": str(int(dt.timestamp())), "open": "100", "high": "101",
              "low": "99", "close": "100.5", "Volume": "10"}
    values.update({key: str(value) for key, value in overrides.items()})
    return values


class StrictIntegrityTests(unittest.TestCase):
    def test_parse_timestamp_accepts_exact_integer_second(self):
        expected = datetime(2024, 6, 25, 9, 15, tzinfo=IST)
        self.assertEqual(s.parse_timestamp("1719287100"), expected)
        self.assertEqual(s.parse_timestamp(1719287100), expected)

    def test_parse_timestamp_rejects_fractional_seconds_without_truncation(self):
        for value in ("1719287100.5", "1719287100.999", "1719287100.0", 1719287100.5):
            with self.subTest(value=value), self.assertRaises(ValueError):
                s.parse_timestamp(value)

    def test_parse_timestamp_rejects_off_grid_integer_second(self):
        with self.assertRaisesRegex(ValueError, "OFF_GRID_TIMESTAMP"):
            s.parse_timestamp("1719287101")

    def test_parse_timestamp_rejects_nonfinite_and_malformed(self):
        for value in ("nan", "inf", "-inf", "", "not-a-timestamp", None, True):
            with self.subTest(value=value), self.assertRaises(ValueError):
                s.parse_timestamp(value)

    def test_valid_bar(self):
        self.assertEqual(s.validate_bar(bar()), ())

    def test_rejects_zero_negative_nonfinite_and_relationships(self):
        self.assertIn("NONPOSITIVE_OHLC", s.validate_bar(bar(open=0)))
        self.assertIn("NONPOSITIVE_OHLC", s.validate_bar(bar(low=-1)))
        self.assertIn("NONFINITE_OHLC", s.validate_bar(bar(high=math.inf)))
        self.assertIn("INVALID_OHLC_RELATIONSHIP", s.validate_bar(bar(open=102)))

    def test_rejects_bad_volume(self):
        self.assertIn("NEGATIVE_VOLUME", s.validate_bar(bar(volume=-1)))
        self.assertIn("NONFINITE_VOLUME", s.validate_bar(bar(volume=math.nan)))

    def test_rejects_off_grid(self):
        self.assertIn("OFF_GRID_TIMESTAMP", s.validate_bar(bar(timestamp=datetime(2024, 6, 25, 9, 15, 1, tzinfo=IST))))

    def test_duplicate_gate(self):
        report = s.audit_session([row(0), row(0)], DAY)
        self.assertEqual(report["duplicate_timestamps"], 1)
        self.assertFalse(report["structurally_eligible"])

    def test_timestamp_order_gate(self):
        report = s.audit_session([row(1), row(0)], DAY)
        self.assertEqual(report["out_of_order_timestamps"], 1)
        self.assertFalse(report["structurally_eligible"])

    def test_missing_session_and_minute_preserved_in_denominator(self):
        report = s.audit_session([], DAY)
        self.assertEqual(report["structural_session_denominator"], 1)
        self.assertEqual(report["issues"]["MISSING_SESSION"], 1)
        self.assertEqual(report["missing_minutes"], 375)

    def test_incomplete_opening_range_is_ineligible(self):
        rows = [row(i) for i in range(15) if i != 4]
        report = s.audit_session(rows, DAY)
        self.assertFalse(report["opening_range_eligible"])
        self.assertGreater(report["incomplete_five_minute_buckets"], 0)

    def test_complete_bucket_only_after_completion(self):
        bars = [s.bar_from_row(row(i)) for i in range(5)]
        start = bars[0].timestamp
        self.assertFalse(s.complete_five_minute_bucket(bars, start, start + timedelta(minutes=4, seconds=59)))
        self.assertTrue(s.complete_five_minute_bucket(bars, start, start + timedelta(minutes=5)))

    def test_invalid_constituent_rejects_bucket_without_interpolation(self):
        rows = [row(i) for i in range(5)]
        rows[2]["open"] = "102"
        bars = [s.bar_from_row(item) for item in rows]
        self.assertFalse(s.complete_five_minute_bucket(bars, bars[0].timestamp, bars[0].timestamp + timedelta(minutes=5)))

    def test_three_exact_qa_exceptions_are_rejected(self):
        for symbol, values in s.EXPECTED_EXCEPTIONS.items():
            candidate = bar(open=values[0], high=values[1], low=values[2], close=values[3], volume=values[4])
            self.assertIn("INVALID_OHLC_RELATIONSHIP", s.validate_bar(candidate), symbol)

    def test_special_session_cannot_satisfy_frozen_opening_range(self):
        start = datetime.combine(DAY, time(10, 0), IST)
        rows = []
        for i in range(330):
            dt = start + timedelta(minutes=i)
            rows.append({"time": str(int(dt.timestamp())), "open": "100", "high": "101",
                         "low": "99", "close": "100.5", "Volume": "10"})
        report = s.audit_session(rows, DAY)
        self.assertFalse(report["opening_range_eligible"])
        self.assertEqual(report["missing_minutes"], 45)

    def test_no_strategy_or_outcome_primitives(self):
        tree = ast.parse(MODULE.read_text())
        names = {node.name.lower() for node in ast.walk(tree) if isinstance(node, (ast.FunctionDef, ast.ClassDef))}
        for forbidden in ("calculate_orb", "calculate_rvol", "profit", "return_pct", "entry_fill", "exit_fill"):
            self.assertNotIn(forbidden, names)


if __name__ == "__main__":
    unittest.main()
