# KATS — ORB cash-equity universe-expansion feasibility

**Document type:** research and feasibility only  
**Frozen source checkpoint:** `e4b6b6347c950a20df2b42051b6e9e9c48734507`  
**Reference hypothesis:** `KATS-ORB-CASH-EQ-LONG-V2`  
**Research branch:** `research/kats-orb-cash-eq-universe-feasibility`  
**Authorization boundary:** no new hypothesis, signal generation, trading engine, P&L, sealed-holdout access, paper trade, or broker order.

## Verdict

`FINAL_VERDICT=EXPANDED_UNIVERSE_WORTH_PREREGISTERING`

Expansion is worth a separate preregistration because the present validation set has only 47 long signals before execution rejection and a lawful minute-data route exists for a materially broader, pre-period liquidity-defined universe. Expansion is **not** yet justified as profitable, adequately sampled, or executable. It introduces cross-sectional ranking, membership, corporate-action, and multiple-testing decisions that cannot be inherited silently from the frozen three-stock V2.

## Strongest case against expansion

1. More symbols do not guarantee 100 executable trades. Signals may be highly correlated on market-wide breakout days, and the one-position-per-session rule collapses simultaneous opportunities.
2. The current 47 long validation signals imply a maximum, not an executed sample. Cash, risk, data, causal-fill, and stop-execution gates can only reduce it.
3. A larger universe multiplies corporate-action and symbol-continuity risks.
4. Selecting symbols after seeing their ORB outcomes would create direct selection bias. This report therefore uses no new-symbol signals or returns.
5. The public one-minute archive is Zerodha-derived research data, not exchange-authoritative. It can support candle diagnostics only after independent NSE daily-volume/price reconciliation.
6. Universe expansion is another hypothesis branch and increases the multiple-testing burden. It cannot be presented as untouched confirmation of the original three-stock result.

## 1. Outcome-independent candidate universe

### Proposed fixed research candidate list

```text
HDFCBANK
ICICIBANK
SBIN
RELIANCE
INFY
AXISBANK
KOTAKBANK
HAL
TATAMOTORS
TCS
DLF
```

This is an 11-stock feasibility universe, not an authorized strategy universe.

### Selection rule

- Take the ten companies in NSE's **July 2024 top-ten stock-futures turnover table**, published in the August 2024 NSE Market Pulse:
  HDFCBANK, ICICIBANK, SBIN, RELIANCE, INFY, AXISBANK, KOTAKBANK, HAL, TATAMOTORS, and TCS.
- Add DLF solely to preserve all three reference symbols from the frozen parent research.
- Freeze the list before computing any new-symbol ORB signal.
- Do not replace a difficult corporate-action name or losing name after outcomes are observed.

This basis existed before the proposed validation period beginning 1 November 2024. It uses official historical liquidity evidence, not future strategy performance. NSE reported that those ten names accounted for 23.3% of stock-futures turnover in July 2024. Derivatives turnover is a strong liquidity-prospect screen, but it is not proof of cash-market spread or depth; cash-segment turnover must be independently verified before admission.

Primary evidence:

- NSE Market Pulse, August 2024, Table 99:  
  https://nsearchives.nseindia.com/web/sites/default/files/inline-files/Market_Pulse_August_2024.pdf
- NSE Market Pulse publication archive:  
  https://www.nseindia.com/static/research/publications-reports-nse-market-pulse
- NSE Nifty 50 methodology and constituent resources:  
  https://www.niftyindices.com/indices/equity/broad-based-indices/nifty--50
- NSE September 2024 index-reconstitution release, effective 30 September 2024:  
  https://www.niftyindices.com/Press_Release/ind_prs23082024.pdf

## 2. Data-source inventory

