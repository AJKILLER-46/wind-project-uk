# WindLens UK: Voiceover Cue Sheet & Teleprompter
**Target Duration**: 4 Minutes 45 Seconds | **Format**: Spoken Presentation

---

### [00:00 – 00:30] | 1. Introduction & The Trading Problem
* **Where to Look**: Top logo branding and Executive Overview chart.
* **What to Explain**: Why wind forecast uncertainty creates massive imbalance exposure for UK trading desks before 11:00 D-1 auction gate closure.
* **Read Aloud**:
> "Hello. Welcome to WindLens UK, an energy analytics platform engineered for UK day-ahead power trading desks and renewable portfolio managers.
>
> In Great Britain, power trading desks must commit generation schedules before the Day-Ahead Auction gate closure at 11:00 AM on the day prior to delivery. With over 28 gigawatts of wind, forecast uncertainty directly drives imbalance exposure and cashout risk."

---

### [00:30 – 01:15] | 2. Gate Cutoff & Elexon Provenance
* **Where to Look**: Top right navbar (`Gate: 11:00 D-1 (Standard)`, `15-01-2026`).
* **What to Explain**: Point-in-time gate cutoff rule, UK Local Time handling (GMT/BST), and dual Elexon streams (FUELHH for outturn, WINDFOR for forecasts).
* **Read Aloud**:
> "Our reporting scope evaluates all 31 days of January 2026—1,488 half-hour settlement periods.
>
> At the top of the interface, notice the decision cutoff filter set to 11:00 D-1 Europe/London. All calculations strictly respect UK Local Time (GMT/BST). WindLens UK integrates two core Elexon BMRS streams: FUELHH for actual metered wind outturn, and WINDFOR for multi-run forecast publications."

---

### [01:15 – 02:15] | 3. Forecast Explorer & Point-in-Time Integrity
* **Where to Look**: Forecast Explorer tab, Settlement Period 24 (Midday), revision evolution chart, green star marker.
* **What to Explain**: Why selecting the latest forecast published before 11:00 D-1 (8,458 MW) prevents lookahead bias, while later runs (post-cutoff) are isolated for hindsight analysis.
* **Read Aloud**:
> "In the Forecast Explorer for Settlement Period 24 (Midday 11:30–12:00): Elexon publishes multiple WINDFOR forecast runs leading up to delivery. Other dashboards mistakenly evaluate performance against the latest forecast published immediately before delivery. That is hindsight analysis.
>
> Here, at 11:00 D-1, the latest eligible forecast was 8,458 MW—marked with our green star. Later runs updated this, but were unavailable at gate closure. WindLens isolates post-cutoff runs, guaranteeing zero lookahead bias."

---

### [02:15 – 03:15] | 4. Accuracy Metrics & Error Distribution
* **Where to Look**: Accuracy Analysis tab, KPI summary cards (MAE, RMSE, Signed Bias, MAPE), daily error bars, histogram.
* **What to Explain**: Four transparent error metrics, Forecast minus Actual sign convention, and strict zero-actual exclusion from MAPE.
* **Read Aloud**:
> "In Accuracy Analysis, we track error volatility across all 31 days of January. Our Core Analytics module computes four transparent metrics: MAE (837 MW), RMSE (1,079 MW), and Signed Bias (+204 MW).
>
> Following UK market standard convention—Forecast minus Actual—positive bias indicates over-forecasting. Crucially, periods where actual wind was 0 MW are strictly isolated from MAPE, eliminating mathematical division-by-zero distortion."

---

### [03:15 – 03:45] | 5. 48-Period Settlement Ledger & CSV Export
* **Where to Look**: Settlement Ledger tab, 48-row table, column headers (SP, Target Delivery, Actual MW, Decision Forecast MW, Error), Download CSV button.
* **What to Explain**: Full granular audit trail for trade reconciliation and 1-click export of 1,488 records.
* **Read Aloud**:
> "In the Settlement Ledger, operations and trading desks have a complete 48-period audit trail with verified UK local timestamps, settlement period IDs, outturn, and gate-selected forecasts.
>
> With one click, traders can download the full CSV export containing all 1,488 rows for downstream trade reconciliation and settlement risk analysis."

---

### [03:45 – 04:25] | 6. Scenario Simulator: Residual Demand
* **Where to Look**: Scenario Simulator tab, Demand Slider (38,000 MW), Baseload Slider (8,000 MW), balancing result cards.
* **What to Explain**: How wind variance translates into flexible thermal/battery dispatch need in the Balancing Mechanism.
* **Read Aloud**:
> "Finally, in the Scenario Simulator, we translate wind uncertainty into commercial procurement requirements.
>
> With 38,000 MW national demand and 8,000 MW non-wind baseload, WindLens calculates the Planned Thermal Need (20,802 MW) versus Actual Outturn (21,069 MW). This reveals the exact dispatchable flexibility that gas CCGTs, peakers, and battery storage had to provide in the balancing mechanism."

---

### [04:25 – 04:45] | 7. Architecture & Deployment Handover
* **Where to Look**: Bottom architecture badge & platform summary.
* **What to Explain**: Docker containerization, 45 automated test suites, production handover readiness.
* **Read Aloud**:
> "To summarize: WindLens UK delivers complete point-in-time integrity with zero lookahead bias, transparent error metrics, and commercial dispatch modeling.
>
> The application is Docker containerized, verified with 45 automated pytest suites, and ready for deployment into your trading desk infrastructure. Thank you."
