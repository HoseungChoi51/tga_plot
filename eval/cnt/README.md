# CNT plant eval world (simulated)

A simulated data world for testing a chat plotting assistant. Engineers at a carbon-nanotube (CNT) maker ask for
plots, mostly in Korean. All companies, people and numbers here are made up.

## The plant

**한결나노텍(가상) 울산 2공장, CNT 2라인.** Multi-wall CNT powder made by floating-catalyst CVD (FC-CVD).

- **Reactors:** four vertical tube reactors, `R1`–`R4`. Each has three heater zones:
  - 1존: preheat and catalyst decomposition, about 1050 °C
  - 2존: growth zone, set point 1150 °C
  - 3존: exit zone, about 1100 °C
- **Feed:** ethylene (C₂H₄) is the carbon source and H₂ is the carrier gas, both in sccm. The catalyst is a
  ferrocene/thiophene solution sprayed through an injector nozzle. Catalyst lots are named `FC-YYMM`
  (FC-2602 … FC-2608).
- **Residence time:** derived from the total flow and the zone-2 temperature. The effective hot volume is 11.8 L:

  τ = V · 60 · 273.15 / (Q_tot[slm] · (T₂ + 273.15))

- **Operation:** runs of about 9–16 h, with roughly 9 runs per reactor per week. A run that is cut short by a
  stop is shorter.
- **Shifts:** 주간 08:00–20:00 and 야간 20:00–08:00. A run's shift is the shift in which it started. Four crews
  rotate weekly.
- **Period:** production weeks 1–26. Week 1 starts Monday 2026-03-02, and the last day is 2026-08-30.
  **주차 = (일자 − 2026-03-02) // 7 + 1.**
- **Quality:**
  - TGA in air (10 °C/min) gives the residual metal (Fe wt%, from the Fe₂O₃ residue × 0.699) and the oxidation
    onset temperature.
  - Raman (532 nm) gives I_G/I_D.
  - Grades:

    | 등급 | Condition |
    |---|---|
    | A | 잔류금속 ≤ 3.5 wt%, IG/ID ≥ 2.6 and 산화개시온도 ≥ 575 °C |
    | B | 잔류금속 ≤ 5.0 wt% and IG/ID ≥ 2.2 (and not A) |
    | C | everything else; C is 불합격 |

## Data files (`data/`)

### `run_log.xlsx`, the production run log (997 runs)

**Sheet `런로그`.** Row 1 holds the headers and **row 2 holds the units**. Data starts at row 3. Read it with
`pd.read_excel(path, sheet_name="런로그", skiprows=[1])`.

| Column | Unit | Description |
|---|---|---|
| 런ID | – | `{반응기}-{yymmdd}-{n}`, where n is the run's sequence number for that reactor on that day |
| 일자 | date | run start date |
| 주차 | – | production week 1–26 |
| 근무조 | – | 주간 / 야간, the shift at run start |
| 반응기 | – | R1–R4 |
| 촉매로트 | – | catalyst lot in use (FC-2602 … FC-2608) |
| 작업자 | – | operator in charge (8 people) |
| 1존온도, 2존온도, 3존온도 | °C | run-average zone temperatures (PV) |
| C2H4유량 | sccm | ethylene flow |
| H2유량 | sccm | hydrogen flow, measured |
| H2/C2H4비 | – | H2유량 / C2H4유량 |
| 체류시간 | s | gas residence time in the hot zone |
| 외기습도 | % | outdoor relative humidity at run start |
| 가동시간 | h | run duration |
| CNT수율 | g/g-cat | CNT mass per catalyst mass fed |
| 생산속도 | g/h | throughput; production per run in kg = 생산속도 × 가동시간 / 1000 |
| 잔류금속 | wt% | TGA residual Fe |
| 산화개시온도 | °C | TGA extrapolated oxidation onset |
| IG/ID | – | Raman G/D intensity ratio |
| 등급 | A/B/C | quality grade (see above) |

**Sheet `주간요약`.** One row per week, computed from `런로그`:

| Column | Description |
|---|---|
| 주차 | production week |
| 시작일 | Monday of the week |
| 런수 | number of runs |
| 평균수율(g/g-cat) | mean CNT수율 |
| 평균잔류금속(wt%) | mean 잔류금속 |
| 합격률(%) | share of grade A or B runs |
| 총생산량(kg) | Σ 생산속도 × 가동시간 / 1000 |

### `tga_batches.xlsx`, TGA exports for 10 batches

There is one sheet per batch, and the sheet name is the 런ID (e.g. `R1-260326-1`). Each run is in air at
10 °C/min from 30 to 900 °C, sampled every 3 s (1741 rows).

| Column | Unit | Description |
|---|---|---|
| 시간 (min) | min | time since start |
| 온도 (°C) | °C | sample temperature |
| 중량 (%) | wt% | sample weight, normalised to the initial weight |
| 미분중량 (%/°C) | %/°C | −d(중량)/dT; positive while the sample loses mass |

