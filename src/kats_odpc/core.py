from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import time
from typing import Literal

import numpy as np
import pandas as pd


SIDE = Literal["LONG", "SHORT"]


@dataclass(frozen=True)
class FrozenSpec:
    drive_threshold: float = 0.006
    relative_volume_threshold: float = 1.25
    volume_lookback: int = 20
    minimum_volume_history: int = 15
    pullback_min: float = 0.25
    pullback_max: float = 0.50
    stop_min_pct: float = 0.002
    stop_max_pct: float = 0.008
    target_r: float = 2.0
    breakeven_r: float = 1.0
    earliest_entry: str = "09:50"
    latest_entry: str = "13:30"
    forced_exit: str = "15:10"
    opening_start: str = "09:15"
    opening_end_exclusive: str = "09:45"
    slippage_bps_per_side: float = 5.0

    def to_dict(self) -> dict:
        return asdict(self)


SPEC = FrozenSpec()


@dataclass
class Candidate:
    symbol: str
    session: str
    side: SIDE
    entry_time: pd.Timestamp
    raw_entry_open: float
    entry_price: float
    stop_price: float
    target_price: float
    one_r_price: float
    exit_time: pd.Timestamp
    raw_exit_price: float
    exit_price: float
    exit_reason: str
    opening_relative_volume: float
    opening_drive_pct: float
    risk_per_share: float
    gross_r: float
    breakeven_activated: bool
    ambiguity_stop_first: bool

    def to_dict(self) -> dict:
        data = asdict(self)
        data["entry_time"] = self.entry_time.isoformat()
        data["exit_time"] = self.exit_time.isoformat()
        return data


def normalize_1m(frame: pd.DataFrame) -> pd.DataFrame:
    mapping = {c.lower(): c for c in frame.columns}
    needed = {k: mapping.get(k) for k in ("date", "open", "high", "low", "close", "volume")}
    if any(v is None for v in needed.values()):
        raise ValueError(f"Missing required columns: {needed}")
    out = frame[[needed[k] for k in needed]].rename(columns={needed[k]: k for k in needed}).copy()
    out["date"] = pd.to_datetime(out["date"], errors="raise")
    if out["date"].dt.tz is not None:
        out["date"] = out["date"].dt.tz_convert("Asia/Kolkata").dt.tz_localize(None)
    out = out.sort_values("date", kind="mergesort").set_index("date")
    return out


def aggregate_5m(one_minute: pd.DataFrame) -> pd.DataFrame:
    """Aggregate minute-start bars into right-exclusive five-minute candles."""
    if not isinstance(one_minute.index, pd.DatetimeIndex):
        one_minute = normalize_1m(one_minute)
    bars = one_minute.resample("5min", label="left", closed="left").agg(
        open=("open", "first"),
        high=("high", "max"),
        low=("low", "min"),
        close=("close", "last"),
        volume=("volume", "sum"),
        minute_count=("close", "count"),
    )
    bars = bars[bars["minute_count"] > 0].copy()
    typical = (one_minute["high"] + one_minute["low"] + one_minute["close"]) / 3.0
    pv = typical * one_minute["volume"]
    grouped_pv = pv.resample("5min", label="left", closed="left").sum()
    grouped_v = one_minute["volume"].resample("5min", label="left", closed="left").sum()
    bars["pv"] = grouped_pv.reindex(bars.index)
    bars["vwap"] = bars["pv"].cumsum() / grouped_v.reindex(bars.index).cumsum().replace(0, np.nan)
    return bars


def adverse_fill(raw_price: float, side: SIDE, is_entry: bool, bps: float = SPEC.slippage_bps_per_side) -> float:
    rate = bps / 10_000.0
    if (side == "LONG" and is_entry) or (side == "SHORT" and not is_entry):
        return raw_price * (1.0 + rate)
    return raw_price * (1.0 - rate)


def opening_volume_history(session_summaries: pd.DataFrame, current_date: pd.Timestamp) -> tuple[float | None, int]:
    prior = session_summaries[
        (session_summaries.index < current_date) & session_summaries["valid"]
    ].tail(SPEC.volume_lookback)
    if len(prior) < SPEC.minimum_volume_history:
        return None, len(prior)
    return float(prior["opening_volume"].mean()), len(prior)


