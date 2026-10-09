# KATS ORB-RVOL capital-aware contracts — preregistration

Frozen before outcome generation. Base revision: `8fcbae2ca0386661237e98201b10b048fde72095`.

- Signals, chronology, RVOL, ORB, direction, exits, 20% option-premium stop,
  baseline costs/slippage, lot sizes and RELIANCE bonus mapping are unchanged.
- Starting cash is INR 20,000; one shared unlevered portfolio; whole lots only;
  one executed trade per session; risk ceiling is 3% of current equity.
- Use the nearest eligible expiry from the baseline rule (at least five calendar
  days away). For the required CE/PE, order strikes ATM, OTM1, OTM2, OTM3 and
  progressively farther OTM. ATM is the available strike nearest the causal
  underlying reference (lower strike wins an exact tie). CE OTM moves upward;
  PE OTM moves downward.
- Examine candidates in that order and select the first candidate passing every
  gate. Do not inspect its future P&L during selection and do not inspect farther
  strikes after selection.
- Entry is the first sound, positive-volume option minute within two minutes of
  the completed-candle decision. The entry fill is its open plus frozen baseline
  slippage. If OI exists, OI must be positive; absent OI is reported and is not
  fabricated.
- Planned risk uses the unmodified 20% stop, adverse stop-fill slippage and the
  frozen round-trip charge model. Premium outlay plus estimated charges must fit
  cash and planned loss must not exceed 3% of current equity.
- Stop distance must exceed two INR 0.05 ticks and must exceed modeled combined
  entry/exit slippage. Otherwise the contract is mechanically ineligible.
- Exit target remains +40%; minute-bar stop/target ambiguity is stop-first;
  gaps fill at the adverse minute open less slippage; force exit remains 15:15.
- Existing 13 sessions are development/feasibility only. Any later data must be
  separately labeled `UNTOUCHED_EXTENSION` and run unchanged.

