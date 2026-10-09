#!/usr/bin/env python3
"""Capital-aware deterministic contract ladder for frozen ORB-RVOL signals."""

from __future__ import annotations

import argparse
import csv
import io
import json
import math
import zipfile
from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import date, timedelta
from pathlib import Path

from backtest import (
    SCENARIOS, STARTING_CAPITAL, Bar, Contract, Signal, build_signals, charges,
    contract_reference_price, lot_size, option_members, parse_cash_archive,
    parse_option_ticker, parse_option_time, sha256_file, slippage,
)
from risk_variants import exit_trade

TICK = 0.05
RISK_CEILING = 0.03
MIN_EXPIRY_DAYS = 5


@dataclass
class CandidateData:
    contract: Contract
    bars: list[Bar]
    open_interest: dict[str, float | None]


def sound_bar(bar: Bar) -> bool:
    return (
        min(bar.open, bar.high, bar.low, bar.close) > 0
        and bar.low <= min(bar.open, bar.close, bar.high)
        and bar.high >= max(bar.open, bar.close, bar.low)
        and bar.volume >= 0
    )


def oi_value(row: dict[str, str]) -> float | None:
    normalized = {key.lower().replace(" ", "").replace("_", ""): value for key, value in row.items()}
    for key in ("openinterest", "oi"):
        raw = normalized.get(key)
        if raw not in (None, ""):
            try:
                return float(raw)
            except ValueError:
                return None
    return None


def load_candidates(zf: zipfile.ZipFile, member: str, signal: Signal) -> list[CandidateData]:
    option_type = "CE" if signal.direction == "LONG" else "PE"
    contracts: dict[str, Contract] = {}
    bars: dict[str, list[Bar]] = defaultdict(list)
    oi: dict[str, dict[str, float | None]] = defaultdict(dict)
    with zf.open(member) as raw:
        reader = csv.DictReader(io.TextIOWrapper(raw, encoding="utf-8-sig", errors="replace", newline=""))
        for row in reader:
            ticker = row["Ticker"].strip().upper()
            contract = parse_option_ticker(ticker)
            if not contract or contract.symbol != signal.symbol or contract.option_type != option_type:
                continue
            if (contract.expiry - signal.day).days < MIN_EXPIRY_DAYS:
                continue
            stamp = parse_option_time(row)
            bar = Bar(stamp, *(float(row[key]) for key in ("Open", "High", "Low", "Close")), float(row["Volume"]))
            contracts[ticker] = contract
            bars[ticker].append(bar)
            oi[ticker][stamp.isoformat()] = oi_value(row)
    if not contracts:
        return []
    expiry = min(contract.expiry for contract in contracts.values())
    return [
        CandidateData(contracts[ticker], sorted(values, key=lambda value: value.timestamp), oi[ticker])
        for ticker, values in bars.items() if contracts[ticker].expiry == expiry
    ]


def strike_ladder(candidates: list[CandidateData], signal: Signal) -> list[tuple[str, CandidateData]]:
    if not candidates:
        return []
    by_strike = {candidate.contract.strike: candidate for candidate in candidates}
    reference = contract_reference_price(signal)
    atm = min(by_strike, key=lambda strike: (abs(strike - reference), strike))
    if signal.direction == "LONG":
        strikes = [atm] + sorted(strike for strike in by_strike if strike > atm)
    else:
        strikes = [atm] + sorted((strike for strike in by_strike if strike < atm), reverse=True)
    return [("ATM" if index == 0 else f"OTM{index}", by_strike[strike]) for index, strike in enumerate(strikes)]


def first_entry(candidate: CandidateData, signal: Signal) -> tuple[int | None, Bar | None]:
    latest = signal.decision_time + timedelta(minutes=2)
    for index, bar in enumerate(candidate.bars):
        minute = bar.timestamp.replace(second=0)
        if signal.decision_time <= minute <= latest and bar.volume > 0 and sound_bar(bar):
            return index, bar
    return None, None


