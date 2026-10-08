from __future__ import annotations

import argparse
import json
from collections import Counter, defaultdict
from pathlib import Path

import pandas as pd

from .audit import create_manifest, sha256_file
from .core import SPEC, Candidate, generate_candidate, normalize_1m, opening_volume_history
from .portfolio import reconstruct


SYMBOLS = ["SBIN", "RELIANCE", "HDFCBANK", "ICICIBANK", "INFY", "TCS", "BHARTIARTL", "TATASTEEL", "ITC", "LT"]


def _json_safe(value):
    if isinstance(value, float) and (value == float("inf") or value == float("-inf")):
        return "INFINITY" if value > 0 else "-INFINITY"
    return value


def _portfolio_analytics(portfolio: dict) -> dict:
    trades = portfolio["trades"]
    if not trades:
        return {
            "win_rate": None, "year_by_year": {}, "monthly_positive_share": None,
            "symbol_concentration": {}, "best_trade_contribution": None,
            "best_day_contribution": None,
        }
    table = pd.DataFrame(trades)
    table["entry_time"] = pd.to_datetime(table.entry_time)
    wins = int((table.net_pnl > 0).sum())
    yearly = table.groupby(table.entry_time.dt.year).agg(trades=("net_pnl", "size"), gross=("gross_pnl", "sum"), net=("net_pnl", "sum"))
    monthly = table.groupby(table.entry_time.dt.to_period("M")).net_pnl.sum()
    symbol_abs = table.groupby("symbol").net_pnl.apply(lambda s: float(s.abs().sum()))
    total_abs = float(symbol_abs.sum())
    positive_sum = float(table.loc[table.net_pnl > 0, "net_pnl"].sum())
    day = table.groupby(table.entry_time.dt.date).net_pnl.sum()
    return {
        "win_rate": wins / len(table),
        "year_by_year": {str(int(idx)): {"trades": int(row.trades), "gross": float(row.gross), "net": float(row.net)} for idx, row in yearly.iterrows()},
        "monthly_positive_share": float((monthly > 0).mean()),
        "symbol_concentration": {k: (float(v) / total_abs if total_abs else None) for k, v in symbol_abs.items()},
        "best_trade_contribution": (float(table.net_pnl.max()) / positive_sum if positive_sum > 0 else None),
        "best_day_contribution": (float(day.max()) / float(day[day > 0].sum()) if bool((day > 0).any()) else None),
    }


