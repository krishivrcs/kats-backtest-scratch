from datetime import date, datetime, time, timedelta
from pathlib import Path
import importlib.util
import sys

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("s0_audit", HERE / "audit.py")
module = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = module
spec.loader.exec_module(module)

AuditBar = module.AuditBar
AuditSignal = module.AuditSignal
IST = module.IST


def bars(start, count=5, *, breakout=False):
    result = []
    for i in range(count):
        close = 102.0 if breakout and i == count - 1 else 100.0
        result.append(AuditBar(start + timedelta(minutes=i), 100, 103 if breakout and i == count - 1 else 101, 99, close, 10))
    return result


def opening(day):
    return bars(datetime.combine(day, time(9, 15), IST), 15)


def test_five_valid_consecutive_minutes():
    start = datetime(2024, 6, 3, 9, 30, tzinfo=IST)
    result = module.complete_5m_bucket(bars(start), start)
    assert result is not None
    assert result.volume == 50


def test_missing_constituent_minute_rejected():
    start = datetime(2024, 6, 3, 9, 30, tzinfo=IST)
    sample = bars(start)
    del sample[2]
    assert module.complete_5m_bucket(sample, start) is None


def test_duplicate_timestamp_rejected():
    start = datetime(2024, 6, 3, 9, 30, tzinfo=IST)
    sample = bars(start)
    sample[-1] = sample[-2]
    assert module.complete_5m_bucket(sample, start) is None


def test_invalid_ohlc_rejected():
    start = datetime(2024, 6, 3, 9, 30, tzinfo=IST)
    sample = bars(start)
    sample[2] = AuditBar(sample[2].timestamp, 100, 98, 99, 100, 10)
    assert module.complete_5m_bucket(sample, start) is None


def test_off_grid_timestamp_rejected():
    start = datetime(2024, 6, 3, 9, 30, tzinfo=IST)
    sample = bars(start)
    item = sample[2]
    sample[2] = AuditBar(item.timestamp.replace(second=1), item.open, item.high, item.low, item.close, item.volume)
    assert module.complete_5m_bucket(sample, start) is None


def test_incomplete_opening_range_rejected():
    day = date(2024, 6, 3)
    sample = opening(day)[:-1]
    signal, reason = module.v2_signal_for_day("SBIN", day, sample, [100] * 20)
    assert signal is None
    assert reason == "INVALID_CURRENT_OPENING_SESSION"


def test_missing_prior_twenty_sessions_rejected():
    day = date(2024, 6, 3)
    signal, reason = module.v2_signal_for_day("SBIN", day, opening(day), [100] * 19)
    assert signal is None
    assert reason == "INSUFFICIENT_20_SESSION_HISTORY"


def test_boundary_0930_not_a_signal_decision():
    day = date(2024, 6, 3)
    sample = opening(day)
    sample[-1] = AuditBar(sample[-1].timestamp, 100, 103, 99, 102, 10)
    signal, _ = module.v2_signal_for_day("SBIN", day, sample, [100] * 20)
    assert signal is None


def test_boundary_1200_is_inclusive_but_later_is_not():
    day = date(2024, 6, 3)
    base = opening(day)
    for start_time, expected in ((time(11, 55), time(12, 0)), (time(12, 0), None)):
        sample = base + bars(datetime.combine(day, start_time, IST), 5, breakout=True)
        signal, _ = module.v2_signal_for_day("SBIN", day, sample, [100] * 20)
        assert (signal.decision_time.timetz().replace(tzinfo=None) if signal else None) == expected


def test_chronological_ranking_rule():
    day = date(2024, 6, 3)
    stamp = datetime(2024, 6, 3, 10, 0, tzinfo=IST)
    values = [
        AuditSignal("RELIANCE", day, "LONG", stamp, 2.0, 0.02),
        AuditSignal("DLF", day, "LONG", stamp, 2.0, 0.02),
        AuditSignal("SBIN", day, "LONG", stamp, 2.5, 0.01),
    ]
    values.sort(key=lambda item: (item.decision_time, -item.rvol, -item.breakout_distance, item.symbol))
    assert [item.symbol for item in values] == ["SBIN", "DLF", "RELIANCE"]


def test_legacy_missing_minute_emits_bar_but_v2_rejects():
    root = HERE.parent
    legacy_path = root / "backtest.py"
    legacy = module.load_legacy_module(legacy_path)
    start = datetime(2024, 6, 3, 9, 30, tzinfo=IST)
    sample = bars(start)
    del sample[2]
    legacy_bars = [legacy.Bar(item.timestamp, item.open, item.high, item.low, item.close, item.volume) for item in sample]
    assert len(legacy.aggregate_5m(legacy_bars)) == 1
    assert module.complete_5m_bucket(sample, start) is None


def test_holdout_access_denied():
    try:
        module.assert_signal_access_allowed(date(2025, 11, 1))
    except module.HoldoutAccessError:
        pass
    else:
        raise AssertionError("holdout signal access was not denied")
