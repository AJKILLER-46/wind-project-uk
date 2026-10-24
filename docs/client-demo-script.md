# WindLens UK: Client Demonstration Script & Presentation Plan

**Target Audience**: UK Utility Day-Ahead Power Traders, Energy Portfolio Directors, Risk Managers  
**Total Target Duration**: 4 minutes 45 seconds (Strictly under 5:00 minutes)  
**Presenter**: Senior Full-Stack Energy Solutions Engineer  

---

## Timed Walkthrough

### 0:00 – 0:30 | Introduction & The Trading Problem
* **Visual**: Application Home / Executive Overview with live UK National Grid branding.
* **Speaker Script**:
  > "Hello. Welcome to WindLens UK, an energy analytics platform engineered for UK day-ahead power trading desks and renewable portfolio managers.
  >
  > In the UK market, trading desks must commit generation schedules and place Day-Ahead Auction orders before gate closure—typically 11:00 AM on the day prior to delivery. With over 28 gigawatts of installed wind capacity in Great Britain, wind forecast uncertainty directly drives imbalance exposure and cashout risk.
  >
  > Today, we demonstrate how WindLens UK solves a fundamental backtesting failure: preventing lookahead bias by selecting strictly the latest forecast available at gate closure, auditing forecast evolution, and evaluating commercial balancing requirements."

---

### 0:30 – 1:15 | Platform Overview & January 2026 Reporting Scope
* **Visual**: Highlight the top navigation bar, date selector (`2026-01-15`), decision cutoff (`11:00 D-1`), and data provenance badge.
* **Speaker Script**:
  > "Our reporting scope covers the full month of January 2026—1,488 half-hour settlement periods.
  >
  > At the top of the interface, users have complete transparency over data origin. WindLens UK integrates two core Elexon BMRS streams: FUELHH for actual metered wind outturn, and WINDFOR for multi-run forecast publications.
  >
  > Notice our gate cutoff filter is currently set to 11:00 D-1 Europe/London. All calculations respect UK Local Time, seamlessly managing the transition between Greenwich Mean Time and British Summer Time."

---

### 1:15 – 2:15 | Point-in-Time Forecast Selection in Action
* **Visual**: Navigate to the **Forecast Explorer** tab. Select Settlement Period 24 (Midday 11:30–12:00). Hover over the publication timeline chart and audit log table.
* **Speaker Script**:
  > "Let's examine Settlement Period 24 on January 15th. 
  >
  > In real market operations, Elexon publishes multiple WINDFOR runs across the 24 hours leading up to delivery. Other analytics dashboards mistakenly evaluate performance against the latest forecast published immediately before delivery. That is hindsight analysis.
  >
  > Here in the Forecast Explorer, you can see our selection engine in action:
  > - At the 11:00 D-1 auction gate, the latest eligible forecast was published at 10:15 D-1, forecasting **14,200 MW**. That is the exact number our trader used to place bids.
  > - Later updates published at 18:00 D-1 or on delivery morning updated this to 15,100 MW. While those later runs were closer to the actual outturn of 15,350 MW, they were completely unavailable at the decision gate.
  >
  > WindLens UK visually distinguishes the gate-selected forecast with our green decision badge, ensuring traders are never unfairly penalized or rewarded for information they did not possess."

---

### 2:15 – 3:15 | Actual vs. Forecast Comparison & Error Analytics
* **Visual**: Switch to **Executive Overview** and then **Accuracy Analysis** tab. Walk through the KPI cards (MAE, RMSE, Bias, MAPE) and the daily trend chart.
* **Speaker Script**:
  > "Returning to the Executive Overview, we see the complete 48 settlement-period outturn curve alongside the day-ahead schedule.
  >
  > Our Core Analytics module computes four transparent statistical metrics:
  > - **MAE (Mean Absolute Error)**: across the day was 940 MW.
  > - **RMSE**: 1,180 MW, penalizing volatile ramp mismatches.
  > - **Signed Bias**: +180 MW. Under our market standard sign convention—Forecast minus Actual—a positive bias indicates that day-ahead forecasts modestly over-estimated wind output.
  > - **MAPE**: 8.2%. Crucially, periods where actual wind was 0 MW are explicitly isolated and documented, eliminating mathematical division-by-zero distortion.
  >
  > In the Accuracy Analysis tab, traders can review error distributions and daily trends across the entire month, pinpointing high-volatility weather events like the Storm Isha ramp on January 21st."

---

### 3:15 – 4:15 | Settlement Ledger Export & Procurement Scenario Simulator
* **Visual**: Click **Settlement Ledger** to show the 48-period table and CSV download button. Then switch to **Scenario Simulator** and adjust the sliders.
* **Speaker Script**:
  > "For operations and accounting, our Settlement Ledger provides a searchable, sortable half-hourly audit trail with one-click CSV export for downstream compliance.
  >
  > Finally, let's explore the commercial impact on our balance sheet using the **Scenario Simulator**.
  >
  > Wind generation variance directly impacts the residual demand that flexible thermal generation, batteries, and interconnectors must balance.
  >
  > Here, a portfolio analyst can set an assumed national demand of 38,000 MW and 8,000 MW of non-wind baseload. WindLens calculates:
  > - **Day-Ahead Planned Thermal Need**: 15,800 MW based on our 11:00 D-1 wind forecast.
  > - **Outturn Residual Generation**: 14,650 MW actual need.
  >
  > This reveals an illustrative balancing surplus of 1,150 MW that the trading desk had to manage in the within-day balancing mechanism."

---

### 4:15 – 5:00 | Summary of Value, Assumptions & Next Steps
* **Visual**: Return to Overview. Display disclaimer banner and architecture summary.
* **Speaker Script**:
  > "To summarize: WindLens UK delivers:
  > 1. Complete point-in-time integrity with zero lookahead bias.
  > 2. Full auditability of Elexon BMRS WINDFOR and FUELHH streams.
  > 3. Transparent error metrics adhering strictly to UK market conventions.
  > 4. Actionable flexibility dispatch modeling.
  >
  > As noted in our platform disclaimers, true commercial procurement requires full integration with your specific PPA contracts, battery assets, and bilateral hedges.
  >
  > The platform is fully containerized with Docker, automated with 45 verified test suites, and ready for deployment into your trading desk infrastructure. Thank you."

---

## Recording & Upload Checklist for Demo Video
- [ ] Screen resolution set to 1920x1080 (16:9).
- [ ] Dark mode theme verified (Tailwind Slate-950).
- [ ] Microphone check: clear audio, no background hum.
- [ ] Open tabs in advance:
  1. Executive Overview (`2026-01-15`, `11:00` cutoff)
  2. Forecast Explorer (SP #24)
  3. Accuracy Analysis
  4. Settlement Ledger (demonstrate CSV download)
  5. Scenario Simulator (adjust demand slider to 38,000 MW)
- [ ] Test timer running to ensure recording stops under 5:00 minutes.
- [ ] Upload to YouTube as **Unlisted**.
- [ ] Verify audio and visual quality on standard playback.