| Source | Intended use | Coverage/provenance | Admission status |
|---|---|---|---|
| `voletiramu/nse-fno-1min-data` release `v1.0.0` | Primary reproducible one-minute candle research archive | 214 F&O underlyings, 2024-04-01 through 2026-04-30; sourced by publisher from Zerodha Kite API; Unix seconds; OHLCV; research-only, no warranty | Lawful zero-cost research source; not exchange-authoritative |
| NSE CM UDiFF/common bhavcopy and security-wise price-volume archives | Official daily close, volume, turnover, series, trading-day and symbol cross-check | Exchange-primary daily files; CM legacy bhavcopy discontinued from 8 July 2024 in favor of UDiFF | Required for every admitted date/symbol |
| NSE corporate-action archive | Splits, bonuses, demergers, symbol/ISIN continuity | Exchange-primary issuer filings | Required date-effective adjustment/refusal map |
| Upstox V3 historical candle API | Independent one-minute cross-check where authenticated history is available | Official broker API; examples support `NSE_EQ` one-minute candles; coverage depth must be tested without assuming completeness | Optional independent cross-check; not the sole admission source |
| Upstox BOD Instruments JSON/Search API | Current instrument key, exchange segment, tick and trading eligibility | Broker-primary, current-day instrument metadata | Useful for prospective implementation; not sufficient for historical membership |
| NSE historical securities/trading files | Date-effective EQ-series eligibility and cash turnover | Exchange-primary | Required before any new hypothesis is scored |

Source links:

- Public archive README: https://github.com/voletiramu/nse-fno-1min-data
- GitHub release: https://github.com/voletiramu/nse-fno-1min-data/releases/tag/v1.0.0
- NSE daily/monthly capital-market archives: https://www.nseindia.com/resources/historical-reports-capital-market-daily-monthly-archives
- NSE all reports / UDiFF bhavcopy: https://www.nseindia.com/all-reports
- NSE corporate actions: https://www.nseindia.com/companies-listing/corporate-filings-actions
- Upstox V3 historical candles: https://upstox.com/developer/api-documentation/v3/get-historical-candle-data/
- Upstox instrument files: https://upstox.com/developer/api-documentation/instruments/
- Upstox V3 order API: https://upstox.com/developer/api-documentation/v3/place-order/

### Coverage findings

- The already verified archive asset is `stocks_1m_csvs.zip`, 485,923,642 bytes, SHA-256 `20024713c455cc16b5daae91e06991d57a1acfa6a30c77bb7d5a742ee1789ab2`.
- S0 directly verified SBIN, DLF, and RELIANCE.
- The publisher explicitly lists HDFCBANK, ICICIBANK, INFY, TCS, SBIN, AXISBANK, KOTAKBANK, and RELIANCE among included examples.
- HAL and TATAMOTORS require a filename/member and full integrity check at the preregistration data gate. Their presence is not asserted from inference.
- The archive documents Unix seconds parsed as UTC and converted to `Asia/Kolkata`; S0 observed 09:15–15:29 IST interval-start alignment for the reference files. Every added file still requires independent schema, duplication, malformed-bar, missing-minute, session-boundary, and timestamp-semantic verification.
- No adjusted/unadjusted price guarantee is documented. Corporate-action reconciliation must fail closed rather than silently rescale suspicious series.

`DATA_COVERAGE=2024-04-01_TO_2026-04-30_PUBLIC_ARCHIVE; PER_SYMBOL_ADMISSION_NOT_YET_COMPLETE`

## 3. Survivorship and selection-bias controls

The archive is described as an April 2026 F&O-underlying universe. Using all 214 symbols would introduce obvious survivorship and future-membership bias.

Required controls for a future preregistration:

1. Use the fixed 11-name rule above, derived from July 2024 official turnover evidence plus the three parent names.
2. Prove each symbol was NSE EQ-series eligible on each scored date.
3. Maintain date-effective ISIN and symbol continuity.
4. Do not drop delisted, renamed, demerged, suspended, or corporate-action-affected names because their data are inconvenient.
5. Fail closed for dates whose price basis cannot be reconciled.
6. Preserve RELIANCE's date-effective bonus handling.
7. Treat TATAMOTORS/Tata Motors Passenger Vehicles and any demerger/symbol transition as an explicit continuity gate rather than a string rename.
8. Record DLF as a parent-retention exception, not as a member of the July top-ten turnover screen.
9. Freeze the entire membership schedule before signal calculation.
10. Count the expansion as a new tested variant in the KATS multiple-testing lineage.

`SURVIVORSHIP_BIAS_CONTROL=FEASIBLE_IF_FIXED_PRE_PERIOD_LIST_AND_DATE_EFFECTIVE_ELIGIBILITY_ARE_PREREGISTERED`

