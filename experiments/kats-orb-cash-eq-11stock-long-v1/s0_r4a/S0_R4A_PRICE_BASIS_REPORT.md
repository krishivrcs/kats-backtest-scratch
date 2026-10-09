# KATS S0-R4A — Corporate-Action Price-Basis Verification

**Hypothesis:** `KATS-ORB-CASH-EQ-11STOCK-LONG-V1`  
**Accepted source:** `98fb16d73eb4c1105c66d15b2da848f489fe96ca`  
**Scope:** data admission only; no signals, ranks, trades, returns, P&L, or broker activity  
**Observation cutoff:** 2025-10-31 inclusive; the sealed holdout beginning 2025-11-01 was not read

## Verdict first

`S0_R4A_PARTIAL_REQUIRES_TARGETED_EVIDENCE`

The public archive does **not** preserve contemporaneously tradable prices across the three investigated corporate actions as one native series. HDFCBANK and RELIANCE use retrospectively bonus-adjusted pre-event prices and a post-event native price basis. The archive member named `TMPV_1m.csv.gz` retroactively transforms and renames pre-demerger TATAMOTORS history and contains non-trading, zero-volume rows before the 10:00 IST regular session on 14 October 2025. None of those transformed pre-event candles may be admitted as historical executable prices without a separately governed recovery procedure.

## Evidence classes

- **Official:** NSE circulars and NSE cash-market bhavcopies; original Tata Motors disclosure.
- **Measured:** bounded, pre-holdout measurements from the frozen public archive after independently recomputing its SHA-256.
- **Provided:** authenticated Upstox V3 observations supplied by the Founder; raw responses are not available in this Work session.
- **Inference:** price/volume transformation classification obtained by comparing measured archive values with official records. Inference is never represented as an exchange quote or executable fill.

## Frozen archive verification

| Item | Verified value |
|---|---|
| Archive URL | `https://github.com/voletiramu/nse-fno-1min-data/releases/download/v1.0.0/stocks_1m_csvs.zip` |
| Bytes | `485923642` |
| SHA-256 | `20024713c455cc16b5daae91e06991d57a1acfa6a30c77bb7d5a742ee1789ab2` |
| HDFCBANK member SHA-256 | `e7727769383fc4ea9291c0ef839fb7e4e77dcd2ceb173f2b713485c18975293b` |
| RELIANCE member SHA-256 | `a66c91f2967d71cec19caca08ed5dc199106926de37401d8412b283bfeae9ca2` |
| TMPV member SHA-256 | `ba676a666caa92b66b61b283ec6b4883bed933095566f889430980c129a32058` |

The archive contains `TMPV_1m.csv.gz` back to 2024, but no exact `TATAMOTORS_1m.csv.gz` member. That filename is later than the security name applicable to the older rows and is not proof of legal or economic continuity.

## Official corporate-action evidence ledger