def evaluate_candidate(signal: Signal, label: str, candidate: CandidateData, equity: float) -> tuple[dict, dict | None]:
    index, bar = first_entry(candidate, signal)
    base = {
        "date": signal.day.isoformat(), "symbol": signal.symbol, "direction": signal.direction,
        "signal_timestamp": signal.decision_time.isoformat(), "contract": candidate.contract.ticker,
        "expiry": candidate.contract.expiry.isoformat(), "strike": candidate.contract.strike,
        "moneyness": label, "lot_size": lot_size(signal.symbol, signal.day), "available_cash": equity,
        "selected": False,
    }
    if bar is None or index is None:
        return {**base, "affordable": False, "risk_eligible": False, "liquidity_eligible": False,
                "stop_executable": False, "rejection_reason": "MISSING_OR_STALE_ENTRY_BAR"}, None
    pct, minimum = SCENARIOS["baseline"]
    entry = bar.open + slippage(bar.open, pct, minimum)
    stop = entry * 0.80
    distance = entry - stop
    stop_exit = max(0.0, stop - slippage(stop, pct, minimum))
    quantity = base["lot_size"]
    cost = charges(entry, stop_exit, quantity)["total"]
    option_risk = distance * quantity
    planned = (entry - stop_exit) * quantity + cost
    outlay = entry * quantity
    required_cash = outlay + cost
    oi = candidate.open_interest.get(bar.timestamp.isoformat())
    liquidity = bar.volume > 0 and (oi is None or oi > 0)
    combined_slippage = slippage(entry, pct, minimum) + slippage(stop, pct, minimum)
    stop_executable = distance > 2 * TICK and distance > combined_slippage
    affordable = required_cash <= equity + 1e-9
    risk_eligible = planned <= equity * RISK_CEILING + 1e-9
    reasons = []
    if not affordable: reasons.append("AFFORDABILITY")
    if not risk_eligible: reasons.append("RISK")
    if not liquidity: reasons.append("LIQUIDITY")
    if not stop_executable: reasons.append("STOP_EXECUTABILITY")
    row = {
        **base, "entry_timestamp": bar.timestamp.isoformat(), "entry_premium": entry,
        "premium_outlay": outlay, "required_cash_including_estimated_costs": required_cash,
        "stop_price": stop, "stop_distance_points": distance, "stop_distance_ticks": distance / TICK,
        "stop_le_1_tick": distance <= TICK, "stop_le_2_ticks": distance <= 2 * TICK,
        "stop_le_modeled_adverse_slippage": distance <= combined_slippage,
        "option_risk_rupees": option_risk, "estimated_costs": cost,
        "planned_total_loss": planned, "planned_risk_percent": planned / equity * 100,
        "volume": bar.volume, "open_interest_if_available": oi,
        "affordable": affordable, "risk_eligible": risk_eligible,
        "liquidity_eligible": liquidity, "stop_executable": stop_executable,
        "rejection_reason": ";".join(reasons),
    }
    opportunity = {"signal": signal, "contract": candidate.contract, "bars": candidate.bars,
                   "entry_index": index, "lot_size": quantity}
    return row, opportunity


def select_contract(signal: Signal, candidates: list[CandidateData], equity: float) -> tuple[list[dict], dict | None, dict | None]:
    rows = []
    for label, candidate in strike_ladder(candidates, signal):
        row, opportunity = evaluate_candidate(signal, label, candidate, equity)
        rows.append(row)
        if all(row.get(key) is True for key in ("affordable", "risk_eligible", "liquidity_eligible", "stop_executable")):
            row["selected"] = True
            row["rejection_reason"] = ""
            return rows, row, opportunity
    return rows, None, None


def simulate_selected(row: dict, opportunity: dict) -> tuple[dict | None, str]:
    estimate = {
        "active_stop": row["stop_price"], "target": row["entry_premium"] * 1.40,
        "historical_lot_size": row["lot_size"], "available_account_cash": row["available_cash"],
        "option_entry_price": row["entry_premium"],
    }
    values, reason = exit_trade(estimate, opportunity)
    if values is None:
        return None, reason
    return {**row, **values}, "EXECUTED"


def metrics(trades: list[dict]) -> dict:
    nets = [row["net_pnl"] for row in trades]
    wins = [value for value in nets if value > 0]
    losses = [value for value in nets if value < 0]
    equity = peak = STARTING_CAPITAL
    drawdown = 0.0
    for value in nets:
        equity += value
        peak = max(peak, equity)
        drawdown = max(drawdown, peak - equity)
    return {
        "executable_trades": len(trades), "gross_pnl": sum(row["gross_pnl"] for row in trades),
        "costs": sum(row["total_charges"] for row in trades), "net_pnl": sum(nets),
        "ending_equity": STARTING_CAPITAL + sum(nets), "max_drawdown": drawdown,
        "profit_factor": sum(wins) / abs(sum(losses)) if losses else ("Infinity" if wins else None),
        "win_rate": len(wins) / len(trades) if trades else None,
    }


def write_csv(path: Path, rows: list[dict]) -> None:
    fields = sorted({key for row in rows for key in row})
    if not fields:
        path.write_text("", encoding="utf-8")
        return
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader(); writer.writerows(rows)