## 4. Cash affordability and risk feasibility

NSE cash equity permits whole-share quantities, so the one-lot stock-option obstruction does not apply. A ₹20,000 fully funded account can buy at least one share only when the adverse executable entry bound plus estimated charges is within available cash.

However, affordability alone is insufficient:

```text
cash_quantity = floor(
    min(
        available_cash / adverse_entry_bound_with_costs,
        0.03 * current_realized_equity / conservative_per_share_planned_loss
    )
)
```

A future admission gate must reject when:

- quantity is below one;
- one share plus costs exceeds available cash;
- opening-range-low stop distance plus the frozen adverse SL-L band and charges exceeds 3% of current realized equity;
- tick validity, quote freshness, protection acknowledgement, or causal fill status is unresolved.

The 3% ceiling limits intended planned loss; gap, circuit, stop rejection, or non-fill can exceed it. No leverage is required or authorized.

Date-effective NSE cash tick size must be applied. NSE circular NSE/CMTR/62174 introduced a ₹0.01 tick for eligible non-ETF CM securities priced below ₹250, with ₹0.05 otherwise, effective 10 June 2024. Price and series eligibility must be checked by date rather than inferred from today's instrument master.

Primary evidence:

- NSE/CMTR/62174: https://nsearchives.nseindia.com/content/circulars/CMTR62174.pdf
- Upstox V3 place-order documentation supports `NSE_EQ` instruments, product `I`, DAY/IOC validity, MARKET/LIMIT/SL/SL-M order types, and integer-unit quantity. This is API capability evidence, not fill proof.

`CASH_AFFORDABILITY=STRUCTURALLY_FEASIBLE_WHOLE_SHARES; DATE_LEVEL_ADMISSION_REQUIRED`

## 5. Sample-adequacy prospect

Measured parent evidence:

- Three symbols
- Validation long signals before execution rejection: 47
- Validation requirement/preference: 100 executed trades
- Therefore the parent validation set cannot reach 100 executed trades.

Outcome-blind scale illustration only:

```text
47 long signals / 3 symbols × 11 candidate symbols ≈ 172 gross long signals
```

This is **not a forecast** and is not a backtest result. It assumes equal per-symbol signal incidence and ignores correlation, simultaneous-signal collapse, data rejections, cash/risk rejection, causal-entry rejection, and stop-execution uncertainty. Executed trades could remain below 100.

The expansion makes an adequate gross opportunity count plausible enough to justify preregistration, but adequacy is unproven until a frozen engine processes an independently admitted non-holdout dataset.

`SAMPLE_ADEQUACY_PROSPECT=PLAUSIBLE_NOT_ESTABLISHED`

## 6. Daily ranking and shared-portfolio implications

The frozen three-stock ranking cannot be assumed complete for 11 symbols. Expansion requires a new hypothesis to define, before outcomes:

- one fixed date-effective universe;
- how simultaneous long signals are ordered;
- whether only the first signal per session is eligible;
- a deterministic tie-breaker using information available at the completed decision candle;
- handling of an open position when another symbol signals;
- re-entry prohibition;
- stale/unsynchronized quote rejection;
- cash reservation during IOC/partial-fill/protection acknowledgement;
- exact treatment of multiple eligible symbols at identical timestamps.

A reasonable family of outcome-independent inputs could include decision timestamp, frozen RVOL value, and alphabetical symbol, but this report does not authorize or select an ordering. Any chosen ordering changes which trade the shared ₹20,000 portfolio takes and is therefore an economic rule requiring Founder-approved preregistration.

## 7. Corporate-action and integrity workload

Per candidate:

1. Verify archive member, bytes and SHA-256.
2. Audit schema, timezone, interval labeling, duplicates, invalid OHLCV and missing minutes.
3. Cross-check daily OHLCV/turnover against NSE primary files.
4. Build date-effective EQ-series, symbol and ISIN map.
5. Audit splits, bonuses, demergers, mergers and renames.
6. Establish raw-versus-adjusted basis; fail closed on contradiction.
7. Verify pre-period liquidity threshold using NSE cash turnover, not strategy returns.
8. Freeze validation dates and source manifest before signals.

