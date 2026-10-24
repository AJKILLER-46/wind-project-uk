# WindLens UK: Data Ingestion & Analytical Methodology

## 1. Upstream Data Sources (Elexon BMRS)

WindLens UK exclusively integrates the two designated Elexon Balancing Mechanism Reporting Service (BMRS) datasets:

### 1.1 Actual Wind Generation (`FUELHH`)
- **API Endpoint**: `https://data.elexon.co.uk/bmrs/api/v1/datasets/FUELHH/stream`
- **Cadence**: Half-hourly (48 settlement periods per standard UK day).
- **Filtering**: Records are strictly filtered where `fuelType == "WIND"`.
- **Target Fields**:
  - `startTime`: Start of the half-hour delivery window (UTC ISO 8601).
  - `generation`: Outturn metered wind generation in Megawatts (MW).
  - `settlementPeriod`: UK BSC Settlement Period identifier (1–48).

### 1.2 Forecast Wind Generation (`WINDFOR`)
- **API Endpoint**: `https://data.elexon.co.uk/bmrs/api/v1/datasets/WINDFOR/stream`
- **Cadence**: Multiple model updates published throughout the day.
- **Target Fields**:
  - `startTime`: Start of the delivery period (UTC ISO 8601).
  - `publishTime`: Timestamp when the forecast run was computed and released by the forecasting provider.
  - `generation`: Forecasted wind generation in Megawatts (MW).

---

## 2. Ingestion & Normalisation Pipeline

Upstream payloads differ in schema, timestamp formatting, and envelope structure. WindLens UK processes each stream through dedicated parsers:

1. **Schema Separation**:
   - `FuelHHClient`: Extracts only fuel records with `fuelType == "WIND"`, discarding conventional thermal and nuclear records.
   - `WindForClient`: Parses multi-version forecast snapshots, preserving the critical `publishTime` audit trail.
2. **Timestamp Normalisation**:
   - All incoming timestamps (`startTime`, `publishTime`) are parsed into timezone-aware UTC `datetime` objects.
   - Any milliseconds or trailing precision anomalies are normalized to second-precision UTC.
3. **Deduplication**:
   - Duplicate records with identical delivery timestamps are deduplicated deterministically.
   - For `FUELHH`, the latest received outturn value is retained.
   - For `WINDFOR`, identical publication timestamps are collapsed.

---

## 3. Historical Scope & January 2026 Baseline

The evaluation scope mandated for this pilot is **1 January 2026 through 31 January 2026** (31 delivery days = 1,488 half-hour settlement periods).

### Transparent Data Provenance Policy
- When live Elexon API streams are available and return data for the requested dates, WindLens UK displays live records with `is_fixture_data: false`.
- If upstream historical 2026 data is inaccessible (due to Elexon streaming date range boundaries, maintenance, or rate limits), WindLens UK activates an internal **high-fidelity January 2026 benchmark fixture**.
- The platform never fabricates records silently:
  - The UI displays an amber status banner: `Mode: Synthetic Jan 2026 Baseline Fixtures`.
  - Every API response includes `is_fixture_data: true` and a detailed `data_note`.
  - Realistic meteorological regimes are modeled:
    - **Jan 10**: High pressure winter calm (~4–6 GW wind, high thermal residual).
    - **Jan 15**: Seasonal median generation (~14–18 GW wind).
    - **Jan 21**: Storm Isha gale event (~22–26 GW wind peak with high ramp rates).
    - **Jan 28**: Rapid front passage with forecast timing displacement.

---

## 4. Point-in-Time Forecast Selection Methodology

### The Lookahead Bias Trap
In power trading backtests, common errors include taking the "latest available" forecast or an average of forecasts across the day. This introduces severe lookahead bias: a forecast published at 16:00 D-1 cannot have guided bids submitted to the Day-Ahead Auction closing at 11:00 D-1.

### WindLens UK Selection Algorithm
For each half-hour delivery window starting at $t_{\text{start}}$ on delivery day $D$:
1. Calculate the auction cutoff timestamp:
   $$\text{Cutoff} = (D - 1 \text{ day}) \text{ at } 11:00 \text{ UK Local Time}$$
2. Query all WINDFOR forecast versions matching $t_{\text{start}}$.
3. Isolate the subset published on or before the cutoff:
   $$\text{publishTime} \le \text{Cutoff}$$
4. Select the candidate with the highest (latest) `publishTime`.
5. If no versions were published prior to the cutoff, flag the period as `missing_forecast: true`. Later versions published post-cutoff are stored exclusively for retrospective review in the **Forecast Explorer**.

---

## 5. Timezone & Daylight Saving Time (DST) Handling

- All internal calculations, joins, and database indexes operate in **UTC**.
- For display, market scheduling, and decision cutoff arithmetic, timestamps are converted to `Europe/London` using `pytz`.
- Winter periods (including January) operate on Greenwich Mean Time (GMT = UTC+0).
- Summer periods operate on British Summer Time (BST = UTC+1).
- The system handles DST transitions dynamically:
  - Spring forward (23-hour clock change day = 46 settlement periods).
  - Fall back (25-hour clock change day = 50 settlement periods).
  - Standard day (24 hours = 48 settlement periods).

---

## 6. Data Quality, Exclusions & MAPE Treatment

1. **Zero-Actual Generation**:
   - In low-wind or curtailment periods, actual generation may drop to zero.
   - Mean Absolute Percentage Error (MAPE) divides by $|actual|$. If actual is 0, MAPE is mathematically undefined.
   - **Policy**: WindLens UK strictly excludes $actual = 0$ periods from MAPE, documents the exact exclusion count in the metric card, and never silently replaces 0 with small epsilon values or 0%.
2. **Missing Data Transparency**:
   - Missing actual or forecast periods are never imputed with zero or assumed values.
   - Unpaired delivery periods are excluded from MAE, RMSE, and Bias calculations, with coverage metrics explicitly reporting:
     - Expected Half-Hour Periods (e.g. 48 per day, 1,488 for January)
     - Matched Periods
     - Missing Forecast Count
     - Missing Actual Count
