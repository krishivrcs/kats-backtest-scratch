from __future__ import annotations


def equity_intraday_costs(entry_price: float, exit_price: float, qty: int, side: str) -> dict[str, float]:
    """Verified Zerodha/NSE cash-intraday schedule observed 2026-10-08.

    Components are retained at sub-paise precision rather than applying broker
    contract-note rounding. Slippage is already embedded in simulated fills.
    """
    entry_turnover = entry_price * qty
    exit_turnover = exit_price * qty
    total_turnover = entry_turnover + exit_turnover
    buy_turnover = entry_turnover if side == "LONG" else exit_turnover
    sell_turnover = exit_turnover if side == "LONG" else entry_turnover
    brokerage = min(20.0, 0.0003 * entry_turnover) + min(20.0, 0.0003 * exit_turnover)
    stt = 0.00025 * sell_turnover
    exchange = 0.0000307 * total_turnover
    sebi = 0.000001 * total_turnover
    ipft = 0.000000001 * total_turnover
    gst = 0.18 * (brokerage + exchange + sebi + ipft)
    stamp = 0.00003 * buy_turnover
    total = brokerage + stt + exchange + sebi + ipft + gst + stamp
    return {
        "brokerage": brokerage,
        "stt": stt,
        "exchange_transaction": exchange,
        "sebi": sebi,
        "nse_ipft": ipft,
        "gst": gst,
        "stamp_duty": stamp,
        "total": total,
    }
