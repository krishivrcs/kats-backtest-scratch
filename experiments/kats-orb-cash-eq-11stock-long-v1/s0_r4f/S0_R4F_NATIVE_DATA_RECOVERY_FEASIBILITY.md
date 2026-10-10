# KATS S0-R4F — Native Historical Data Recovery Feasibility

**Hypothesis:** `KATS-ORB-CASH-EQ-11STOCK-LONG-V1`  
**Source checkpoint:** `bf2ea9189795ca96f0f6b26c13b371b6de3cbdd0`  
**Accepted strict validator:** `98fb16d73eb4c1105c66d15b2da848f489fe96ca`  
**Research date:** 2026-10-10  
**Permitted data horizon:** 2024-04-01 through 2025-10-31 only

## Verdict first

`S0_R4F_NATIVE_SOURCE_IDENTIFIED`

NSE Data & Analytics Limited's **Capital Market Historical Trade Data** is the shortest defensible native-data route. Its official specification supplies every cash-market trade tick with market-session indicator, transaction timestamp, symbol, series, trade price and trade quantity. Those trade records can be aggregated deterministically into contemporaneous one-minute OHLCV without corporate-action back-adjustment.

This identifies a suitable source; it does **not** mean the data have been acquired or admitted. Exact availability for 2024-04-01 through 2025-10-31, the permissible private proprietary-backtesting use, delivery scope, and final price must be confirmed in writing before any purchase. No purchase was made.

The existing adjusted archive cannot be admitted by merely multiplying pre-bonus prices and dividing volumes. Price rounding loses information, volume does not invert exactly, malformed bars remain malformed, and twenty-session RVOL windows crossing a bonus date compare incompatible volume bases.

## Evidence classes

- **Verified official:** public NSE product pages, specifications, tariff and data-use policy.
- **Verified provider documentation:** provider-owned API/product/licensing pages.
- **Measured prior evidence:** frozen S0-R4A findings and the Founder-supplied S0-R4B/D/E context.
- **Unknown:** exact custom quote, precise requested-date entitlement, and any provider behavior not explicitly documented or demonstrated by a source sample.

## 1. Source comparison

