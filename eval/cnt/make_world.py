#!/usr/bin/env python3
"""make_world.py - simulated FC-CVD CNT plant data for the plotting-assistant eval.

Plant (fictional): 한결나노텍 울산 2공장, CNT 2라인 (floating-catalyst CVD, R1-R4).
Deterministic: one master seed, independent child streams per data product.
Re-running gives byte-identical CSV files and identical cell values in the xlsx files.

Run from eval/cnt/:   ../../.venv/bin/python make_world.py
Writes eval/cnt/data/.
"""
from __future__ import annotations

import datetime as dt
from pathlib import Path

import numpy as np
import pandas as pd
from openpyxl import Workbook
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.utils import get_column_letter

HERE = Path(__file__).resolve().parent
OUT = HERE / "data"
SEED = 20260302
START = dt.datetime(2026, 3, 2)          # Monday = production week 1, day 0
N_WEEKS = 26
N_DAYS = N_WEEKS * 7
END = START + dt.timedelta(days=N_DAYS)
REACTORS = ["R1", "R2", "R3", "R4"]
FIXED_DOC_TIME = dt.datetime(2026, 9, 1, 9, 0, 0)

_ss = np.random.SeedSequence(SEED)
(RNG_HUM, RNG_DT, RNG_RUN, RNG_TGA, RNG_RAMAN,
 RNG_ZONE, RNG_DOE, RNG_DIA, RNG_L3) = [np.random.default_rng(s) for s in _ss.spawn(9)]

# --------------------------------------------------------------------------------------
# plant constants
# --------------------------------------------------------------------------------------
V_EFF_L = 11.8                       # effective hot volume of each reactor tube (L)
T_STD = 273.15
LOT_START_DAY = {                    # first day each catalyst (ferrocene/thiophene) lot is charged
    "FC-2602": 0, "FC-2603": 23, "FC-2604": 51, "FC-2605": 72,
    "FC-2606": 91, "FC-2607": 121, "FC-2608": 150,
}
LOT_OFFSET_DAYS = {"R1": 0, "R2": 2, "R3": 7, "R4": 9}
LOT_YIELD_EFFECT = {"FC-2602": 0.3, "FC-2603": -0.2, "FC-2604": 0.2, "FC-2605": 0.0,
                    "FC-2606": -3.9, "FC-2607": -3.4, "FC-2608": -3.7}
CREWS = {"A": ["김도현", "이서준"], "B": ["박지훈", "최유진"],
         "C": ["정민호", "강하늘"], "D": ["윤재원", "한수빈"]}
CREW_ORDER = ["A", "B", "C", "D"]


def lot_for(reactor: str, day: float) -> str:
    cur = "FC-2602"
    for lot, d0 in LOT_START_DAY.items():
        start = d0 if d0 == 0 else d0 + LOT_OFFSET_DAYS[reactor]
        if day >= start:
            cur = lot
    return cur


def lot_switch_day(reactor: str, lot: str) -> int:
    return LOT_START_DAY[lot] + LOT_OFFSET_DAYS[reactor]


# --------------------------------------------------------------------------------------
# ambient humidity (one value per calendar day)
# --------------------------------------------------------------------------------------
def make_humidity(rng) -> np.ndarray:
    d = np.arange(N_DAYS)
    base = 50.0 + 27.0 / (1.0 + np.exp(-(d - 108) / 12.0))       # spring ~50 %, summer ~77 %
    e = rng.normal(0, 7.0, N_DAYS)
    ar = np.zeros(N_DAYS)
    for i in range(1, N_DAYS):
        ar[i] = 0.55 * ar[i - 1] + e[i]
    p_rain = np.where((d >= 110) & (d <= 150), 0.32, 0.10)       # 장마 late June - July
    rain = rng.random(N_DAYS) < p_rain
    h = base + ar + rain * rng.uniform(10, 22, N_DAYS)
    return np.clip(h, 22, 97)