def pullback_flags(
    side: SIDE,
    *,
    low: float,
    high: float,
    vwap: float,
    pb25: float,
    pb50: float,
    opening_extreme: float,
) -> tuple[bool, bool]:
    if side == "LONG":
        invalid = low < pb50 or low <= vwap or low <= opening_extreme
        qualifies = low <= pb25 and low >= pb50 and low > vwap and low > opening_extreme
    else:
        invalid = high > pb50 or high >= vwap or high >= opening_extreme
        qualifies = high >= pb25 and high <= pb50 and high < vwap and high < opening_extreme
    return qualifies, invalid


def stop_distance_status(entry: float, stop: float, side: SIDE) -> tuple[bool, str, float]:
    risk = (entry - stop) if side == "LONG" else (stop - entry)
    if risk <= 0:
        return False, "NONPOSITIVE_STRUCTURAL_RISK", risk
    risk_pct = risk / entry
    if risk_pct < SPEC.stop_min_pct:
        return False, "STOP_TOO_TIGHT", risk
    if risk_pct > SPEC.stop_max_pct:
        return False, "STOP_TOO_WIDE", risk
    return True, "STOP_ACCEPTED", risk


def _time(text: str) -> time:
    return time.fromisoformat(text)


def _manage_exit(
    side: SIDE,
    one_minute: pd.DataFrame,
    entry_time: pd.Timestamp,
    entry_price: float,
    stop: float,
    target: float,
    one_r: float,
) -> tuple[pd.Timestamp, float, float, str, bool, bool]:
    forced = entry_time.normalize() + pd.Timedelta(hours=15, minutes=10)
    path = one_minute[(one_minute.index >= entry_time) & (one_minute.index < forced)]
    active_stop = stop
    moved = False
    ambiguous = False
    for ts, bar in path.iterrows():
        if side == "LONG":
            stop_hit = float(bar.low) <= active_stop
            target_hit = float(bar.high) >= target
            if stop_hit and target_hit:
                ambiguous = True
                raw = active_stop
                return ts, raw, adverse_fill(raw, side, False), "STOP_AMBIGUOUS_FIRST", moved, ambiguous
            if stop_hit:
                raw = active_stop
                return ts, raw, adverse_fill(raw, side, False), "BREAKEVEN" if moved else "STOP", moved, ambiguous
            if target_hit:
                raw = target
                return ts, raw, adverse_fill(raw, side, False), "TARGET_2R", moved, ambiguous
            if not moved and float(bar.high) >= one_r:
                if float(bar.low) <= entry_price:
                    ambiguous = True
                    raw = entry_price
                    return ts, raw, adverse_fill(raw, side, False), "BREAKEVEN_AMBIGUOUS_FIRST", True, ambiguous
                active_stop = entry_price
                moved = True
        else:
            stop_hit = float(bar.high) >= active_stop
            target_hit = float(bar.low) <= target
            if stop_hit and target_hit:
                ambiguous = True
                raw = active_stop
                return ts, raw, adverse_fill(raw, side, False), "STOP_AMBIGUOUS_FIRST", moved, ambiguous
            if stop_hit:
                raw = active_stop
                return ts, raw, adverse_fill(raw, side, False), "BREAKEVEN" if moved else "STOP", moved, ambiguous
            if target_hit:
                raw = target
                return ts, raw, adverse_fill(raw, side, False), "TARGET_2R", moved, ambiguous
            if not moved and float(bar.low) <= one_r:
                if float(bar.high) >= entry_price:
                    ambiguous = True
                    raw = entry_price
                    return ts, raw, adverse_fill(raw, side, False), "BREAKEVEN_AMBIGUOUS_FIRST", True, ambiguous
                active_stop = entry_price
                moved = True
    if forced not in one_minute.index:
        raise ValueError(f"Missing forced-exit minute {forced}")
    raw = float(one_minute.loc[forced, "open"])
    return forced, raw, adverse_fill(raw, side, False), "FORCED_1510", moved, ambiguous