### `raman/*.csv`, Raman spectra for 8 samples

The file name is the 런ID (e.g. `raman/R4-260407-1.csv`). Each spectrum covers 1000–3000 cm⁻¹ in 1560 points
on a slightly non-uniform pixel grid. The raw counts include a fluorescence background.

| Column | Unit |
|---|---|
| Raman Shift (cm-1) | cm⁻¹ |
| Intensity (a.u.) | counts |

### `r2_zone_temps.csv`, reactor R2 zone temperatures for one day

This file covers 2026-06-17 from 00:00:00 to 23:59:50 at 10 s resolution (8640 rows).

| Column | Unit | Description |
|---|---|---|
| 시각 | `YYYY-MM-DD HH:MM:SS` | timestamp |
| 1존(°C), 2존(°C), 3존(°C) | °C | zone PVs |
| 2존 SP(°C) | °C | zone-2 set point |

### `doe_temp_h2.csv`, the DOE on temperature × H₂ ratio

This is a full-factorial design with 3 replicates:
- 5 zone-2 temperatures: 1100, 1125, 1150, 1175 and 1200 °C
- 6 H₂/C₂H₄ ratios: 6, 8, 10, 12, 14 and 16

That gives 90 rows.

| Column | Unit | Description |
|---|---|---|
| 실험번호 | – | DOE-01 … DOE-90, in standard order |
| 실험순서 | – | randomised run order |
| 2존온도(°C) | °C | zone-2 set point |
| H2/C2H4비 | – | H₂/C₂H₄ ratio |
| 반복 | – | replicate 1–3 |
| 수율(g/g-cat) | g/g-cat | yield |
| 순도(%) | % | TGA carbon purity |

### `downtime.xlsx`, the equipment stop log (294 events)

**Sheet `정지이력`.** A plant-wide power event appears as one row per reactor.

| Column | Unit | Description |
|---|---|---|
| 일자 | date | stop date |
| 시작시각 | HH:MM | stop start time |
| 반응기 | – | R1–R4 |
| 원인 | – | 노즐 막힘, 촉매 공급 이상, 히터 고장, 전력 or 기타 |
| 정지시간(분) | min | stop duration |
| 비고 | – | free-text note |

### `diameters.csv`, TEM outer diameters

There are 6 samples with 160–290 tubes each, 1300 rows in total. The data is in long format.

| Column | Unit | Description |
|---|---|---|
| 시료 | – | TEM-01 … TEM-06 |
| 반응기 | – | reactor of the sample |
| 촉매로트 | – | catalyst lot of the sample |
| 직경(nm) | nm | outer diameter of one tube |

### `L3_MES_export_202607.csv`, a raw MES export from line 3 (pilot)

This is an export from a different line: pilot reactors P1 and P2, July 2026, 119 runs. It is left exactly as
the MES wrote it:
- UTF-8 with a BOM and CRLF line endings
- **5 preamble lines** (title, line, period, export stamp and a blank line)
- `;` as the separator and a **decimal comma**
- dates written as `2026.07.01`
- a **footer line** `총 119건`

The columns are 일자, 반응기, 촉매로트, 가동시간(h), CNT수율(g/g-cat), 잔류금속(wt%), IG/ID and 비고.

## Eval layout

| Path | Contents |
|---|---|
| `make_world.py` | Seeded, deterministic generator; writes `data/`. CSVs are byte-identical on re-run, and xlsx cell values are identical. |
| `make_expectations.py` | Loads the written files with pandas, computes the ground-truth values for every request, and writes `dev/requests.json` and `sealed/requests.json` plus `SEALED.sha256`. |
| `dev/` | The development split: request specs and `requests.json`. |
| `sealed/` | The held-out split. Do not open it while developing the assistant. |
| `SEALED.sha256` | sha256 of every file in `sealed/`. Check it with `sha256sum -c SEALED.sha256` from `eval/cnt/`. |
| `_selfcheck/` | Independent matplotlib re-draws of a few requests, used as a sanity check. |

Regenerate everything from `eval/cnt/`:

```
../../.venv/bin/python make_world.py
../../.venv/bin/python make_expectations.py
../../.venv/bin/python make_expectations.py --check   # recompute and compare with the written JSON
```

### Request format

Each item looks like this:

```
{ id, persona, split, type: single|session, files,
  turns: [ { text, needs: [...], expect: { kind, data, values, asks, alternatives, [alternative_values], [tolerance] } } ] }
```

- `kind` is one of `bar`, `grouped_bar`, `stacked_bar`, `hbar`, `line`, `scatter`, `histogram`, `heatmap` or
  `pie`.
- `data` describes the source, the sheet, the x/y/by columns, filters (pandas `query` syntax), the aggregation,
  sorting, top-N and bins. `derive` holds pandas expressions for computed columns.
- `values` is the ground truth, computed from the files in `data/`. `meta.value_conventions` explains its
  layout, and `meta.tolerance_default` gives the default tolerances.
- In a session, each turn's `expect` describes the whole plot expected after that turn, not just the change.