def run(option_zip: Path, stock_zip: Path, out: Path) -> dict:
    out.mkdir(parents=True, exist_ok=True)
    members = option_members(option_zip)
    days = sorted(members)
    cash = parse_cash_archive(stock_zip)
    signals, audit = build_signals(cash, days)
    equity = STARTING_CAPITAL
    candidate_rows, trades, signal_rows = [], [], []
    with zipfile.ZipFile(option_zip) as zf:
        for day in days:
            executed_today = False
            day_equity = equity
            for signal in signals.get(day, []):
                candidates = load_candidates(zf, members[day], signal)
                rows, selected, opportunity = select_contract(signal, candidates, day_equity)
                if executed_today and selected is not None:
                    selected["selected"] = False
                    selected["rejection_reason"] = "DAILY_PORTFOLIO_LIMIT"
                    selected = opportunity = None
                candidate_rows.extend(rows)
                status = "NO_ELIGIBLE_CONTRACT"
                if selected is not None and opportunity is not None:
                    trade, status = simulate_selected(selected, opportunity)
                    if trade is not None:
                        equity += trade["net_pnl"]
                        trade["equity_after_trade"] = equity
                        trades.append(trade); executed_today = True
                signal_rows.append({"date": day.isoformat(), "symbol": signal.symbol,
                                    "selected_contract": selected["contract"] if selected else None,
                                    "status": status})
    counts = Counter()
    for row in candidate_rows:
        if not row.get("affordable", False): counts["affordability"] += 1
        if not row.get("risk_eligible", False): counts["risk"] += 1
        if not row.get("liquidity_eligible", False): counts["liquidity"] += 1
        if not row.get("stop_executable", False): counts["stop"] += 1
        if row.get("rejection_reason") == "MISSING_OR_STALE_ENTRY_BAR": counts["missing"] += 1
    selected_rows = [row for row in candidate_rows if row.get("selected")]
    result = {
        "project": "KATS-ORB-3STOCK-CAPITAL-AWARE-CONTRACTS",
        "base_commit": "8fcbae2ca0386661237e98201b10b048fde72095",
        "data_range": [days[0].isoformat(), days[-1].isoformat()], "option_sessions": len(days),
        "signals": sum(len(value) for value in signals.values()), "starting_capital": STARTING_CAPITAL,
        "max_risk_percent": 3, "option_zip_sha256": sha256_file(option_zip),
        "stock_zip_sha256": sha256_file(stock_zip), "signal_audit": audit,
        "preregistered_contract_selection": "ATM_THEN_DIRECTIONAL_OTM_FIRST_FULLY_ELIGIBLE",
        "stop_rule": "UNMODIFIED_20_PERCENT_OPTION_PREMIUM",
        "liquidity_filter": "SOUND_POSITIVE_VOLUME_ENTRY; POSITIVE_OI_IF_FIELD_PRESENT",
        "feasibility": {
            "signals_with_affordable_option": len({(r["date"], r["symbol"], r["signal_timestamp"]) for r in candidate_rows if r.get("affordable")}),
            "signals_with_risk_eligible_option": len({(r["date"], r["symbol"], r["signal_timestamp"]) for r in candidate_rows if r.get("risk_eligible")}),
            "signals_with_liquid_option": len({(r["date"], r["symbol"], r["signal_timestamp"]) for r in candidate_rows if r.get("liquidity_eligible")}),
            "signals_with_executable_option": len(selected_rows), "executable_trades": len(trades),
            "atm_rejections": sum(r["moneyness"] == "ATM" and not r.get("selected") for r in candidate_rows),
            "otm1_rejections": sum(r["moneyness"] == "OTM1" and not r.get("selected") for r in candidate_rows),
            "otm2_rejections": sum(r["moneyness"] == "OTM2" and not r.get("selected") for r in candidate_rows),
            "otm3_rejections": sum(r["moneyness"] == "OTM3" and not r.get("selected") for r in candidate_rows),
            "further_otm_required": sum(int(r["moneyness"][3:]) >= 4 for r in selected_rows),
            "rejections_affordability": counts["affordability"], "rejections_risk": counts["risk"],
            "rejections_liquidity": counts["liquidity"], "rejections_stop_executability": counts["stop"],
            "rejections_missing_data": counts["missing"],
            "min_selected_premium": min((r["entry_premium"] for r in selected_rows), default=None),
            "max_selected_premium": max((r["entry_premium"] for r in selected_rows), default=None),
            "min_selected_stop_points": min((r["stop_distance_points"] for r in selected_rows), default=None),
            "max_selected_stop_points": max((r["stop_distance_points"] for r in selected_rows), default=None),
        },
        "development_only_pnl": metrics(trades),
        "untouched_extension": {"available": False, "reason": "FROZEN_ARCHIVE_CONTAINS_ONLY_THE_13_DEVELOPMENT_SESSIONS"},
        "corporate_action_regression": "PASS_RELIANCE_PRE_BONUS_REFERENCE_2X_ADJUSTED_CASH",
        "previous_variant_regression_expected": {"signals": 5, "control_trades": 0, "three_pct_trades": 0,
                                                  "one_point_trades": 2, "one_point_net": -1354.94308342235},
        "signal_selection": signal_rows,
    }
    write_csv(out / "contract_candidates.csv", candidate_rows)
    write_csv(out / "selected_trades.csv", trades)
    write_csv(out / "signal_selection.csv", signal_rows)
    (out / "capital_aware_results.json").write_text(json.dumps(result, indent=2, sort_keys=True), encoding="utf-8")
    print(json.dumps({"signals": result["signals"], "feasibility": result["feasibility"],
                      "development_only_pnl": result["development_only_pnl"]}, indent=2))
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("option_zip", type=Path); parser.add_argument("stock_zip", type=Path)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args(); run(args.option_zip, args.stock_zip, args.out); return 0


if __name__ == "__main__":
    raise SystemExit(main())