| Source | Relevant documented capability | Corporate-action basis | Required coverage | Cost/access | Feasibility decision |
|---|---|---|---|---|---|
| **NSE Data & Analytics — CM Historical Trade Data** | Official [historical-data page](https://www.nseindia.com/static/market-data/eod-historical-data-subscription) and [Historical Order & Trade specification v1.18](https://nsearchives.nseindia.com/web/mediaattachment/2026-05/NSE_Hist_Order_Trade_Data_1.18_20260518122214.pdf) document all cash-market trade ticks, timestamp, symbol, series, trade price and trade quantity. Historical downloads are supplied through an approved downloader/cloud process. | Native executed trades are the source primitive; one-minute bars would be derived by KATS rather than accepted from an adjusted charting series. | Product lineage predates the requested period, but exact 2024-04-01–2025-10-31 availability must be contractually confirmed. | Published 2026 domestic tariff: **₹1,10,000 per annum/site plus taxes** for CM Historical Trade Data. Subscription and relevant agreement required. | **Authoritative candidate identified.** Exact coverage/licence/quote gate remains. Full order-book data is unnecessary for OHLCV and costs far more. |
| **NSE Historical Order & Trade Data** | Adds order events to trades and supports liquidity/execution studies. | Native exchange events. | Expected to cover requested dates subject to subscription confirmation. | Published CM tariff: **₹12,50,000 per annum/site plus taxes**. | Technically strongest, economically disproportionate for the current OHLCV-only admission gate. Not recommended now. |
| **Global Financial Datafeeds (GFDL)** | [GetHistory](https://globaldatafeeds.in/global-datafeeds-apis/global-datafeeds-apis/rest-api-documentation/function-gethistory/) supports minute data and an explicit `AdjustSplits=false`; [coverage page](https://globaldatafeeds.in/global-datafeeds-apis/global-datafeeds-apis/introduction/type-of-data-available/) documents only three calendar months of one-minute NSE CM backfill. NSE lists GFDL among authorized real-time data vendors. | Potentially native/unadjusted when `AdjustSplits=false`, but bonus handling and native volume for an older bulk archive have not been demonstrated. | Documented API retention is insufficient for April 2024–October 2025. Older one-off availability is `UNKNOWN`. | Quote-only. Terms allow single-subscriber charting/analysis and prohibit redistribution; written confirmation is required for this proprietary backtest and retained research archive. | **Targeted fallback probe only.** A sample and written policy are mandatory; current public documentation does not establish coverage. |
| **TrueData** | Authorized vendor; one-minute chart/history products and proprietary-analysis licensing are documented. | Product pages explicitly state **back-adjusted in split and bonus**. | Historical depth and bulk pricing require provider confirmation. | Paid/quote-based. | **Reject as native source under documented default.** Another provider's adjusted candles do not solve the defect. |
| **Accelpix** | Authorized vendor with API/bulk history; older months/years can be requested. Entry plan is ₹1,599/month + GST with 45 days of one-minute history; older bulk delivery is separately priced. | Documentation says corporate actions are applied across every resolution and identifies adjusted IEOD. | Bulk history may exist, but documented series is adjusted. | Paid; bulk quote required. | **Reject as native source unless a separately documented raw-trade/unadjusted product is proven.** |
| **Zerodha Kite Connect** | Several years of one-minute OHLCV; ₹500/month published API price. | Zerodha explicitly states historical charts are adjusted for bonuses, splits, rights, spin-offs and qualifying extraordinary dividends. | Date depth is adequate. | Paid broker API; personal-use restrictions. | **Reject as native source.** Adequate depth does not cure retrospective transformation. |
| **Upstox V3** | Required dates were accessible in prior bounded authenticated checks. | S0-R4B established retrospectively adjusted HDFCBANK and RELIANCE history. | Adequate for the tested dates. | Existing authenticated service; no purchase in this task. | **Reject as native source for the affected pre-bonus periods.** |
| **Current public GitHub archive** | Full one-minute research archive already frozen and hashed. | S0-R4A proved mixed/transformed HDFCBANK and RELIANCE price and volume bases. | Adequate date depth. | Free/public. | **Reject for native pre-action OHLCV.** Preserve as evidence; do not overwrite. |

The NSE authorized-vendor list establishes exchange-vendor status for GFDL, TrueData and Accelpix, but real-time-vendor authorization does not prove that a particular historical product is native, complete, or licensed for this use.

## 2. Why NSE trade data is the correct primitive

The CM trade specification defines:

- `PO` versus `RM` market-session indicator;
- transaction time in NSE jiffies (`65,536` jiffies per second, epoch 1-Jan-1980);
- security symbol and series;
- transaction price in paise;
- non-zero trade quantity in shares; and
- all trade ticks, with the full historical form available after 30 days.

For each admitted EQ security and IST minute, KATS can derive:

- `open` = first eligible trade price;
- `high` = maximum eligible trade price;
- `low` = minimum eligible trade price;
- `close` = last eligible trade price; and
- `volume` = sum of eligible trade quantities.

The aggregation policy must freeze how `PO`, `RM`, auctions, special sessions, cancellations/corrections and duplicate trade numbers are handled before reading strategy signals. Daily NSE bhavcopies remain a reconciliation check, not a substitute for minute trades.

## 3. Licensing and cost

### Measured/documented

- NSE's effective-1-April-2026 tariff lists CM Historical Trade Data at ₹1,10,000 per annum/site, exclusive of taxes and levies.
- CM Historical Order & Trade Data is ₹12,50,000 per annum/site and is unnecessary for source OHLCV recovery.
- NSE's data-use policy requires a relevant agreement defining handling, retention, transmission, dissemination and end-user restrictions.
- NSE's reduced research category concerns non-commercial research. KATS is intended to evaluate a future profit-seeking trading system, so it must not self-classify as non-commercial academic research.

### Unknown pending written confirmation

- Whether the published annual tariff covers the entire 19-month historical interval or requires more than one annual charge.
- Whether symbol-filtered delivery is available at a lower price.
- Whether local retention, deterministic aggregation, internal backtesting and storage of derived candles are permitted.
- Whether small derived result artifacts may be committed privately/publicly without containing licensed raw values.
- Taxes, onboarding charges and delivery-channel charges applicable to this request.

No subscription, quote acceptance, paid trial or purchase is authorized by this report.

## 4. Governed reconstruction feasibility

### 4.1 Price-factor accuracy

For each 1:1 bonus, the archive's pre-action price is nominally native price divided by two. Inversion by multiplying by two is mathematically simple but not lossless:

- Original NSE prices traded on the date-effective tick grid.
- Division by two can create half-tick values.
- A provider that stores two decimals or rounds adjusted OHLC fields destroys the original tick choice.
- S0-R4A's HDFCBANK example demonstrates this: official high ₹1,716.95 divided by two is ₹858.475, while the archive stores ₹858.50. Multiplying back yields ₹1,717.00, not the traded ₹1,716.95.

Therefore reconstructed prices may be useful only in a separately labelled diagnostic ledger after empirical error bounds are frozen. They are not yet admissible as exact historical executable prices.

### 4.2 Intraday OHLC integrity

A factor correction cannot repair malformed bars or recover trade order. The frozen archive's invalid HDFCBANK 2024-06-25 09:15 OHLC relationship remains invalid after multiplying every price field by two. Any reconstruction must still pass S0-R3a strict validation, complete-bucket rules, tick validity and NSE-daily containment checks.

### 4.3 Native minute volume

S0-R4A found that pre-action archive volume moves in the expected reciprocal direction but does not equal official total volume multiplied by the corporate-action factor. This prevents exact inversion. Possible explanations—provider omissions, trade-category differences, rounding or undocumented processing—remain unknown.

There is no defensible operation that converts an adjusted minute-volume series back to native traded shares without independent native trade quantities. Volume reconstruction is therefore `NOT_PROVEN`.

### 4.4 RVOL compatibility

The frozen signal requires current opening volume divided by the mean of exactly twenty prior valid opening sessions, with a threshold of 1.50.

- If both numerator and all twenty denominator sessions were transformed by the same exact scalar, the scalar would cancel.
- The observed volume transformation is not exact.
- For twenty-session windows crossing a bonus date, pre-action adjusted volumes and post-action native volumes use different bases; no scalar cancellation is possible.
- HDFCBANK windows crossing 26-Aug-2025 and RELIANCE windows crossing 28-Oct-2024 are therefore causally incompatible with the frozen RVOL gate until native volume is recovered.
- Silently changing the RVOL threshold, excluding inconvenient dates after inspecting signals, or treating adjusted volume as share turnover would create a different hypothesis.

`RVOL_COMPATIBILITY=BLOCKED_WITH_ADJUSTED_OR_PRICE_ONLY_RECONSTRUCTION`

## 5. Admission criteria

### Native price admission

All conditions must pass:

1. Exact security identity, ISIN, symbol and EQ series are date-effective.
2. Provider supplies unadjusted executed trade prices or explicitly documented unadjusted one-minute candles.
3. Timestamp epoch, timezone, session marker and interval semantics are documented.
4. Raw response/file bytes and SHA-256 are frozen before aggregation.
5. Every derived minute respects the date-effective tick grid and OHLC containment.
6. Pre-open, regular, auction and nonstandard sessions are classified from official calendars.
7. Daily open/high/low/last and traded quantity reconcile to NSE primary records under a frozen reconciliation rule.
8. No provider-created synthetic/stale candle is admitted as a trade.

### Native volume admission

All conditions must pass:

1. Unit is explicitly **shares traded**, not adjusted shares, turnover, cumulative volume, lots or an undocumented field.
2. Minute volume equals the sum of the admitted native trade quantities.
3. Daily minute-volume sums reconcile exactly to the corresponding included trade universe, or every documented exclusion is quantified.
4. Bonus/split processing does not retroactively rescale historical trade quantities.
5. Missing trade files, partial sessions and malformed/missing minutes fail closed without interpolation.
6. Twenty-session opening-volume histories are built entirely from one native basis across corporate-action dates.

### Legal/licensing admission

Written terms must permit private/proprietary strategy research, local retention, deterministic transformation to candles, and retention of non-redistributed derived results. Raw licensed data must never be committed to GitHub.

## 6. Route decision

| Route | Evidence quality | Cost | Time/risk | Decision |
|---|---|---|---|---|
| Official NSE CM trade ticks | Highest; native primary source | High: published ₹1.10 lakh/year/site + taxes, exact quote unknown | Requires subscription approval and aggregation work | **Recommended definitive route** if written coverage/licence confirmation is acceptable to Founder. |
| Licensed-vendor raw/unadjusted archive | Potentially adequate | Unknown; likely lower | No provider currently documents both required historical depth and proven native volume | **Probe before spending**, especially GFDL because `AdjustSplits=false` exists. |
| Governed reconstruction from current archive | Price approximation possible | Low monetary cost | Exact prices, volume and cross-action RVOL remain unproven | **Do not implement for scoring.** Only reconsider if native sample evidence empirically proves per-field recovery, including volume. |
| Stay blocked | No evidence contamination | Zero | Delays backtest | Correct outcome if the quote/licence or provider probe fails. |

## 7. Fastest credible path

1. Obtain a **non-binding written confirmation and small sample before purchase** from NSE Data & Analytics for CM Historical Trade Data covering HDFCBANK, RELIANCE and the other frozen EQ symbols from 2024-04-01 through 2025-10-31.
2. The response must state date coverage, file type, trade-time precision, quantity units, absence of retrospective corporate-action adjustment, permitted proprietary-backtest use, retention/derived-output rules and full price.
3. In parallel only if Founder authorizes provider outreach, ask GFDL whether a one-off older archive exists with `AdjustSplits=false` and native, unscaled trade quantities. Do not buy without a sample that passes the admission criteria.
4. If neither route is acceptable, remain `BLOCKED_DATA`; do not reconstruct and score.

The earliest credible eleven-stock net-of-cost backtest must use one admitted native OHLCV basis for every frozen symbol. HDFCBANK and RELIANCE cannot be mixed with adjusted provider volume while other stocks use native volume.

## 8. Smallest additional evidence request

Send NSE Data & Analytics one bounded, no-purchase request to `marketdata@nse.co.in` asking for:

- availability of **Capital Market Historical Trade Data** for 2024-04-01 through 2025-10-31;
- a one-day sample for HDFCBANK on 2025-08-25 and RELIANCE on 2024-10-25;
- confirmation that files contain original executed prices and trade quantities without retrospective corporate-action adjustment;
- price for the exact period and whether symbol-filtered delivery is possible;
- written permission for private proprietary backtesting, local retention and non-redistributed derived candles/metrics; and
- delivery method and checksum support.

This request commits no funds and does not authorize a purchase.

## 9. Safeguards

- Frozen files changed: **NO**
- Strategy rules changed: **NO**
- Signals generated: **NO**
- P&L calculated: **NO**
- Holdout accessed: **NO**
- Broker orders: **NO**
- Paid data purchased: **NO**

## Single next action

Obtain the bounded written NSE Data & Analytics coverage/licence/sample quotation specified in section 8; return it for Founder review before any payment or data acquisition.
