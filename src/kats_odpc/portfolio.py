from __future__ import annotations

import math
from collections import defaultdict

from .core import Candidate, candidate_sort_key
from .costs import equity_intraday_costs


def reconstruct(candidates: list[Candidate], initial_capital: float) -> dict:
    equity = float(initial_capital)
    peak = equity
    max_dd = 0.0
    busy_until = None
    executed: list[dict] = []
    rejected = defaultdict(int)
    for c in sorted(candidates, key=candidate_sort_key):
        if busy_until is not None and c.entry_time <= busy_until:
            rejected["PORTFOLIO_POSITION_ALREADY_OPEN"] += 1
            continue
        risk_budget = 0.01 * equity
        cash_qty = math.floor(equity / c.entry_price)
        risk_qty = math.floor(risk_budget / c.risk_per_share)
        qty = min(cash_qty, risk_qty)
        if qty < 1:
            rejected["CAPITAL_OR_RISK_CONSTRAINT"] += 1
            continue
        if qty * c.entry_price > equity + 1e-9:
            raise AssertionError("Leverage invariant violated")
        if qty * c.risk_per_share > risk_budget + 1e-9:
            raise AssertionError("Risk ceiling invariant violated")
        signed_move = (c.exit_price - c.entry_price) if c.side == "LONG" else (c.entry_price - c.exit_price)
        gross = qty * signed_move
        costs = equity_intraday_costs(c.entry_price, c.exit_price, qty, c.side)
        net = gross - costs["total"]
        before = equity
        equity += net
        peak = max(peak, equity)
        max_dd = max(max_dd, (peak - equity) / peak if peak else 0.0)
        row = c.to_dict()
        row.update({
            "qty": qty,
            "equity_before": before,
            "gross_pnl": gross,
            "costs": costs,
            "net_pnl": net,
            "equity_after": equity,
            "risk_rupees": qty * c.risk_per_share,
            "risk_pct_equity": qty * c.risk_per_share / before,
            "notional": qty * c.entry_price,
        })
        executed.append(row)
        busy_until = c.exit_time

    wins = [t["net_pnl"] for t in executed if t["net_pnl"] > 0]
    losses = [t["net_pnl"] for t in executed if t["net_pnl"] < 0]
    pf = (sum(wins) / abs(sum(losses))) if losses else ("INFINITY" if wins else None)
    return {
        "initial_capital": initial_capital,
        "ending_equity": equity,
        "gross_pnl": sum(t["gross_pnl"] for t in executed),
        "total_costs": sum(t["costs"]["total"] for t in executed),
        "net_pnl": sum(t["net_pnl"] for t in executed),
        "trade_count": len(executed),
        "profit_factor_net": pf,
        "max_drawdown_pct": max_dd,
        "rejections": dict(rejected),
        "trades": executed,
    }
