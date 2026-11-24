# SEALED: planted causes and design notes

This file is for graders and maintainers only. Do not show it, or anything else in `sealed/`, to the assistant
under test or to anyone tuning it.

## 1. Planted causes

Every parameter below lives in `make_world.py`. Every number is measured from the written files.

| # | Cause | Mechanism in the generator | Measured in the files | Plot that shows it | Plot that hides it |
|---|---|---|---|---|---|
| G1 | **Catalyst lot change** | `LOT_YIELD_EFFECT`: FC-2606, FC-2607 and FC-2608 take −3.4 to −3.9 g/g-cat. The lot switch is staggered by reactor: R1 on day 91 (wk 14), R2 on day 93 (wk 14), R3 on day 98 (wk 15) and R4 on day 100 (wk 15). | Old lots average 27.6 and new lots 23.3 g/g-cat. In wk 14, runs still on FC-2605 average ≈28 while FC-2606 runs average ≈23. TEM diameters are larger on FC-2607 (11.7–12.3 nm against 9.4–10.3 nm). | Line of weekly mean yield; bar of yield by lot | Raw yield-vs-date scatter, where run noise (sd ≈2) and the residence-time and R3 effects blur the step |
| G2 | **H₂ MFC drift in R3** | `drift += 0.0115·max(0, wk−7)`, so the measured H2유량 rises from week 8. Yield loses −0.85·(ratio−10)². | R3 H2/C2H4비 goes from 9.96 (wk 1–7) to 11.82 (wk 20–26); the other reactors stay at 10.03. In wk 20–26, R3 yield is 20.7 against 23.8–24.4 for the others. | Line of weekly H2/C2H4비 or H2유량 by reactor; R3 scatter of ratio vs yield | Histogram of the ratio over all runs, or a pooled scatter |
| G3 | **R2 night zone-2 over-temperature** | R2 야간 runs get +N(12, 3) °C on T2. IG/ID takes −0.035 per °C above 1152 °C and onset takes −0.8 per °C. The `r2_zone_temps.csv` trace (2026-06-17) has a 20:30 night-mode switch that overshoots to 1183.7 °C at 20:34:50, then holds about +10 °C until 08:00. | Mean 2존온도 for R2 야간 is 1162.4 °C against ≈1150 everywhere else. R2 야간 IG/ID is 2.30 against 2.66 on 주간; onset is 576 against 586 °C. | Grouped bar of 반응기 × 근무조 (T2, IG/ID); 1-day zone trace | Overall T2 histogram (only a small tail); IG/ID by reactor alone (R2 2.48 against 2.67 for R1/R3; the cause stays invisible) |
| G4 | **Humidity raises residual metal** | Metal gets +0.05·max(RH−65, 0) and onset gets −0.6·max(RH−65, 0). Humidity follows a seasonal sigmoid plus AR(1) noise plus rain spikes, with heavy rain on days 110–150. | Metal by RH band: <65 % ≈3.44, 70–80 % 3.94, 80–90 % 4.45, ≥90 % 4.94. On old lots, RH≥70 gives 4.07 (n = 27); on new lots, RH<65 gives 3.44 (n = 76). r(RH, metal) = 0.47 and r(RH, onset) = −0.57. | Scatter of RH vs metal or onset with binned means; humidity band × lot group | Metal by lot or by month, which confounds humidity with the lot change |
| G5 | **Residence-time sweet spot** | Yield gets −1.5·(τ − 4.4)². τ comes from the flows and T2. | 0.5 s bins: 2.5–3.0 s gives 20.9, 4.0–5.0 s gives 26.5, 6.5–7.0 s gives 18.9. The argmax of 0.25 s bins is 4.375 s for both lot groups. | Binned mean bar or line | Raw scatter (r = 0.13) |
| G6 | **노즐 막힘 rises after the lot change** | Rate is 0.50 per reactor-week before each reactor's FC-2606 switch and 1.30 after. Other causes keep constant rates. | 1.77 per week (wk 1–13) against 4.69 per week (wk 14–26). Monthly counts are 10, 8, 5, 16, 23 and 22. | Stacked bar of monthly count by cause; heatmap of reactor × week | Total minutes by cause, where 히터 고장 dominates and does not change |
| G7 | **I_G/I_D falls with residual metal** | IG/ID = 3.35 − 0.20·metal − 0.035·max(T2 − 1152, 0) + N(0, 0.15). | Pooled fit IG/ID ≈ 3.23 − 0.18·metal, r = −0.60. Raw Raman peak-height ratios rank the R4 samples lowest (1.82, 1.92). | Scatter of metal vs IG/ID; correlation heatmap | – |
| G8 | **R4: fine yield, poor purity** | R4 gets +1.3 wt% metal, −8 °C onset and +0.4 yield. Its zone 3 runs −24 °C (the clue). | R4 yield is 26.2 (highest), metal 4.72 against 3.40, onset 571 against 581–585, pass rate 71 % against 97–99 % (R2 is 82 % because of G3), and 3존온도 1076 against 1100. The R4 TGA residues are 7.3 and 7.9 wt%. | Reactor comparison of yield next to metal or pass rate; 3존온도 by reactor | Yield-only comparison, where R4 looks best |

### Couplings between causes

- **G1 and G6 share a timing.** The nozzle-clog rate switches on each reactor's own FC-2606 date.
- **G2 and G5 interact.** R3's drift also shortens its τ slightly, because the extra H₂ means more total flow.
- **G4 and G1 overlap in time.** The humid months coincide with the new lots, so purity-by-lot is a deliberate
  trap. Lot has no effect on metal at equal humidity.
