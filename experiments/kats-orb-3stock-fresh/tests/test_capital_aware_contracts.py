from datetime import date, datetime, timedelta
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from backtest import IST, Bar, Contract, Signal, contract_reference_price, lot_size
from capital_aware_contracts import (
    CandidateData, evaluate_candidate, first_entry, metrics, select_contract,
    simulate_selected, strike_ladder,
)


DAY = date(2024, 10, 15)
STAMP = datetime(2024, 10, 15, 10, 0, 59, tzinfo=IST)


def signal(direction="LONG", symbol="SBIN", price=800):
    return Signal(symbol, DAY, direction, STAMP.replace(second=0), price, 2.0, 0.01)


def candidate(strike, option_type="CE", price=2.0, volume=100, oi=None, symbol="SBIN", later_low=None):
    ticker = f"{symbol}31OCT24{int(strike)}{option_type}.NFO"
    contract = Contract(ticker, symbol, date(2024, 10, 31), strike, option_type)
    first = Bar(STAMP, price, price + .2, price - .2, price, volume)
    later = Bar(STAMP + timedelta(minutes=1), price, price + .4,
                price if later_low is None else later_low, price, volume)
    forced = Bar(STAMP.replace(hour=15, minute=15), price, price, price, price, volume)
    return CandidateData(contract, [first, later, forced], {STAMP.isoformat(): oi})


def test_atm_then_directional_otm_ladder_ordering():
    ce = [candidate(x) for x in (780, 790, 800, 810, 820)]
    assert [(label, c.contract.strike) for label, c in strike_ladder(ce, signal())] == [
        ("ATM", 800), ("OTM1", 810), ("OTM2", 820)]
    pe = [candidate(x, "PE") for x in (780, 790, 800, 810, 820)]
    assert [(label, c.contract.strike) for label, c in strike_ladder(pe, signal("SHORT"))] == [
        ("ATM", 800), ("OTM1", 790), ("OTM2", 780)]


def test_first_eligible_is_selected_and_farther_contract_not_examined():
    candidates = [candidate(800, price=20), candidate(810, price=2), candidate(820, price=1.5)]
    rows, selected, _ = select_contract(signal(), candidates, 20_000)
    assert [row["moneyness"] for row in rows] == ["ATM", "OTM1"]
    assert selected["contract"].endswith("810CE.NFO")


def test_selection_does_not_depend_on_future_pnl_path():
    first = candidate(800, price=2, later_low=0.1)
    second = candidate(800, price=2, later_low=2.0)
    a = select_contract(signal(), [first], 20_000)[1]
    b = select_contract(signal(), [second], 20_000)[1]
    assert a["contract"] == b["contract"]
    assert a["entry_premium"] == b["entry_premium"]


def test_affordability_and_whole_historical_lot():
    row, _ = evaluate_candidate(signal(), "ATM", candidate(800, price=27), 20_000)
    assert row["lot_size"] == 750
    assert row["premium_outlay"] > 20_000
    assert row["affordable"] is False


def test_dynamic_three_percent_ceiling_changes_eligibility():
    cand = candidate(800, price=2)
    high, _ = evaluate_candidate(signal(), "ATM", cand, 20_000)
    low, _ = evaluate_candidate(signal(), "ATM", cand, 10_000)
    assert high["planned_risk_percent"] < low["planned_risk_percent"]
    assert high["available_cash"] == 20_000 and low["available_cash"] == 10_000


def test_missing_stale_bar_is_rejected_without_forward_search():
    stale = candidate(800, price=2)
    stale.bars[0] = Bar(STAMP - timedelta(minutes=5), 2, 2.2, 1.8, 2, 100)
    stale.bars[1] = Bar(STAMP + timedelta(minutes=3), 2, 2.2, 1.8, 2, 100)
    index, bar = first_entry(stale, signal())
    assert index is None and bar is None
    row, _ = evaluate_candidate(signal(), "ATM", stale, 20_000)
    assert row["rejection_reason"] == "MISSING_OR_STALE_ENTRY_BAR"


def test_liquidity_requires_positive_oi_when_oi_is_present():
    row, _ = evaluate_candidate(signal(), "ATM", candidate(800, price=2, oi=0), 20_000)
    assert row["liquidity_eligible"] is False
    assert "LIQUIDITY" in row["rejection_reason"]
    absent, _ = evaluate_candidate(signal(), "ATM", candidate(800, price=2, oi=None), 20_000)
    assert absent["liquidity_eligible"] is True


def test_frozen_twenty_percent_stop_and_tick_sanity():
    row, _ = evaluate_candidate(signal(), "ATM", candidate(800, price=2), 20_000)
    assert abs(row["stop_price"] / row["entry_premium"] - .8) < 1e-12
    assert abs(row["stop_distance_ticks"] - row["stop_distance_points"] / .05) < 1e-12
    tiny, _ = evaluate_candidate(signal(), "ATM", candidate(800, price=.20), 20_000)
    assert tiny["stop_executable"] is False


def test_planned_loss_includes_slippage_and_all_costs():
    row, _ = evaluate_candidate(signal(), "ATM", candidate(800, price=2), 20_000)
    assert row["entry_premium"] > 2
    assert row["estimated_costs"] > 40
    assert row["planned_total_loss"] > row["option_risk_rupees"]


def test_gap_through_stop_uses_adverse_open_not_stop_price():
    cand = candidate(800, price=2)
    row, opp = evaluate_candidate(signal(), "ATM", cand, 20_000)
    cand.bars[1] = Bar(STAMP + timedelta(minutes=1), .5, .6, .4, .5, 100)
    trade, reason = simulate_selected(row, opp)
    assert reason == "EXECUTED"
    assert trade["exit_reason"] == "STOP_GAP"
    assert trade["exit_price"] < .5


def test_lot_sizes_and_reliance_bonus_mapping_regression():
    assert lot_size("SBIN", DAY) == 750
    assert lot_size("DLF", DAY) == 825
    assert lot_size("RELIANCE", DAY) == 250
    rel = signal(symbol="RELIANCE", price=1356)
    assert contract_reference_price(rel) == 2712


def test_shared_portfolio_metrics_compound_realized_net_only():
    trades = [{"net_pnl": -100.0, "gross_pnl": -50.0, "total_charges": 50.0},
              {"net_pnl": 200.0, "gross_pnl": 250.0, "total_charges": 50.0}]
    result = metrics(trades)
    assert result["ending_equity"] == 20_100
    assert result["max_drawdown"] == 100