Special attention is required for RELIANCE bonus treatment and TATAMOTORS corporate restructuring/symbol continuity. The other candidates still require full NSE corporate-action checks; absence of a known issue is not evidence of absence.

## 8. Research effort and cost

- Paid data cost: ₹0 under the proposed route.
- GitHub storage: raw archives remain runtime-only and must not be committed.
- Expected bounded engineering/research effort: approximately 1–2 working days for archive admission, NSE daily reconciliation, membership/corporate-action mapping, and preregistration drafting.
- Expected compute: one integrity-only GitHub Actions workflow plus one independent review run; approximately 20–60 runner minutes depending on NSE archive retrieval.
- Main uncertainty: reliable automated retrieval of date-effective NSE daily and corporate-action files, plus HAL/TATAMOTORS archive admission.
- No paid dataset or additional cloud subscription is warranted at this feasibility stage.

`EXPECTED_RESEARCH_COST=₹0_PAID_DATA;_1_TO_2_WORKING_DAYS;_20_TO_60_GITHUB_RUNNER_MINUTES_ESTIMATED`

## 9. Comparison with frozen three-stock V2

| Path | Strength | Main failure mode |
|---|---|---|
| Continue frozen three-stock V2 only | Lowest complexity; S0 compatibility frozen; fewer corporate-action surfaces | At most 47 validation long signals before execution rejection; cannot satisfy 100 executed trades |
| Preregister fixed 11-stock expansion | Plausible gross sample above 100; objective pre-period liquidity basis; cash shares remain fractionally unnecessary | New economic ranking rule, correlated signals, survivorship/corporate-action burden, and another multiple-tested variant |
| Open sealed holdout to compensate | None | Prohibited leakage; destroys the untouched gate |

The expanded path is preferable only as a separately named, frozen hypothesis. It must not rewrite or retrospectively “improve” KATS-ORB-CASH-EQ-LONG-V2.

## Final report

```text
SOURCE_COMMIT=e4b6b6347c950a20df2b42051b6e9e9c48734507
RESEARCH_COMMIT=RECORDED_BY_THIS_DOCUMENT_COMMIT
CANDIDATE_UNIVERSE=HDFCBANK,ICICIBANK,SBIN,RELIANCE,INFY,AXISBANK,KOTAKBANK,HAL,TATAMOTORS,TCS,DLF
UNIVERSE_SELECTION_BASIS=JULY_2024_NSE_TOP_10_STOCK_FUTURES_TURNOVER_PLUS_DLF_PARENT_RETENTION_EXCEPTION
DATA_COVERAGE=PUBLIC_1MIN_2024-04-01_TO_2026-04-30;_PER_SYMBOL_ADMISSION_PENDING
DATA_PROVENANCE=ZERODHA_KITE_DERIVED_PUBLIC_RESEARCH_ARCHIVE_PLUS_NSE_PRIMARY_DAILY_AND_CORPORATE_ACTION_CROSSCHECKS
SURVIVORSHIP_BIAS_CONTROL=FIXED_PRE_VALIDATION_LIST_AND_DATE_EFFECTIVE_EQ_ELIGIBILITY_REQUIRED
CASH_AFFORDABILITY=STRUCTURALLY_FEASIBLE_WHOLE_SHARES;_DATE_LEVEL_CASH_AND_3PCT_RISK_GATE_REQUIRED
SAMPLE_ADEQUACY_PROSPECT=PLAUSIBLE_NOT_ESTABLISHED
EXPECTED_RESEARCH_COST=₹0_PAID_DATA;_1_TO_2_WORKING_DAYS;_20_TO_60_GITHUB_RUNNER_MINUTES_ESTIMATED
FROZEN_V2_CHANGED=NO
VALIDATION_OUTCOMES_READ=NO
HOLDOUT_ACCESSED=NO
PNL_CALCULATED=NO
FINAL_VERDICT=EXPANDED_UNIVERSE_WORTH_PREREGISTERING
NEXT_SINGLE_ACTION=FOUNDER_DECIDES_WHETHER_TO_AUTHORIZE_A_SEPARATE_FIXED_UNIVERSE_PREREGISTRATION_WITH_NO_SIGNAL_OR_PNL_ACCESS
```