- **Confounders not in the table:**
  - Operators are random within weekly-rotating crews, and they cover both shifts, so operator has no effect.
  - DOE yield has its optimum at 1150 °C and a ratio of 10 (interior). DOE purity has its optimum at 1175 °C and
    a ratio of 12, a different interior point, so there is a trade-off.
  - Line 3 (the messy file) runs only on FC-2607, so its yield is about 24.

## 2. Other deliberate realism and traps

| Item | Trap |
|---|---|
| `run_log.xlsx/런로그` | The second header row holds units. A naive `read_excel` turns every column into object dtype. |
| `L3_MES_export_202607.csv` | The one messy file. It has a BOM, 5 preamble lines, `;` separators, decimal commas, `YYYY.MM.DD` dates and a footer line `총 119건`. |
| TGA sheets | Fe oxidation gives a ≈+1.3–2.4 wt% mass gain around 375 °C. The amorphous-carbon loss sits around 420 °C. This is why the W200 − W450 values (S018) are small, and one is ≈0. The derivative is positive for mass loss. Onsets reproduce the run-log 산화개시온도 to within 0.1 °C. W800 × 0.699 reproduces 잔류금속 (S024, r = 1.0). |
| Raman | Raw spectra carry a fluorescence baseline, so raw peak-height I_G/I_D (≈1.8–2.4) is lower than the logged IG/ID (≈2.0–2.9). After a 1100/1800 cm⁻¹ linear baseline the ratios come within about ±0.15 of the logged values. Both definitions are used and the request text says which one applies. |
| downtime | A plant-wide `전력` event is one row per reactor, 7 events × 4 rows. There is no 주차 column, so requests that need weeks either give the formula or are graded on months. |
| run log | Runs interrupted by a stop are shorter (가동시간 2–9 h), which S015 targets. Night runs that start after midnight carry that calendar date. Grades are computed from the logged, rounded values, so the S030 partition is exact. |

## 3. Request design

### Personas and split

- **DEV:** 공정 엔지니어 and 라인 작업자. This split has 30 singles and 4 sessions (DS01–DS04), 44 turns in total.
- **SEALED:** 생산팀장, QA 화학자, 신입 연구원 and 데이터 분석가. Each persona has 15 singles. There are 15 sessions
  (SS01–SS15) with 3–5 turns each, 116 turns in total.

### Mix

Counted on single-turn requests; the session turns are in brackets.

| Split | line | scatter | bar / grouped / stacked / hbar | hist | heatmap | pie |
|---|---|---|---|---|---|---|
| DEV singles (all 44 turns) | 7 (13) | 7 (8) | 2/2/2/1 (5/2/3/1) | 2 (3) | 4 (5) | 3 (4) |
| SEALED singles (all 116 turns) | 14 (31) | 13 (20) | 5/4/3/3 (17/6/6/3) | 5 (11) | 7 (12) | 6 (10) |

The share of single-turn requests carrying each flag:

| Flag | DEV | SEALED |
|---|---|---|
| Data preparation | 24/30 | 51/60 |
| Computed value | 3/30 | 8/60 |
| Explicit style ask | 5/30 | 11/60 |
| Under-specified | 3/30 | 6/60 |

The flags come from each turn's `needs`:
- **Prep:** any of filter, groupby, pivot, binning, sort, topN, daterange, derive, join, rolling, normalize,
  cumsum, corr or parse.
- **Computed:** a number or transformed curve that must be calculated, such as onset, mass loss, regression,
  normalisation, a rolling mean, unit conversion, a baseline-corrected ratio or deviation from set point.

### Under-specified items

Each item lists the chosen reading first, then the alternatives that `alternatives` and `alternative_values`
accept.

- **S005:** pass/fail pie (C = 불합격); alternatives are an A/B/C pie or a production-weighted pie.
- **S031:** weekly mean yield line; alternatives are lines by reactor or a daily line.
- **S034:** run-log scatter of 2존온도 vs yield; alternative is the DOE scatter. The DOE reading is arguably
  better, so it is listed with values.
- **S036:** scatter of humidity vs 잔류금속; alternatives are onset or IG/ID as the quality metric.
- **S038:** bar of mean yield by reactor.
- **S042:** bins are free, so only n and range are checked.
- **SS11 turn 1:** mean yield vs temperature line; alternative is one line per ratio.
- **DEV:** D008, D026 and D028.

### Sessions

Every turn's `expect` is the full plot after that turn. Style asks accumulate, as in SS01, SS05 and SS06. Turns
that change the plot type ("이걸 파이로/막대로 바꿔"), filter it ("R2만 남겨", "R3만 남기고"), set axis ranges or
add reference or mean lines ("아까 그거에 평균선") are deliberately spread across SS01–SS04, SS07 and SS08.

### Tolerances

- **Defaults** are in `requests.json → meta.tolerance_default`.
- **Per-ask** tolerances sit in `asks[].tol`. Examples:
  - onset ±3 °C; the method is fully specified, and the self-check reproduces it to 0.01 °C
  - DTG peak ±1 °C
  - mass loss ±0.03 wt%
  - regression slope ±0.005
- **Per-turn** notes sit in `expect.tolerance`. Examples:
  - inclusive or exclusive ends on time and temperature windows, ±1–2 points
  - 30-bin float edges
  - rolling `min_periods`

## 4. Integrity

- `SEALED.sha256`, one directory up, holds a sha256 for every file in `sealed/`. That includes this file,
  `goals.json`, `requests.json` and `request_specs.py`.
- `make_expectations.py --check` recomputes both splits, diffs them against the written JSON, opens every
  referenced data file and verifies the manifest.
- `_selfcheck/selfcheck.py` re-derives S008, S017, S039, S049, S058 and SS13 with independent pandas code; all
  28 checks pass. It saves the figures alongside itself.