# --------------------------------------------------------------------------------------
# downtime events
# --------------------------------------------------------------------------------------
CAUSE_NOTES = {
    "노즐 막힘": ["인젝터 노즐 카본 퇴적, 교체", "노즐 세정 후 재가동", "분무 노즐 막힘, N2 퍼지",
              "노즐 팁 교체", "인젝터 차압 상승, 분해 세정"],
    "촉매 공급 이상": ["페로센 용액 펌프 압력 저하", "촉매 라인 기포 제거", "공급 펌프 재시작",
                 "용액 탱크 레벨 센서 오류", "시린지 펌프 알람"],
    "히터 고장": ["SSR 교체", "열전대 단선, 교체", "히터 엘리먼트 점검", "온도 컨트롤러 리셋",
              "히터 전류 불균형 점검"],
    "전력": ["순간 정전", "수전 전압 강하", "UPS 전환 후 재가동"],
    "기타": ["배기 필터 교체", "포집기 청소", "안전점검", "N2 퍼지 지연", "샘플링 대기",
           "원료가스 실린더 교체"],
}
WEEKLY_RATE = {"촉매 공급 이상": 0.70, "히터 고장": 0.35, "기타": 0.75}   # per reactor per week
NOZZLE_RATE_OLD, NOZZLE_RATE_NEW = 0.50, 1.30
DUR_MEDIAN = {"노즐 막힘": 50, "촉매 공급 이상": 70, "히터 고장": 200, "전력": 35, "기타": 30}
DUR_SIGMA = {"노즐 막힘": 0.5, "촉매 공급 이상": 0.6, "히터 고장": 0.7, "전력": 0.4, "기타": 0.8}


