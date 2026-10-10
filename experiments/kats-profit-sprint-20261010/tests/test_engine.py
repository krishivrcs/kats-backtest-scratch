import math
import sys
import unittest
from datetime import date, datetime, time, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from engine import (IST, Candidate, FiveBar, MinuteBar, aggregate_five, bar_issues,
                    ema5, fill_entry, fill_exit, parse_timestamp, run_portfolio,
                    session_issues, side_costs, simulate_exit, size_position,
                    tick_down, tick_up)


def minute(day=date(2024, 4, 2), i=0, price=100.0):
    stamp = datetime.combine(day, time(9, 15), IST) + timedelta(minutes=i)
    return MinuteBar(stamp, price, price + 1, price - 1, price + 0.2, 1000)


def full_session(day=date(2024, 4, 2), price=100.0):
    return [minute(day, i, price) for i in range(375)]


class EngineTests(unittest.TestCase):
    def test_exact_integer_timestamp(self):
        valid = int(datetime(2024, 4, 2, 3, 45, tzinfo=__import__('datetime').timezone.utc).timestamp())
        self.assertEqual(parse_timestamp(str(valid)).time(), time(9, 15))
        for bad in (f"{valid}.5", "nan", "abc", str(valid + 1)):
            with self.assertRaises(ValueError):
                parse_timestamp(bad)

    def test_invalid_ohlc_and_volume(self):
        bar = MinuteBar(minute().timestamp, 100, 99, 98, 100, -1)
        self.assertIn("INVALID_OHLC_RELATIONSHIP", bar_issues(bar))
        self.assertIn("NEGATIVE_VOLUME", bar_issues(bar))
        nonfinite = MinuteBar(minute().timestamp, math.nan, 101, 99, 100, math.inf)
        self.assertIn("NONFINITE_OHLC", bar_issues(nonfinite))
        self.assertIn("NONFINITE_VOLUME", bar_issues(nonfinite))

    def test_complete_session_and_five_minute_aggregation(self):
        bars = full_session()
        self.assertEqual(session_issues(bars), ())
        five = aggregate_five(bars)
        self.assertEqual(len(five), 75)
        self.assertEqual(five[0].volume, 5000)

    def test_missing_minute_fails_closed(self):
        bars = full_session()
        del bars[3]
        self.assertTrue(session_issues(bars))
        with self.assertRaises(ValueError):
            aggregate_five(bars)

    def test_duplicate_and_out_of_order_fail(self):
        bars = full_session()
        bars.insert(2, bars[1])
        self.assertTrue(any(x.startswith("DUPLICATE") for x in session_issues(bars)))
        swapped = full_session()
        swapped[1], swapped[2] = swapped[2], swapped[1]
        self.assertTrue(session_issues(swapped, out_of_order=1))

    def test_ema_is_causal_session_local(self):
        start = datetime(2024, 4, 2, 9, 15, tzinfo=IST)
        bars = [FiveBar(start + timedelta(minutes=5*i), x, x, x, x, 1) for i, x in enumerate((10, 13, 16))]
        self.assertEqual(ema5(bars), [10, 11, 12.666666666666668])

    def test_tick_rounding_is_adverse(self):
        self.assertEqual(tick_up(100.001), 100.05)
        self.assertEqual(tick_down(99.999), 99.95)
        self.assertGreaterEqual(fill_entry(100, 5), 100.05)
        self.assertLessEqual(fill_exit(100, 5), 99.95)

    def test_costs_have_all_statutory_components(self):
        cost = side_costs(10_000, buy=False, day=date(2025, 4, 1))
        self.assertGreater(cost["brokerage"], 0)
        self.assertGreater(cost["stt"], 0)
        self.assertAlmostEqual(cost["total"], sum(v for k, v in cost.items() if k != "total"))

    def test_sizing_respects_cash_and_one_percent_all_in_risk(self):
        day = date(2024, 4, 2)
        c = Candidate(day, "SBIN", 2, .01, datetime.combine(day,time(10),IST), datetime.combine(day,time(10,5),IST), datetime.combine(day,time(10,10),IST), datetime.combine(day,time(10,15),IST), 100, 98)
        qty, entry, _, planned = size_position(20_000, c, 5)
        self.assertGreater(qty, 0)
        self.assertLessEqual(planned, 200)
        self.assertLessEqual(qty * entry + side_costs(qty * entry, buy=True, day=day)["total"], 20_000)

    def test_stop_target_ambiguity_is_stop_first(self):
        day = date(2024, 4, 2)
        stamp = datetime.combine(day, time(10,15), IST)
        c = Candidate(day,"SBIN",2,.01,stamp,stamp,stamp,stamp,100,99)
        bars = [MinuteBar(stamp,100,103,98,101,1)]
        _, _, reason, _ = simulate_exit(c,bars,100,5)
        self.assertEqual(reason,"AMBIGUOUS_STOP_FIRST")

    def test_gap_through_stop_uses_gap_open(self):
        day = date(2024, 4, 2)
        stamp = datetime.combine(day, time(10,15), IST)
        c = Candidate(day,"SBIN",2,.01,stamp,stamp,stamp,stamp,100,99)
        bars = [MinuteBar(stamp,98,99,97,98,1)]
        _, exit_price, reason, _ = simulate_exit(c,bars,100,5)
        self.assertEqual(reason,"STOP_GAP")
        self.assertLess(exit_price,99)

    def test_time_exit(self):
        day = date(2024, 4, 2)
        entry = datetime.combine(day, time(10), IST)
        exit_stamp = datetime.combine(day,time(15,10),IST)
        c = Candidate(day,"SBIN",2,.01,entry,entry,entry,entry,100,90)
        bars = [MinuteBar(exit_stamp,101,101,101,101,1)]
        _, _, reason, _ = simulate_exit(c,bars,100,5)
        self.assertEqual(reason,"TIME_15_10")

    def test_one_position_per_day(self):
        day=date(2024,4,2); stamp=datetime.combine(day,time(10),IST)
        c1=Candidate(day,"SBIN",2,.01,stamp,stamp,stamp,stamp,100,99)
        c2=Candidate(day,"TCS",1.8,.01,stamp,stamp,stamp,stamp,100,99)
        session=full_session(day,100)
        # force an immediate target for the chosen candidate
        idx=(10*60-9*60-15)
        session[idx]=MinuteBar(stamp,100,103,100,102,1000)
        data={s:{} for s in ("AXISBANK","DLF","HAL","ICICIBANK","INFY","KOTAKBANK","SBIN","TCS")}
        data["SBIN"][day]=session; data["TCS"][day]=session
        trades,rejects=run_portfolio(data,[c1,c2],5)
        self.assertEqual(len(trades),1)
        self.assertEqual(rejects[0]["reason"],"PORTFOLIO_OCCUPIED")


if __name__ == "__main__":
    unittest.main()

