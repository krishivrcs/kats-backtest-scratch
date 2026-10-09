from datetime import date, datetime
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from backtest import Bar, Contract, IST, Signal
from risk_variants import estimated_trade, exit_trade, floor_tick, stop_prices


def opportunity(symbol="SBIN", price=2.0, lot=750, second_open=2.0, second_low=2.0):
    day = date(2024, 10, 15)
    stamp = datetime(2024, 10, 15, 10, 0, 59, tzinfo=IST)
    signal = Signal(symbol, day, "LONG", stamp.replace(second=0), 800, 2.0, 0.01)
    contract = Contract(f"{symbol}31OCT24800CE.NFO", symbol, date(2024, 10, 31), 800, "CE")
    bars = [
        Bar(stamp, price, price + 0.2, price - 0.2, price, 10),
        Bar(stamp.replace(minute=1), second_open, max(second_open, 3), second_low, second_open, 10),
        Bar(stamp.replace(hour=15, minute=15), second_open, second_open, second_open, second_open, 10),
    ]
    return signal, {"signal": signal, "contract": contract, "bars": bars, "entry_index": 0, "lot_size": lot}


def test_control_and_three_percent_use_same_unmodified_stop():
    signal, opp = opportunity(price=2.0, lot=1)
    control = estimated_trade(signal, opp, "control_1pct", 20_000)
    variant = estimated_trade(signal, opp, "variant_a_3pct", 20_000)
    assert control["active_stop"] == variant["active_stop"] == control["original_strategy_stop"]
    assert control["risk_limit_rupees"] == 200
    assert variant["risk_limit_rupees"] == 600


def test_fixed_stop_is_one_point_subject_to_downward_tick_rounding():
    stops = stop_prices(10.123)
    assert stops["variant_b_stop"] == floor_tick(9.123)
    assert 1.0 <= 10.123 - stops["variant_b_stop"] < 1.05


def test_variant_b_does_not_apply_percentage_risk_ceiling():
    signal, opp = opportunity(price=10.0, lot=750)
    estimate = estimated_trade(signal, opp, "variant_b_1point", 20_000)
    assert estimate["risk_limit_rupees"] is None
    assert estimate["risk_eligibility_result"] == "PASS"
    assert estimate["estimated_planned_risk_percent"] > 1


def test_affordability_reserves_estimated_charges():
    signal, opp = opportunity(price=20.0, lot=1)
    estimate = estimated_trade(signal, opp, "variant_b_1point", 20.0)
    assert estimate["required_premium_outlay"] <= 20.1
    assert estimate["required_cash_including_estimated_costs"] > 20.0
    assert estimate["affordability_result"] == "FAIL"


def test_gap_through_stop_fills_at_adverse_open_plus_slippage():
    signal, opp = opportunity(price=10.0, lot=1, second_open=8.0, second_low=7.5)
    estimate = estimated_trade(signal, opp, "variant_b_1point", 20_000)
    trade, reason = exit_trade(estimate, opp)
    assert reason == "EXECUTED"
    assert trade["exit_reason"] == "STOP_GAP"
    assert trade["exit_price"] < 8.0


def test_reliance_corporate_action_mapping_is_retained():
    signal, opp = opportunity(symbol="RELIANCE", price=10.0, lot=250)
    estimate = estimated_trade(signal, opp, "variant_b_1point", 20_000)
    assert estimate["underlying_close"] == 800
    assert estimate["contract_reference_price"] == 1600