def make_downtime(rng) -> pd.DataFrame:
    ev = []
    for r in REACTORS:
        sw = lot_switch_day(r, "FC-2606")
        for day in range(N_DAYS):
            for cause in ["노즐 막힘", "촉매 공급 이상", "히터 고장", "기타"]:
                if cause == "노즐 막힘":
                    rate = NOZZLE_RATE_NEW if day >= sw else NOZZLE_RATE_OLD
                else:
                    rate = WEEKLY_RATE[cause]
                for _ in range(rng.poisson(rate / 7.0)):
                    t = START + dt.timedelta(days=day, seconds=int(rng.integers(0, 86400 // 60)) * 60)
                    dur = DUR_MEDIAN[cause] * np.exp(rng.normal(0, DUR_SIGMA[cause]))
                    ev.append((t, r, cause, max(5, int(round(dur))),
                               CAUSE_NOTES[cause][int(rng.integers(len(CAUSE_NOTES[cause])))]))
    # plant-wide power events hit all four reactors
    power_days = np.sort(rng.choice(np.arange(3, N_DAYS - 2), size=7, replace=False))
    for day in power_days:
        t0 = START + dt.timedelta(days=int(day), seconds=int(rng.integers(0, 1440)) * 60)
        base = DUR_MEDIAN["전력"] * np.exp(rng.normal(0, DUR_SIGMA["전력"]))
        note = CAUSE_NOTES["전력"][int(rng.integers(3))]
        for r in REACTORS:
            ev.append((t0, r, "전력", max(5, int(round(base * rng.uniform(0.8, 1.35)))), note))
    df = pd.DataFrame(ev, columns=["ts", "반응기", "원인", "정지시간(분)", "비고"])
    df = df.sort_values(["ts", "반응기"], kind="mergesort").reset_index(drop=True)
    return df


# --------------------------------------------------------------------------------------
# run log
# --------------------------------------------------------------------------------------
def make_runs(rng, hum: np.ndarray, downtime: pd.DataFrame) -> pd.DataFrame:
    rows = []
    start_offset_h = {"R1": 8.5, "R2": 11.0, "R3": 14.5, "R4": 17.0}
    for r in REACTORS:
        dts = downtime[downtime["반응기"] == r]
        ev_t = [(t - START).total_seconds() / 3600 for t in dts["ts"]]
        ev_d = list(dts["정지시간(분)"] / 60.0)
        k = 0
        t = start_offset_h[r]
        while t < N_DAYS * 24:
            runtime = float(np.clip(rng.normal(13.0, 1.2), 9.5, 16.5))
            gap = float(np.clip(rng.normal(5.6, 1.0), 3.5, 9.0))
            # skip events that happened before this run start (during previous gap)
            while k < len(ev_t) and ev_t[k] < t:
                k += 1
            extra = 0.0
            interrupted = False
            if k < len(ev_t) and ev_t[k] < t + runtime:       # stop during the run
                runtime = max(ev_t[k] - t, 2.0)
                extra = ev_d[k]
                interrupted = True
                k += 1
            while k < len(ev_t) and ev_t[k] < t + runtime + gap + extra:
                extra += ev_d[k]
                k += 1
            rows.append((r, t, runtime, interrupted))
            t = t + runtime + gap + extra
    runs = pd.DataFrame(rows, columns=["반응기", "t_h", "가동시간", "중단"])
    runs["start"] = [START + dt.timedelta(hours=h) for h in runs["t_h"]]
    runs = runs.sort_values(["start", "반응기"], kind="mergesort").reset_index(drop=True)

    out = []
    seq_count: dict = {}
    for _, row in runs.iterrows():
        r, st = row["반응기"], row["start"]
        st = st.replace(second=0, microsecond=0)
        day = (st - START).days
        week = day // 7 + 1
        hour = st.hour
        shift = "주간" if 8 <= hour < 20 else "야간"
        date = st.date()
        key = (r, date)
        seq_count[key] = seq_count.get(key, 0) + 1
        run_id = f"{r}-{st:%y%m%d}-{seq_count[key]}"
        lot = lot_for(r, day + hour / 24)
        wk0 = week - 1
        crew = CREW_ORDER[wk0 % 4] if shift == "주간" else CREW_ORDER[(wk0 + 2) % 4]
        operator = CREWS[crew][int(rng.integers(2))]
        night = shift == "야간"

        t1 = 1050 + rng.normal(0, 3.0)
        t2 = 1150 + rng.normal(0, 2.2)
        if r == "R2" and night:
            t2 += rng.normal(12.0, 3.0)
        t3 = 1100 + rng.normal(0, 3.0) - (24.0 + rng.normal(0, 2.0) if r == "R4" else 0.0)
        tau_target = float(np.clip(rng.normal(4.5, 0.75), 2.9, 6.6))
        ratio_set = rng.normal(10.0, 0.30)
        drift = 1.0 + rng.normal(0, 0.005)
        if r == "R3":
            drift += 0.0115 * max(0, week - 7)
        q_tot = V_EFF_L * 60 * T_STD / (tau_target * (t2 + T_STD))          # slm
        c2h4 = round(q_tot * 1000 / (1 + ratio_set) / 5) * 5                  # sccm
        h2 = round(c2h4 * ratio_set * drift / 10) * 10
        t1, t2, t3 = round(t1, 1), round(t2, 1), round(t3, 1)
        ratio = h2 / c2h4
        tau = V_EFF_L * 60 * T_STD / ((c2h4 + h2) / 1000 * (t2 + T_STD))
        h = float(np.clip(hum[min(day, N_DAYS - 1)] + rng.normal(0, 1.5), 20, 99))

        y = (28.6 + LOT_YIELD_EFFECT[lot] + (0.4 if r == "R4" else 0.0)
             - 1.5 * (tau - 4.4) ** 2 - 0.85 * (ratio - 10.0) ** 2
             - 0.004 * (t2 - 1150) ** 2 + rng.normal(0, 2.0))
        catfeed = 0.00052 * c2h4 * (1 + rng.normal(0, 0.03))                # g-cat/h
        thr = y * catfeed
        metal = (3.1 + (1.3 if r == "R4" else 0.0) + 0.05 * max(h - 65, 0)
                 + rng.normal(0, 0.40))
        metal = max(metal, 1.2)
        onset = (590 - 5 * (metal - 3.1) - 0.6 * max(h - 65, 0) - (8 if r == "R4" else 0)
                 - 0.8 * max(t2 - 1152, 0) + rng.normal(0, 5.0))
        igid = 3.35 - 0.20 * metal - 0.035 * max(t2 - 1152, 0) + rng.normal(0, 0.15)
        metal, onset, igid = round(metal, 2), round(onset, 1), round(igid, 2)   # grade from logged values
        if metal <= 3.5 and igid >= 2.6 and onset >= 575:
            grade = "A"
        elif metal <= 5.0 and igid >= 2.2:
            grade = "B"
        else:
            grade = "C"
        out.append({
            "런ID": run_id, "일자": date, "주차": week, "근무조": shift, "반응기": r,
            "촉매로트": lot, "작업자": operator,
            "1존온도": t1, "2존온도": t2, "3존온도": t3,
            "C2H4유량": int(c2h4), "H2유량": int(h2), "H2/C2H4비": round(ratio, 2),
            "체류시간": round(tau, 2), "외기습도": round(h, 1),
            "가동시간": round(row["가동시간"], 1),
            "CNT수율": round(y, 2), "생산속도": round(thr, 1),
            "잔류금속": round(metal, 2), "산화개시온도": round(onset, 1),
            "IG/ID": round(igid, 2), "등급": grade,
        })
    df = pd.DataFrame(out)
    df = df[df["주차"] <= N_WEEKS].reset_index(drop=True)
    return df


RUN_UNITS = {"런ID": "-", "일자": "yyyy-mm-dd", "주차": "-", "근무조": "-", "반응기": "-",
             "촉매로트": "-", "작업자": "-", "1존온도": "°C", "2존온도": "°C", "3존온도": "°C",
             "C2H4유량": "sccm", "H2유량": "sccm", "H2/C2H4비": "-", "체류시간": "s",
             "외기습도": "%", "가동시간": "h", "CNT수율": "g/g-cat", "생산속도": "g/h",
             "잔류금속": "wt%", "산화개시온도": "°C", "IG/ID": "-", "등급": "A/B/C"}


def weekly_summary(df: pd.DataFrame) -> pd.DataFrame:
    g = df.groupby("주차")
    ws = pd.DataFrame({
        "주차": sorted(df["주차"].unique()),
    })
    ws["시작일"] = [(START + dt.timedelta(days=7 * (w - 1))).date() for w in ws["주차"]]
    ws["런수"] = g.size().values
    ws["평균수율(g/g-cat)"] = g["CNT수율"].mean().round(2).values
    ws["평균잔류금속(wt%)"] = g["잔류금속"].mean().round(2).values
    ws["합격률(%)"] = (g["등급"].apply(lambda s: (s != "C").mean() * 100)).round(1).values
    prod = df["생산속도"] * df["가동시간"] / 1000.0
    ws["총생산량(kg)"] = prod.groupby(df["주차"]).sum().round(1).values
    return ws


def _style_header(ws, row, ncol, fill="DDEBF7", italic=False):
    for c in range(1, ncol + 1):
        cell = ws.cell(row=row, column=c)
        cell.font = Font(bold=not italic, italic=italic)
        cell.fill = PatternFill("solid", fgColor=fill)
        cell.alignment = Alignment(horizontal="center")


def _fix_props(wb):
    wb.properties.creator = "MES-ExportBot"
    wb.properties.created = FIXED_DOC_TIME
    wb.properties.modified = FIXED_DOC_TIME
    wb.properties.lastModifiedBy = "MES-ExportBot"


def write_run_log(df: pd.DataFrame, ws_df: pd.DataFrame, path: Path):
    wb = Workbook()
    ws = wb.active
    ws.title = "런로그"
    cols = list(df.columns)
    ws.append(cols)
    ws.append([RUN_UNITS[c] for c in cols])
    for rec in df.itertuples(index=False):
        ws.append(list(rec))
    _style_header(ws, 1, len(cols))
    _style_header(ws, 2, len(cols), fill="F2F2F2", italic=True)
    date_col = cols.index("일자") + 1
    for rr in range(3, len(df) + 3):
        ws.cell(row=rr, column=date_col).number_format = "yyyy-mm-dd"
    for i, c in enumerate(cols, start=1):
        ws.column_dimensions[get_column_letter(i)].width = max(9, len(c) * 1.8 + 2)
    ws.freeze_panes = "A3"

    w2 = wb.create_sheet("주간요약")
    w2.append(list(ws_df.columns))
    for rec in ws_df.itertuples(index=False):
        w2.append(list(rec))
    _style_header(w2, 1, ws_df.shape[1])
    for rr in range(2, len(ws_df) + 2):
        w2.cell(row=rr, column=2).number_format = "yyyy-mm-dd"
    for i, c in enumerate(ws_df.columns, start=1):
        w2.column_dimensions[get_column_letter(i)].width = max(10, len(c) * 1.6 + 2)
    _fix_props(wb)
    wb.save(path)


def write_simple_xlsx(sheets: dict, path: Path, date_cols=()):
    wb = Workbook()
    first = True
    for name, df in sheets.items():
        ws = wb.active if first else wb.create_sheet()
        first = False
        ws.title = name
        ws.append(list(df.columns))
        for rec in df.itertuples(index=False):
            ws.append([None if (isinstance(v, float) and np.isnan(v)) else v for v in rec])
        _style_header(ws, 1, df.shape[1])
        for c in date_cols:
            if c in df.columns:
                ci = list(df.columns).index(c) + 1
                for rr in range(2, len(df) + 2):
                    ws.cell(row=rr, column=ci).number_format = "yyyy-mm-dd"
        for i, c in enumerate(df.columns, start=1):
            ws.column_dimensions[get_column_letter(i)].width = max(10, len(str(c)) * 1.6 + 2)
        ws.freeze_panes = "A2"
    _fix_props(wb)
    wb.save(path)


# --------------------------------------------------------------------------------------
# TGA (air, 10 °C/min, 30-900 °C)
# --------------------------------------------------------------------------------------
def _logi(T, c, w):
    return 1.0 / (1.0 + np.exp(-(T - c) / w))


def _dlogi(T, c, w):
    s = _logi(T, c, w)
    return s * (1 - s) / w


TGA_PICKS = [  # (reactor, week, shift or None)
    ("R1", 4, "주간"), ("R1", 20, "주간"), ("R2", 16, "주간"), ("R2", 16, "야간"),
    ("R3", 9, None), ("R3", 24, None), ("R4", 6, None), ("R4", 21, None),
    ("R1", "humid", None), ("R2", 2, "주간"),
]


def pick_runs(df: pd.DataFrame) -> list:
    ids = []
    for r, wk, sh in TGA_PICKS:
        sub = df[df["반응기"] == r]
        if wk == "humid":
            s2 = sub[(sub["주차"] >= 18) & (sub["주차"] <= 22) & (sub["근무조"] == "주간")]
            ids.append(s2.sort_values("외기습도", ascending=False, kind="mergesort")["런ID"].iloc[0])
            continue
        s2 = sub[sub["주차"] == wk]
        if sh:
            s2 = s2[s2["근무조"] == sh]
        s2 = s2[~s2["런ID"].isin(ids)]
        ids.append(s2["런ID"].iloc[1])
    return ids


def make_tga(rng, run: pd.Series) -> pd.DataFrame:
    m = float(run["잔류금속"])
    onset = float(run["산화개시온도"])
    igid = float(run["IG/ID"])
    t_min = np.arange(0, (900 - 30) / 10 + 1e-9, 0.05)          # 3 s sampling
    T = 30 + 10 * t_min + rng.normal(0, 0.04, t_min.size)
    moist = 0.35 + 0.35 * rng.random()
    amorph = float(np.clip(1.6 + 2.6 * (2.9 - igid), 0.8, 5.5))
    w_main = 13.0 + rng.normal(0, 0.8)
    tc = onset + 2 * w_main
    gain = 0.4298 * m
    cnt = 100 - moist - amorph - m
    ca = 418 + rng.normal(0, 6)
    W = (100 - moist * _logi(T, 78, 18) - amorph * _logi(T, ca, 17)
         + gain * _logi(T, 375, 24) - cnt * _logi(T, tc, w_main))
    dW = (moist * _dlogi(T, 78, 18) + amorph * _dlogi(T, ca, 17)
          - gain * _dlogi(T, 375, 24) + cnt * _dlogi(T, tc, w_main))
    W = W + rng.normal(0, 0.004, T.size)
    dW = dW + rng.normal(0, 0.0015, T.size)
    return pd.DataFrame({"시간 (min)": np.round(t_min, 2), "온도 (°C)": np.round(T, 2),
                         "중량 (%)": np.round(W, 4), "미분중량 (%/°C)": np.round(dW, 5)})


# --------------------------------------------------------------------------------------
# Raman (532 nm, 1000-3000 cm-1)
# --------------------------------------------------------------------------------------
def _lor(x, x0, fwhm):
    g = fwhm / 2
    return g ** 2 / ((x - x0) ** 2 + g ** 2)


def make_raman(rng, igid: float) -> pd.DataFrame:
    n = 1560
    p = np.linspace(0, 1, n)
    x = 1000 + 2000 * (0.94 * p + 0.06 * p ** 2)          # slightly non-uniform pixel grid
    g_amp = 1800 * (1 + rng.normal(0, 0.15))
    d_amp = g_amp / igid
    d0 = 1347 + rng.normal(0, 1.5)
    g0 = 1582 + rng.normal(0, 1.0)
    y = (d_amp * _lor(x, d0, 48 + rng.normal(0, 2))
         + g_amp * _lor(x, g0, 31 + rng.normal(0, 1.5))
         + 0.22 * d_amp * _lor(x, 1617, 22)
         + 0.55 * g_amp * _lor(x, 2690 + rng.normal(0, 2), 72)
         + 0.07 * g_amp * _lor(x, 2935, 60))
    base = 220 + 0.06 * (x - 1000) + 25 * np.sin((x - 1000) / 900)
    y = y + base
    y = y + rng.normal(0, 1, n) * np.sqrt(y) * 0.9
    return pd.DataFrame({"Raman Shift (cm-1)": np.round(x, 2), "Intensity (a.u.)": np.round(y, 1)})


# --------------------------------------------------------------------------------------
# R2 zone temperatures, one day @ 10 s
# --------------------------------------------------------------------------------------
ZONE_DAY = dt.datetime(2026, 6, 17)


def make_zone_day(rng) -> pd.DataFrame:
    s = np.arange(0, 86400, 10)
    hrs = s / 3600.0
    n = s.size
    ar = np.zeros((3, n))
    e = rng.normal(0, 1, (3, n))
    for i in range(1, n):
        ar[:, i] = 0.92 * ar[:, i - 1] + 0.35 * e[:, i]
    off = np.zeros(n)
    # previous night (night-mode loop tuning): +10 °C with slow ripple, released at 08:00
    m_n1 = hrs < 8
    off[m_n1] = 10 + 3.0 * np.sin(2 * np.pi * s[m_n1] / 900.0)
    m_tr = (hrs >= 8) & (hrs < 9)
    tt = s[m_tr] - 8 * 3600
    off[m_tr] = 10 * np.exp(-tt / 360.0)
    # 20:30 switch to night mode -> underdamped overshoot, settles at +10 with ripple
    t0 = 20.5 * 3600
    m_n2 = s >= t0
    tp = s[m_n2] - t0
    off[m_n2] = (10 * (1 - np.exp(-tp / 240.0)) + 55 * np.exp(-tp / 420.0) * np.sin(2 * np.pi * tp / 1500.0)
                 + 3.0 * np.sin(2 * np.pi * tp / 900.0) * (1 - np.exp(-tp / 1800.0)))
    sp2 = np.full(n, 1150.0)
    z2 = sp2 + off + ar[1]
    z1 = 1050 + 0.15 * off + ar[0]
    z3 = 1100 + 0.30 * off + ar[2]
    ts = [(ZONE_DAY + dt.timedelta(seconds=int(v))).strftime("%Y-%m-%d %H:%M:%S") for v in s]
    return pd.DataFrame({"시각": ts, "1존(°C)": np.round(z1, 1), "2존(°C)": np.round(z2, 1),
                         "3존(°C)": np.round(z3, 1), "2존 SP(°C)": sp2.round(1)})


# --------------------------------------------------------------------------------------
# DOE: zone-2 temperature x H2/C2H4 ratio, 3 replicates
# --------------------------------------------------------------------------------------
def make_doe(rng) -> pd.DataFrame:
    rows = []
    for T in [1100, 1125, 1150, 1175, 1200]:
        for r in [6, 8, 10, 12, 14, 16]:
            for rep in (1, 2, 3):
                y = (31.5 - 0.0016 * (T - 1150) ** 2 - 0.30 * (r - 10) ** 2
                     - 0.004 * (T - 1150) * (r - 10) + rng.normal(0, 0.9))
                pur = 96.6 - 0.0012 * (T - 1175) ** 2 - 0.10 * (r - 12) ** 2 + rng.normal(0, 0.3)
                rows.append([T, r, rep, round(y, 2), round(min(pur, 99.5), 2)])
    df = pd.DataFrame(rows, columns=["2존온도(°C)", "H2/C2H4비", "반복", "수율(g/g-cat)", "순도(%)"])
    order = rng.permutation(len(df)) + 1
    df.insert(0, "실험순서", order)
    df.insert(0, "실험번호", [f"DOE-{i:02d}" for i in range(1, len(df) + 1)])
    return df


# --------------------------------------------------------------------------------------
# TEM outer diameters
# --------------------------------------------------------------------------------------
TEM_SAMPLES = [("TEM-01", "R1", "FC-2604", 9.6, 180), ("TEM-02", "R1", "FC-2607", 12.1, 220),
               ("TEM-03", "R2", "FC-2605", 9.8, 160), ("TEM-04", "R3", "FC-2604", 9.9, 250),
               ("TEM-05", "R4", "FC-2604", 10.2, 200), ("TEM-06", "R4", "FC-2607", 12.4, 290)]


def make_diameters(rng) -> pd.DataFrame:
    rows = []
    for sid, r, lot, mean, n in TEM_SAMPLES:
        sig = 0.27
        mu = np.log(mean) - sig ** 2 / 2
        d = np.exp(rng.normal(mu, sig, n))
        d = np.clip(d, 3.5, None)
        for v in d:
            rows.append([sid, r, lot, round(float(v), 1)])
    return pd.DataFrame(rows, columns=["시료", "반응기", "촉매로트", "직경(nm)"])


# --------------------------------------------------------------------------------------
# messy export from line 3 (pilot)
# --------------------------------------------------------------------------------------
def write_l3_export(rng, path: Path):
    rows = []
    for day in range(31):
        date = dt.date(2026, 7, 1) + dt.timedelta(days=day)
        for p in ("P1", "P2"):
            nrun = 2 if rng.random() < 0.92 else 1
            for _ in range(nrun):
                y = 24.3 + (0.9 if p == "P2" else 0.0) + rng.normal(0, 1.8)
                m = 3.5 + rng.normal(0, 0.45)
                ig = 3.35 - 0.2 * m + rng.normal(0, 0.15)
                rt = float(np.clip(rng.normal(10.5, 1.0), 6, 13))
                note = "" if rng.random() > 0.08 else ["샘플링", "재측정", "노즐 세정 후"][int(rng.integers(3))]
                rows.append([date.strftime("%Y.%m.%d"), p, "FC-2607", f"{rt:.1f}", f"{y:.2f}", f"{m:.2f}",
                             f"{ig:.2f}", note])
    lines = ["[MES 데이터 내보내기]",
             "라인: 3라인(파일럿) / 설비: P1,P2",
             "조회기간: 2026.07.01~2026.07.31",
             "출력: 2026.08.03 09:14:52 / 사용자: qa_kim",
             "",
             "일자;반응기;촉매로트;가동시간(h);CNT수율(g/g-cat);잔류금속(wt%);IG/ID;비고"]
    for r in rows:
        lines.append(";".join(v.replace(".", ",") if i in (3, 4, 5, 6) else v for i, v in enumerate(r)))
    lines.append(f"총 {len(rows)}건")
    path.write_bytes(("﻿" + "\r\n".join(lines) + "\r\n").encode("utf-8"))


# --------------------------------------------------------------------------------------
def main():
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "raman").mkdir(exist_ok=True)

    hum = make_humidity(RNG_HUM)
    dtm = make_downtime(RNG_DT)
    runs = make_runs(RNG_RUN, hum, dtm)
    write_run_log(runs, weekly_summary(runs), OUT / "run_log.xlsx")

    dt_out = pd.DataFrame({
        "일자": [t.date() for t in dtm["ts"]],
        "시작시각": [t.strftime("%H:%M") for t in dtm["ts"]],
        "반응기": dtm["반응기"], "원인": dtm["원인"],
        "정지시간(분)": dtm["정지시간(분)"].astype(int), "비고": dtm["비고"],
    })
    write_simple_xlsx({"정지이력": dt_out}, OUT / "downtime.xlsx", date_cols=("일자",))

    picks = pick_runs(runs)
    by_id = runs.set_index("런ID")
    tga = {rid: make_tga(RNG_TGA, by_id.loc[rid]) for rid in picks}
    write_simple_xlsx(tga, OUT / "tga_batches.xlsx")

    raman_ids = [picks[i] for i in (0, 1, 2, 3, 5, 6, 7, 8)]
    for f in sorted((OUT / "raman").glob("*.csv")):
        f.unlink()
    for rid in raman_ids:
        make_raman(RNG_RAMAN, float(by_id.loc[rid, "IG/ID"])).to_csv(
            OUT / "raman" / f"{rid}.csv", index=False, lineterminator="\n")

    make_zone_day(RNG_ZONE).to_csv(OUT / "r2_zone_temps.csv", index=False, lineterminator="\n")
    make_doe(RNG_DOE).to_csv(OUT / "doe_temp_h2.csv", index=False, lineterminator="\n")
    make_diameters(RNG_DIA).to_csv(OUT / "diameters.csv", index=False, lineterminator="\n")
    write_l3_export(RNG_L3, OUT / "L3_MES_export_202607.csv")

    print(f"runs: {len(runs)}  downtime events: {len(dt_out)}  TGA sheets: {picks}")
    print(f"raman: {raman_ids}")


if __name__ == "__main__":
    main()
