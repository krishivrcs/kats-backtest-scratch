from __future__ import annotations

import math

import pandas as pd
import pytest
import pyarrow  # noqa: F401 - proves parquet dependency is present

from kats_odpc.core import (
    Candidate,
    SPEC,
    _manage_exit,
    aggregate_5m,
    adverse_fill,
    candidate_sort_key,
    generate_candidate,
    opening_volume_history,
    pullback_flags,
    stop_distance_status,
)
from kats_odpc.portfolio import reconstruct
from kats_odpc.costs import equity_intraday_costs
from kats_odpc.audit import audit_symbol


def minute_frame(day="2025-01-02", price=100.0):
    idx = pd.date_range(f"{day} 09:15", periods=375, freq="1min")
    return pd.DataFrame(
        {"open": price, "high": price, "low": price, "close": price, "volume": 100},
        index=idx,
    )


def set_candle(df, stamp, *, open_, high, low, close, volume=100):
    idx = pd.date_range(stamp, periods=5, freq="1min")
    df.loc[idx, ["open", "high", "low", "close", "volume"]] = [open_, high, low, close, volume]
    df.loc[idx[0], "open"] = open_
    df.loc[idx[-1], "close"] = close
    df.loc[idx[0], "low"] = low
    df.loc[idx[-1], "high"] = high


def executable_long_day():
    df = minute_frame()
    # Opening anchor O=100, H=100.8, opening low=99.95, low VWAP due to most bars near 100.
    for ts in pd.date_range("2025-01-02 09:15", periods=6, freq="5min"):
        set_candle(df, ts, open_=100.0, high=100.12, low=99.95, close=100.05, volume=100)
    df.loc[pd.Timestamp("2025-01-02 09:44"), ["high", "close"]] = [100.8, 100.6]
    # PB25=100.60 and PB50=100.40; qualified pullback gives >=0.20% risk.
    set_candle(df, "2025-01-02 09:45", open_=100.62, high=100.65, low=100.50, close=100.62)
    # Strictly later trigger closes over previous completed candle high.
    set_candle(df, "2025-01-02 09:50", open_=100.62, high=100.75, low=100.58, close=100.70)
    # Next-bar entry.
    set_candle(df, "2025-01-02 09:55", open_=100.70, high=100.78, low=100.66, close=100.72)
    return df


def candidate(symbol="AAA", side="LONG", entry="2025-01-02 10:00", exit_="2025-01-02 10:30", relvol=1.5, drive=0.01, risk=0.5):
    entry_price = 100.0
    stop = 99.5 if side == "LONG" else 100.5
    exit_price = 101.0 if side == "LONG" else 99.0
    return Candidate(
        symbol=symbol, session="2025-01-02", side=side,
        entry_time=pd.Timestamp(entry), raw_entry_open=entry_price, entry_price=entry_price,
        stop_price=stop, target_price=101.0 if side == "LONG" else 99.0,
        one_r_price=100.5 if side == "LONG" else 99.5,
        exit_time=pd.Timestamp(exit_), raw_exit_price=exit_price, exit_price=exit_price,
        exit_reason="TARGET_2R", opening_relative_volume=relvol,
        opening_drive_pct=drive if side == "LONG" else -drive,
        risk_per_share=risk, gross_r=2.0, breakeven_activated=True,
        ambiguity_stop_first=False,
    )


def test_one_minute_to_five_minute_aggregation():
    df = minute_frame().iloc[:10].copy()
    df.loc[:, "open"] = range(10)
    df.loc[:, "high"] = range(1, 11)
    df.loc[:, "low"] = range(10)
    df.loc[:, "close"] = range(10)
    bars = aggregate_5m(df)
    assert len(bars) == 2
    assert bars.iloc[0][["open", "high", "low", "close", "volume", "minute_count"]].tolist() == [0, 5, 0, 4, 500, 5]


def test_volume_uses_only_prior_valid_sessions_and_caps_at_twenty():
    dates = pd.date_range("2025-01-01", periods=25, freq="D")
    table = pd.DataFrame({"valid": True, "opening_volume": range(1, 26)}, index=dates)
    avg, count = opening_volume_history(table, dates[-1])
    assert count == 20
    assert avg == pytest.approx(sum(range(5, 25)) / 20)