def generate_candidate(
    symbol: str,
    session_date: pd.Timestamp,
    one_minute: pd.DataFrame,
    opening_relative_volume: float,
) -> tuple[Candidate | None, str]:
    bars = aggregate_5m(one_minute)
    opening = bars.between_time("09:15", "09:40")
    if len(opening) != 6 or not bool((opening["minute_count"] == 5).all()):
        return None, "INVALID_OPENING_WINDOW"
    o = float(opening.iloc[0].open)
    h = float(opening.high.max())
    l = float(opening.low.min())
    long_pct = h / o - 1.0
    short_pct = l / o - 1.0
    long_ok = long_pct >= SPEC.drive_threshold
    short_ok = short_pct <= -SPEC.drive_threshold
    if long_ok and short_ok:
        return None, "AMBIGUOUS_BIDIRECTIONAL_OPENING_DRIVE"
    if not long_ok and not short_ok:
        return None, "NO_OPENING_DRIVE"
    if opening_relative_volume < SPEC.relative_volume_threshold:
        return None, "RELATIVE_VOLUME_FILTER"

    side: SIDE = "LONG" if long_ok else "SHORT"
    drive_pct = long_pct if long_ok else short_pct
    drive = (h - o) if side == "LONG" else (o - l)
    pb25 = (h - 0.25 * drive) if side == "LONG" else (l + 0.25 * drive)
    pb50 = (h - 0.50 * drive) if side == "LONG" else (l + 0.50 * drive)
    opening_extreme = l if side == "LONG" else h

    post = bars.between_time("09:45", "15:05")
    qualified_at: pd.Timestamp | None = None
    swing: float | None = None
    for i, (ts, bar) in enumerate(post.iterrows()):
        qualifies, invalid = pullback_flags(
            side,
            low=float(bar.low),
            high=float(bar.high),
            vwap=float(bar.vwap),
            pb25=pb25,
            pb50=pb50,
            opening_extreme=opening_extreme,
        )
        if invalid:
            return None, "INVALIDATED_BEFORE_ENTRY"
        if qualified_at is None:
            if qualifies:
                qualified_at = ts
                swing = float(bar.low if side == "LONG" else bar.high)
            continue

        swing = min(float(swing), float(bar.low)) if side == "LONG" else max(float(swing), float(bar.high))
        previous = post.iloc[i - 1]
        triggered = (bar.close > previous.high) if side == "LONG" else (bar.close < previous.low)
        if not triggered:
            continue
        entry_time = ts + pd.Timedelta(minutes=5)
        if entry_time.time() < _time(SPEC.earliest_entry):
            continue
        if entry_time.time() > _time(SPEC.latest_entry):
            return None, "NEXT_BAR_AFTER_LATEST_ENTRY"
        if entry_time not in bars.index or int(bars.loc[entry_time, "minute_count"]) != 5:
            return None, "MISSING_NEXT_ENTRY_BAR"
        raw_entry = float(bars.loc[entry_time, "open"])
        entry = adverse_fill(raw_entry, side, True)
        stop = float(swing)
        accepted, stop_reason, risk = stop_distance_status(entry, stop, side)
        if not accepted:
            return None, stop_reason
        target = entry + SPEC.target_r * risk if side == "LONG" else entry - SPEC.target_r * risk
        one_r = entry + risk if side == "LONG" else entry - risk
        exit_time, raw_exit, exit_price, reason, moved, ambiguous = _manage_exit(
            side, one_minute, entry_time, entry, stop, target, one_r
        )
        gross_r = ((exit_price - entry) if side == "LONG" else (entry - exit_price)) / risk
        return Candidate(
            symbol=symbol,
            session=session_date.date().isoformat(),
            side=side,
            entry_time=entry_time,
            raw_entry_open=raw_entry,
            entry_price=entry,
            stop_price=stop,
            target_price=target,
            one_r_price=one_r,
            exit_time=exit_time,
            raw_exit_price=raw_exit,
            exit_price=exit_price,
            exit_reason=reason,
            opening_relative_volume=opening_relative_volume,
            opening_drive_pct=drive_pct,
            risk_per_share=risk,
            gross_r=gross_r,
            breakeven_activated=moved,
            ambiguity_stop_first=ambiguous,
        ), "EXECUTABLE_CANDIDATE"
    return None, "NO_TRIGGER"


def candidate_sort_key(candidate: Candidate) -> tuple:
    return (
        candidate.entry_time,
        -candidate.opening_relative_volume,
        -abs(candidate.opening_drive_pct),
        candidate.symbol,
    )