def execute(data_dir: Path, output_dir: Path, source_commit: str) -> dict:
    output_dir.mkdir(parents=True, exist_ok=True)
    manifest_path = output_dir / "data_manifest.json"
    manifest = create_manifest(data_dir, SYMBOLS, manifest_path, source_commit)
    manifest_sha = sha256_file(manifest_path)

    candidates: list[Candidate] = []
    diagnostics = Counter()
    symbol_counts = Counter()
    for symbol in SYMBOLS:
        frame = normalize_1m(pd.read_parquet(data_dir / f"{symbol}.parquet"))
        sessions = pd.read_csv(output_dir / "session_audits" / f"{symbol}.csv", parse_dates=["session"]).set_index("session")
        valid_dates = set(sessions.index[sessions.valid])
        session_keys = frame.index.normalize()
        for session_date, day in frame.groupby(session_keys, sort=True):
            if session_date not in valid_dates:
                continue
            avg, history_count = opening_volume_history(sessions, session_date)
            if avg is None or avg <= 0:
                diagnostics["INSUFFICIENT_VOLUME_HISTORY"] += 1
                continue
            current_volume = float(sessions.loc[session_date, "opening_volume"])
            relvol = current_volume / avg
            candidate, reason = generate_candidate(symbol, session_date, day, relvol)
            diagnostics[reason] += 1
            if candidate is not None:
                candidates.append(candidate)
                symbol_counts[symbol] += 1

    candidates = sorted(candidates, key=lambda c: (c.entry_time, -c.opening_relative_volume, -abs(c.opening_drive_pct), c.symbol))
    p15 = reconstruct(candidates, 15_000.0)
    p20 = reconstruct(candidates, 20_000.0)
    r_values = [c.gross_r for c in candidates]
    r_wins = [r for r in r_values if r > 0]
    r_losses = [r for r in r_values if r < 0]
    result = {
        "status": "COMPLETED",
        "experiment": "KATS-ODPC-V0",
        "parameters": SPEC.to_dict(),
        "data_source": manifest["source_repository"],
        "data_range": {
            "earliest": min(x["earliest_timestamp"] for x in manifest["symbols"]),
            "latest": max(x["latest_timestamp"] for x in manifest["symbols"]),
        },
        "data_manifest_sha256": manifest_sha,
        "symbol_file_sha256s": {x["symbol"]: x["sha256"] for x in manifest["symbols"]},
        "schema_status": "PASS" if all(x["row_count"] > 0 for x in manifest["symbols"]) else "FAIL",
        "session_integrity": {x["symbol"]: {"valid": x["valid_session_count"], "invalid": x["invalid_session_count"], "corporate_action_suspects": x["corporate_action_suspects"]} for x in manifest["symbols"]},
        "canonical_signal_count": int(sum(diagnostics.get(k, 0) for k in {
            "EXECUTABLE_CANDIDATE", "NONPOSITIVE_STRUCTURAL_RISK",
            "STOP_TOO_TIGHT", "STOP_TOO_WIDE", "MISSING_NEXT_ENTRY_BAR",
        })),
        "canonical_executable_trades": len(candidates),
        "diagnostics": dict(diagnostics),
        "candidate_symbol_counts": dict(symbol_counts),
        "r_metrics": {
            "win_rate": (len(r_wins) / len(r_values) if r_values else None),
            "expectancy_r": (sum(r_values) / len(r_values) if r_values else None),
            "avg_win_r": (sum(r_wins) / len(r_wins) if r_wins else None),
            "avg_loss_r": (sum(r_losses) / len(r_losses) if r_losses else None),
            "long_trades": sum(c.side == "LONG" for c in candidates),
            "short_trades": sum(c.side == "SHORT" for c in candidates),
        },
        "breakeven_management": "SUPPORTED_1MIN_CONSERVATIVE_WITHIN_MINUTE",
        "cost_model": {
            "broker": "Zerodha equity intraday schedule observed 2026-10-08",
            "brokerage": "0.03% or INR 20 per executed order, whichever lower",
            "stt_sell": 0.00025,
            "nse_transaction": 0.0000307,
            "sebi": 0.000001,
            "gst_on_brokerage_exchange_sebi_ipft": 0.18,
            "stamp_buy": 0.00003,
            "slippage_bps_each_side": SPEC.slippage_bps_per_side,
            "rounding_limitation": "sub-paise continuous components; broker contract-note rounding excluded",
        },
        "portfolio_15000": p15,
        "portfolio_20000": p20,
        "analytics_15000": _portfolio_analytics(p15),
        "analytics_20000": _portfolio_analytics(p20),
        "limitations": [
            "Discovery-grade public data, not exchange-authoritative.",
            "Naive timestamps interpreted as Asia/Kolkata local exchange time.",
            "Corporate-action gaps >=15% are reported and excluded, not adjusted.",
            "Five-basis-point adverse slippage is an explicit pre-outcome assumption.",
            "Within-one-minute sequencing ambiguity is resolved stop-first.",
            "Broker contract-note component rounding is not replicated.",
            "Current 2026 cost rates are applied uniformly across the 2018-2025 discovery period.",
            "Maximum drawdown is calculated on closed-trade equity, not intratrade mark-to-market equity.",
        ],
    }
    (output_dir / "candidates.json").write_text(json.dumps([c.to_dict() for c in candidates], indent=2) + "\n", encoding="utf-8")
    (output_dir / "results.json").write_text(json.dumps(result, indent=2, sort_keys=True, default=_json_safe) + "\n", encoding="utf-8")
    pd.DataFrame(p15["trades"]).to_csv(output_dir / "trades_15000.csv", index=False)
    pd.DataFrame(p20["trades"]).to_csv(output_dir / "trades_20000.csv", index=False)
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--data-dir", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--source-commit", required=True)
    args = parser.parse_args()
    result = execute(args.data_dir, args.output_dir, args.source_commit)
    print(json.dumps({
        "status": result["status"],
        "manifest": result["data_manifest_sha256"],
        "candidates": result["canonical_executable_trades"],
        "p15_net": result["portfolio_15000"]["net_pnl"],
        "p20_net": result["portfolio_20000"]["net_pnl"],
    }, indent=2))


if __name__ == "__main__":
    main()