def test_volume_requires_fifteen_prior_valid_sessions():
    dates = pd.date_range("2025-01-01", periods=15, freq="D")
    table = pd.DataFrame({"valid": True, "opening_volume": 100}, index=dates)
    avg, count = opening_volume_history(table, dates[-1])
    assert avg is None and count == 14


@pytest.mark.parametrize("low", [100.75, 100.50])
def test_long_pullback_boundaries_are_inclusive(low):
    qualifies, invalid = pullback_flags("LONG", low=low, high=101, vwap=100.4, pb25=100.75, pb50=100.50, opening_extreme=100.0)
    assert qualifies and not invalid


@pytest.mark.parametrize("high", [99.25, 99.50])
def test_short_pullback_boundaries_are_inclusive(high):
    qualifies, invalid = pullback_flags("SHORT", low=99, high=high, vwap=99.6, pb25=99.25, pb50=99.50, opening_extreme=100.0)
    assert qualifies and not invalid


def test_shallow_pullback_waits_but_deep_pullback_invalidates():
    assert pullback_flags("LONG", low=100.8, high=101, vwap=100.4, pb25=100.75, pb50=100.5, opening_extreme=100)[0] is False
    qualifies, invalid = pullback_flags("LONG", low=100.49, high=101, vwap=100.4, pb25=100.75, pb50=100.5, opening_extreme=100)
    assert not qualifies and invalid


def test_long_short_pullback_mirror_symmetry():
    long = pullback_flags("LONG", low=100.6, high=101, vwap=100.4, pb25=100.75, pb50=100.5, opening_extreme=100)
    short = pullback_flags("SHORT", low=99, high=99.4, vwap=99.6, pb25=99.25, pb50=99.5, opening_extreme=100)
    assert long == short == (True, False)


def test_stop_bounds_accept_exact_020_and_080_percent():
    assert stop_distance_status(100, 99.8, "LONG")[0]
    assert stop_distance_status(100, 99.2, "LONG")[0]
    assert not stop_distance_status(100, 99.80001, "LONG")[0]
    assert not stop_distance_status(100, 99.19999, "LONG")[0]


def test_trigger_information_fills_only_at_next_bar_open():
    c, reason = generate_candidate("AAA", pd.Timestamp("2025-01-02"), executable_long_day(), 1.5)
    assert reason == "EXECUTABLE_CANDIDATE"
    assert c is not None
    assert c.entry_time == pd.Timestamp("2025-01-02 09:55")
    assert c.raw_entry_open == pytest.approx(100.70)
    assert c.entry_price > c.raw_entry_open


def test_stop_target_same_minute_is_stop_first():
    df = minute_frame()
    ts = pd.Timestamp("2025-01-02 10:00")
    df.loc[ts, ["high", "low"]] = [102.1, 98.9]
    out = _manage_exit("LONG", df, ts, 100, 99, 102, 101)
    assert out[3] == "STOP_AMBIGUOUS_FIRST"
    assert out[5] is True


def test_breakeven_activates_then_exits_on_later_minute():
    df = minute_frame()
    entry = pd.Timestamp("2025-01-02 10:00")
    df.loc[entry, ["high", "low"]] = [101.1, 100.2]
    df.loc[entry + pd.Timedelta(minutes=1), ["high", "low"]] = [100.5, 99.9]
    out = _manage_exit("LONG", df, entry, 100, 99, 102, 101)
    assert out[3] == "BREAKEVEN"
    assert out[4] is True


def test_forced_exit_is_1510_open():
    df = minute_frame()
    df.loc[pd.Timestamp("2025-01-02 15:10"), "open"] = 100.4
    out = _manage_exit("LONG", df, pd.Timestamp("2025-01-02 14:00"), 100, 99, 102, 101)
    assert out[0] == pd.Timestamp("2025-01-02 15:10")
    assert out[1] == pytest.approx(100.4)
    assert out[3] == "FORCED_1510"