| Security | Official evidence | Established fact |
|---|---|---|
| HDFCBANK | [NSE/FAOP/69840](https://nsearchives.nseindia.com/content/circulars/FAOP69840.pdf); [NSE/CML/69791](https://nsearchives.nseindia.com/content/circulars/CML69791.pdf) | 1:1 bonus; F&O adjustment factor 2; ex/effective date 26-Aug-2025; record date 27-Aug-2025; ISIN `INE040A01034`. |
| RELIANCE | [NSE/FAOP/64621](https://nsearchives.nseindia.com/content/circulars/FAOP64621.pdf); [NCL/CMPT/64652](https://nsearchives.nseindia.com/content/circulars/CMPT64652.pdf); [NSE/CML/64862](https://nsearchives.nseindia.com/content/circulars/CML64862.pdf) | 1:1 bonus; adjustment factor 2; ex/effective and record date 28-Oct-2024; EQ ISIN `INE002A01018`; bonus allotment followed the record date. |
| TATAMOTORS | [NSE/CMTR/70614](https://nsearchives.nseindia.com/content/circulars/CMTR70614.pdf); [NSE/FAOP/70615](https://nsearchives.nseindia.com/content/circulars/FAOP70615.pdf) | Demerger ex/effective date 14-Oct-2025; special pre-open session 09:00–10:00 IST; ordinary 09:15 opening assumptions do not apply. |
| TATAMOTORS → TMPV | [NSE/FAOP/70882](https://nsearchives.nseindia.com/content/circulars/FAOP70882.pdf); [NCL/CMPT/70904](https://nsearchives.nseindia.com/content/circulars/CMPT70904.pdf) | Old symbol/name changed to `TMPV` / Tata Motors Passenger Vehicles Limited from 24-Oct-2025; reports through 23-Oct use `TATAMOTORS`, from 24-Oct use `TMPV`. The continuing listed ISIN is `INE155A01022`. |
| Demerged CV company | [Tata Motors scheme announcement](https://www.tatamotors.com/press-releases/demerger-of-cv-business-undertaking-of-tata-motors-ltd-into-a-separate-listed-company/) | Shareholders receive one TMLCV share for each existing TML share. The original listed entity retains/absorbs the passenger-vehicle businesses and later becomes TMPV; the separately listed CV company is economically distinct. |

The same ISIN before and after 24 October establishes security-record continuity for the surviving listed legal shell; it does not make the 13–14 October demerger value discontinuity an ordinary trading return.

## Date-by-date comparison

Official rows below are exact NSE cash-market daily records downloaded from the date-addressed bhavcopy endpoints listed in `EVIDENCE_MANIFEST.json`. “Archive close” is the final 15:29 one-minute close where a normal session exists; NSE `ClsPric` is an exchange daily close calculation and need not equal the final trade. Therefore the strongest basis checks use open/high/low and NSE `LastPric` where appropriate.

### HDFCBANK

| Date | Archive O/H/L/final | Official NSE O/H/L/close/last | Volume: archive / NSE | Finding |
|---|---:|---:|---:|---|
| 2024-06-25 | 835.60 / 858.50 / 837.40 / 853.50 | 1671.10 / 1716.95 / 1671.10 / 1711.35 / 1707.00 | 74,203,802 / 37,260,774 | Prices are approximately official values divided by 2; archive final equals official last divided by 2. The invalid first minute prevents exact low recovery. Volume is approximately doubled, not exactly. |
| 2025-08-25 | 980.10 / 988.70 / 978.50 / 984.60 | 1960.20 / 1977.40 / 1957.00 / 1964.10 / 1969.20 | 16,758,294 / 8,759,022 | Exact half-price alignment for O/H/L/last proves retrospective pre-bonus price adjustment. Volume is not an exact reciprocal transform. |
| 2025-08-26 | 979.50 / 985.70 / 968.00 / 972.30 | 979.50 / 985.70 / 968.00 / 973.40 / 972.30 | 16,858,542 / 16,917,731 | Post-bonus O/H/L/last are on the contemporaneous basis; minute-volume sum differs from official total. |
| 2025-10-31 | 994.00 / 1004.45 / 981.15 / 987.95 | 994.00 / 1004.45 / 981.15 / 987.30 / 987.95 | 22,518,224 / 23,221,330 | Post-bonus price basis remains native; volume remains incomplete or differently scoped. |

**Period classification:**

- Through 25-Aug-2025: `ADJUSTED_PRICE_BASIS_VERIFIED` for price; volume is transformed but not exactly reconstructible from a factor of two.
- From 26-Aug-2025: `NATIVE_PRICE_BASIS_VERIFIED` for O/H/L and observed last trade on sampled dates; minute-level executability remains unverified.
- Whole archive member: `MIXED_OR_TRANSFORMED_SERIES`.

The factor-of-two relationship does not repair the malformed 25-Jun-2024 opening minute and does not prove every original minute can be reconstructed.

### RELIANCE

| Date | Archive O/H/L/final | Official NSE O/H/L/close/last | Volume: archive / NSE | Finding |
|---|---:|---:|---:|---|
| 2024-10-25 | 1343.50 / 1344.35 / 1322.00 / 1328.15 | 2687.00 / 2688.70 / 2644.00 / 2655.70 / 2656.30 | 18,480,828 / 9,298,748 | Exact half-price alignment for O/H/L/last; retrospective bonus adjustment is proven. Volume is approximately, not exactly, doubled. |
| 2024-10-28 | 1337.00 / 1353.00 / 1322.10 / 1334.15 | 1337.00 / 1353.00 / 1322.10 / 1334.35 / 1335.00 | 10,745,130 / 10,824,350 | Ex-date O/H/L use contemporaneous post-bonus basis; archive final differs from official close/last within the day's traded range. |
| 2024-10-29 | 1328.10 / 1343.20 / 1320.30 / 1340.00 | 1328.10 / 1343.20 / 1320.30 / 1340.00 / 1340.00 | 11,802,639 / 12,008,361 | Post-bonus native price basis; minute-volume total is lower than official total. |
| 2024-10-30 | 1335.00 / 1350.00 / 1325.35 / 1345.00 | 1335.00 / 1350.00 / 1325.35 / 1343.90 / 1344.85 | 11,768,429 / 11,984,423 | O/H/L align; final-minute value is close to official last but not identical. |
| 2025-10-31 | 1490.40 / 1497.50 / 1482.30 / 1487.00 | 1490.40 / 1497.50 / 1482.30 / 1486.40 / 1487.00 | 8,685,549 / 8,758,053 | Native post-bonus price basis; incomplete/differently scoped volume persists. |

**Period classification:**

- Through 25-Oct-2024: `ADJUSTED_PRICE_BASIS_VERIFIED` for price; reciprocal volume adjustment is approximate only.
- From 28-Oct-2024: `NATIVE_PRICE_BASIS_VERIFIED` for sampled price extremes/open/last; minute-level executability remains unverified.
- Whole archive member: `MIXED_OR_TRANSFORMED_SERIES`.

### TATAMOTORS / TMPV

| Date | Archive measurement | Official NSE record | Provided Upstox observation | Finding |
|---|---|---|---|---|
| 2024-06-25 | `TMPV` member O 660.95, H 662.90, L 653.60, final 657.85; volume 10,578,529 | `TATAMOTORS` O 960.00, H 962.85, L 949.30, close 955.00, last 955.50; volume 7,304,128 | Not available in Work | Archive price factor is about 0.6885 and volume factor about 1.45. This is transformed, retroactively renamed history, not the contemporaneous TATAMOTORS tape. |
| 2025-10-13 | O 467.50, H 467.75, L 453.10, final 457.15; volume 48,139,930 | `TATAMOTORS` O 679.00, H 679.40, L 658.10, close 660.75, last 664.00; volume 33,288,645 | Last close/trade supplied as 664.00 under `NSE_EQ|INE155A01022` | Same ~0.6885 price transform and ~1.45 volume transform as the 2024 sample. The archive is not native pre-demerger history. |
| 2025-10-14 | 342 rows; earliest 09:15 at 561.65 with zero volume; sparse zero-volume 400.00 rows before 10:00; first positive-volume 10:00 bar O 399.00; daily low 376.30; final 394.90 | Special-session daily O 400.00, H 421.55, L 376.30, close 395.45, last 395.00 | 330 candles beginning 10:00; first regular-session open 399.00; last 395.00 | Archive includes non-trading/stale or synthetic pre-10:00 rows. Frozen 09:15 opening logic cannot apply. The 13–14 October discontinuity is corporate-action price discovery, not a trading loss. |
| 2025-10-15 | O 403.00, final 391.90 | O 403.00, close 390.85, last 391.90 | First open 403.00 | Post-demerger price basis agrees on open/last. |
| 2025-10-23 | final 405.60 | `TATAMOTORS` close 405.85, last 405.80 | Last 405.80 | Archive final differs by ₹0.20; identity still officially TATAMOTORS. |
| 2025-10-24 | O 406.95 under archive `TMPV` member | NSE symbol changes to `TMPV`; O 406.95 | First open 406.95 | Symbol transition and open align; this does not validate earlier transformed rows. |
| 2025-10-31 | final 410.15 | `TMPV` close 410.00, last 410.10 | Last 410.10 | ₹0.05 archive/provider difference; current post-transition price basis is otherwise aligned. |

**Period classification:**

- Before 14-Oct-2025: `ADJUSTED_PRICE_BASIS_VERIFIED` as a transformed price series, but the transform is not an admitted executable-price reconstruction.
- 14-Oct-2025: `SOURCE_INSUFFICIENT` for frozen-session use because of the official special pre-open and archive-inserted zero-volume rows.
- From 15-Oct-2025: sampled prices are on the post-demerger basis; the official symbol remains `TATAMOTORS` through 23-Oct and becomes `TMPV` on 24-Oct.
- Whole archive member: `MIXED_OR_TRANSFORMED_SERIES`.

## Admission decision

| Security | Required classification | Historical executable price recovery |
|---|---|---|
| HDFCBANK | `MIXED_OR_TRANSFORMED_SERIES` | **Blocked for pre-bonus minutes.** Daily evidence proves the transformation, not each original minute or executable quote. Post-bonus sampled price basis is native, but quote/depth evidence is absent. |
| RELIANCE | `MIXED_OR_TRANSFORMED_SERIES` | **Blocked for pre-bonus minutes.** Same limitation. Post-bonus sampled price basis is native, but quote/depth evidence is absent. |
| TATAMOTORS/TMPV | `MIXED_OR_TRANSFORMED_SERIES` | **Blocked before and across the demerger.** Retroactive naming, transformed prices/volumes, a special session, and synthetic/stale rows prevent admission as one uninterrupted executable series. |

No adjusted source is admitted as contemporaneous executable prices merely because its returns appear plausible.

## Volume-basis assessment

The direction of the pre-action volume transformation is consistent with reciprocal adjustment (approximately doubled for 1:1 bonuses and approximately 1/0.6885 for the TATAMOTORS demerger factor), but the totals do not equal the official totals multiplied by those factors. This may reflect missing trade categories, provider aggregation, rounding, or other undocumented processing. The cause is `SOURCE_INSUFFICIENT`; a deterministic native-volume reconstruction is not proven.

## Unresolved evidence and smallest targeted request

1. **Minute-level native reconstruction:** NSE daily OHLCV proves that the public archive is transformed but cannot prove every pre-action minute's original OHLCV. The smallest credential-safe request is a local, sanitized Upstox V3 evidence manifest—no token and no raw response upload—containing request date, instrument key, raw-response byte count and SHA-256, candle count, first/last timestamp, and selected first/last OHLCV for:
   - HDFCBANK: 2024-06-25, 2025-08-25, 2025-08-26;
   - RELIANCE: 2024-10-25, 2024-10-28;
   - `NSE_EQ|INE155A01022`: 2025-10-13, 2025-10-14, 2025-10-15, 2025-10-23, 2025-10-24, 2025-10-31.
2. **Tata special-session semantics:** retain the raw-response hashes and exact timestamp list for 14-Oct-2025 to establish that Upstox returns only the 330 regular-session candles starting 10:00 and that the archive's earlier zero-volume rows are provider-created rather than trades.
3. **Independence limitation:** Upstox matching the archive does not by itself establish exchange-authoritative minute prices if both derive from a common adjusted vendor pipeline. A future admission gate must label provenance and cannot use agreement alone as proof of independence.

## Governed recovery methodology (proposal only; not implemented)

Any reconstruction must be a separately authorized data-recovery method that:

1. preserves the original archive bytes and creates a new derived-data lineage;
2. freezes official action ratios, effective dates, security identities, and exceptional sessions before transforming data;
3. requires independent native minute evidence for both sides of each action;
4. applies a period-specific price factor and separately validated volume rule—never assumes reciprocal volume scaling;
5. rejects malformed, synthetic, stale, missing, and special-session-incompatible bars without interpolation;
6. keeps TATAMOTORS, surviving TMPV, and new TMCV economic identities explicit; and
7. publishes per-row provenance and deterministic checksums before any signal generation.

## Safety attestation

- Frozen files changed: **NO**
- Strategy rules changed: **NO**
- Signals generated: **NO**
- P&L calculated: **NO**
- Holdout accessed: **NO**
- Broker orders: **NO**

## Single next action

Founder authorizes only the bounded local Upstox evidence-manifest export listed above, after which an independent data-admission review may decide whether a separate native-price recovery methodology is warranted.
