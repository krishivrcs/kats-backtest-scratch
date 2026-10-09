# KATS ORB-RVOL three-stock risk variants — frozen extension

Parent strategy and data basis: `KATS-ORB-RVOL-3STOCK-FRESH-V1` at commit
`23174e644dd3ef10a4973a6e895bbaceb692b324`.

This extension changes no signal, contract, entry, target, cost, slippage or
session rule.  It evaluates three mutually exclusive portfolio configurations:

- `control_1pct`: original 20% premium stop; planned loss including estimated
  stop slippage and round-trip charges must not exceed 1% of current equity.
- `variant_a_3pct`: original 20% premium stop; identical calculation with a 3%
  ceiling.
- `variant_b_1point`: one whole lot, stop exactly one premium point below the
  actual entry fill, rounded downward to the ₹0.05 tick.  No percentage-risk
  ceiling is applied.  Affordability remains mandatory.

All configurations begin with ₹20,000 cash, use one shared portfolio, allow at
most one executed trade per day, prohibit leverage and overnight holdings, and
reserve estimated round-trip charges when checking affordability.  The parent
target remains 40% above actual entry.  Gap-through-stop execution uses the
adverse candle open plus frozen sell slippage; same-minute stop/target ambiguity
is stop-first.

The main comparison uses the parent's baseline slippage of 0.50% per fill with
a ₹0.05 minimum.  No parameters are selected from outcomes.