def test_simultaneous_signal_tie_breaking():
    a = candidate("ZZZ", relvol=1.6, drive=0.01)
    b = candidate("AAA", relvol=1.6, drive=0.02)
    c = candidate("BBB", relvol=1.7, drive=0.01)
    assert [x.symbol for x in sorted([a, b, c], key=candidate_sort_key)] == ["BBB", "AAA", "ZZZ"]


def test_only_one_open_portfolio_position_and_one_trade_per_candidate():
    first = candidate("AAA", entry="2025-01-02 10:00", exit_="2025-01-02 10:30")
    overlap = candidate("BBB", entry="2025-01-02 10:05", exit_="2025-01-02 10:20")
    result = reconstruct([overlap, first], 20_000)
    assert result["trade_count"] == 1
    assert result["rejections"]["PORTFOLIO_POSITION_ALREADY_OPEN"] == 1


def test_sizing_has_no_leverage_and_never_exceeds_one_percent_risk():
    result = reconstruct([candidate(risk=0.5)], 15_000)
    trade = result["trades"][0]
    assert trade["notional"] <= 15_000
    assert trade["risk_pct_equity"] <= 0.01 + 1e-12
    assert trade["qty"] == min(math.floor(15_000 / 100), math.floor(150 / 0.5))


def test_capital_constraint_rejects_when_one_share_exceeds_cash():
    c = candidate()
    c.entry_price = 20_001
    c.risk_per_share = 1
    result = reconstruct([c], 20_000)
    assert result["trade_count"] == 0
    assert result["rejections"]["CAPITAL_OR_RISK_CONSTRAINT"] == 1


def test_adverse_slippage_mirrors_long_and_short():
    assert adverse_fill(100, "LONG", True) == pytest.approx(100.05)
    assert adverse_fill(100, "LONG", False) == pytest.approx(99.95)
    assert adverse_fill(100, "SHORT", True) == pytest.approx(99.95)
    assert adverse_fill(100, "SHORT", False) == pytest.approx(100.05)


def test_verified_cost_model_contains_every_required_component():
    costs = equity_intraday_costs(100, 101, 100, "LONG")
    assert set(costs) == {"brokerage", "stt", "exchange_transaction", "sebi", "nse_ipft", "gst", "stamp_duty", "total"}
    assert costs["brokerage"] == pytest.approx(6.03)
    assert costs["stt"] == pytest.approx(2.525)
    assert costs["stamp_duty"] == pytest.approx(0.3)
    assert costs["total"] == pytest.approx(sum(v for k, v in costs.items() if k != "total"))


def test_valid_session_audit_requires_exact_complete_grid(tmp_path):
    df = minute_frame().reset_index().rename(columns={"index": "Date", "open": "Open", "high": "High", "low": "Low", "close": "Close", "volume": "Volume"})
    path = tmp_path / "AAA.parquet"
    df.to_parquet(path, index=False)
    report, sessions = audit_symbol(path, "AAA")
    assert report["valid_session_count"] == 1
    assert bool(sessions.iloc[0].valid)


def test_missing_minute_session_is_invalid(tmp_path):
    df = minute_frame().iloc[:-1].reset_index().rename(columns={"index": "Date", "open": "Open", "high": "High", "low": "Low", "close": "Close", "volume": "Volume"})
    path = tmp_path / "AAA.parquet"
    df.to_parquet(path, index=False)
    report, sessions = audit_symbol(path, "AAA")
    assert report["invalid_session_count"] == 1
    assert not bool(sessions.iloc[0].valid)


def test_duplicate_timestamp_is_reported_and_session_invalid(tmp_path):
    df = minute_frame().reset_index().rename(columns={"index": "Date", "open": "Open", "high": "High", "low": "Low", "close": "Close", "volume": "Volume"})
    df = pd.concat([df, df.iloc[[0]]], ignore_index=True)
    path = tmp_path / "AAA.parquet"
    df.to_parquet(path, index=False)
    report, sessions = audit_symbol(path, "AAA")
    assert report["duplicate_rows"] == 2
    assert report["invalid_session_count"] == 1
    assert not bool(sessions.iloc[0].valid)
