from datetime import date, datetime, timedelta
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from backtest import Bar, Contract, IST, Signal, aggregate_5m, charges, contract_reference_price, lot_size, parse_option_date, parse_option_ticker, signal_for_day, simulate


def test_option_identity_and_historical_lots():
    contract = parse_option_ticker("RELIANCE31OCT241370CE.NFO")
    assert (contract.symbol, contract.expiry, contract.strike, contract.option_type) == ("RELIANCE", date(2024, 10, 31), 1370.0, "CE")
    assert lot_size("SBIN", date(2024, 10, 15)) == 750
    assert lot_size("DLF", date(2024, 10, 15)) == 825
    assert lot_size("RELIANCE", date(2024, 10, 25)) == 250
    assert lot_size("RELIANCE", date(2024, 10, 28)) == 500


def test_observed_option_date_format_is_explicitly_supported():
    assert parse_option_date("31/10/2024") == date(2024, 10, 31)
    assert parse_option_date("2024-10-31") == date(2024, 10, 31)


def test_reliance_bonus_basis_is_dated_and_deterministic():
    before = Signal("RELIANCE", date(2024, 10, 25), "LONG", datetime(2024, 10, 25, 10, tzinfo=IST), 1350, 2, 0.01)
    after = Signal("RELIANCE", date(2024, 10, 28), "LONG", datetime(2024, 10, 28, 10, tzinfo=IST), 1350, 2, 0.01)
    assert contract_reference_price(before) == 2700
    assert contract_reference_price(after) == 1350


def test_completed_five_minute_aggregation():
    start = datetime(2024, 10, 15, 9, 15, tzinfo=IST)
    bars = [Bar(start + timedelta(minutes=i), 100 + i, 101 + i, 99 + i, 100.5 + i, 10) for i in range(5)]
    out = aggregate_5m(bars)
    assert len(out) == 1
    assert (out[0].open, out[0].high, out[0].low, out[0].close, out[0].volume) == (100, 105, 99, 104.5, 50)


def test_signal_uses_prior_twenty_and_completed_bar_time():
    day = date(2024, 10, 15)
    start = datetime(2024, 10, 15, 9, 15, tzinfo=IST)
    bars = []
    for i in range(20):
        close = 100.0 if i < 19 else 102.0
        bars.append(Bar(start + timedelta(minutes=i), 100, 102 if i == 19 else 101, 99, close, 10))
    signal, reason = signal_for_day("SBIN", day, bars, [80.0] * 20)
    assert reason == "SIGNAL"
    assert signal.decision_time == datetime(2024, 10, 15, 9, 35, tzinfo=IST)


def test_costs_are_positive_and_include_two_brokerage_orders():
    cost = charges(10, 12, 750)
    assert cost["brokerage"] == 40
    assert cost["total"] > 40


def test_one_minute_stop_target_ambiguity_is_stop_first():
    day = date(2024, 10, 15)
    stamp = datetime(2024, 10, 15, 10, 0, 59, tzinfo=IST)
    signal = Signal("SBIN", day, "LONG", stamp.replace(second=0), 800, 2.0, 0.01)
    contract = Contract("SBIN31OCT24800CE.NFO", "SBIN", date(2024, 10, 31), 800, "CE")
    bars = [
        Bar(stamp, 10, 15, 7, 11, 10),
        Bar(stamp.replace(hour=15, minute=15), 11, 11, 11, 11, 10),
    ]
    trade, reason = simulate({"signal": signal, "contract": contract, "bars": bars, "entry_index": 0, "lot_size": 1}, "baseline", 20_000)
    assert reason == "EXECUTED"
    assert trade["exit_reason"] == "AMBIGUOUS_STOP_FIRST"


def test_one_real_sbin_lot_breaches_one_percent_risk_at_typical_premium():
    day = date(2024, 10, 15)
    stamp = datetime(2024, 10, 15, 10, 0, 59, tzinfo=IST)
    signal = Signal("SBIN", day, "LONG", stamp.replace(second=0), 800, 2.0, 0.01)
    contract = Contract("SBIN31OCT24800CE.NFO", "SBIN", date(2024, 10, 31), 800, "CE")
    bars = [Bar(stamp, 10, 10, 10, 10, 10), Bar(stamp.replace(hour=15, minute=15), 10, 10, 10, 10, 10)]
    trade, reason = simulate({"signal": signal, "contract": contract, "bars": bars, "entry_index": 0, "lot_size": 750}, "baseline", 20_000)
    assert trade is None
    assert reason == "RISK_CONSTRAINT"
