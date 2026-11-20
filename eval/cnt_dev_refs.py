"""Hand-written specs for the dev split (eval/cnt/dev/requests.json): what a correct layer-v2 answer looks like.

Used to validate the checker (every reference must pass on both engines, and every negative control must fail)
and to show that each dev ask can be said in the spec. Paths are relative to eval/cnt/.

    python eval/cnt_dev_refs.py            # draws, checks, prints a table
"""
RL = {"file": "data/run_log.xlsx", "sheets": "런로그"}
WS = {"file": "data/run_log.xlsx", "sheets": "주간요약"}
DT = {"file": "data/downtime.xlsx", "sheets": "정지이력"}
TGA = "data/tga_batches.xlsx"
ZONE = {"file": "data/r2_zone_temps.csv"}
DOE = {"file": "data/doe_temp_h2.csv"}
MONTH = "df['월'] = df['일자'].dt.month"
TAU = {"edges": [2.5, 3.0, 3.5, 4.0, 4.5, 5.0, 5.5, 6.0, 6.5, 7.0]}

REFS = {
    "D001.1": {**RL, "chart": "line", "x": "주차", "y": {"col": "CNT수율", "agg": "mean"}, "by": "반응기"},
    "D002.1": {**ZONE, "chart": "line", "x": "시각", "y": ["2존(°C)", "2존 SP(°C)", "2존 10분 이동평균"],
               "data_code": "df['2존 10분 이동평균'] = df['2존(°C)'].rolling(60).mean()"},
    "D004.1": {"file": TGA, "sheets": ["R1-260326-1", "R1-260716-1"], "combine": True, "y2": False},
    "D005.1": {"file": TGA, "sheets": ["R4-260407-1", "R4-260721-1"], "combine": True, "preset": "none",
               "x": {"col": "온도"}, "y1": {"col": "미분중량"}, "y2": False},
    "D006.1": {"file": "data/raman/*.csv", "preset": "none", "x": {"col": "A"}, "y1": {"col": "B", "label": "정규화 강도"},
               "y2": False, "combine": True, "legend": "outside right",
               "data_code": "y1 = y1 / y1[(x >= 1550) & (x <= 1620)].max()"},
    "D007.1": {**WS, "chart": "line", "x": "주차", "y": "합격률"},
    "D008.1": {**RL, "chart": "line", "x": "주차", "y": {"col": "CNT수율", "agg": "mean"}},
    "D003.1": {**ZONE, "chart": "scatter", "x": "1존", "y": "2존(°C)"},
    "D009.1": {**RL, "chart": "scatter", "x": "체류시간", "y": "CNT수율", "by": "반응기"},
    "D010.1": {**RL, "chart": "scatter", "x": "잔류금속", "y": "IG/ID", "by": "C여부", "colors": {"C": "red", "A/B": "gray"},
               "data_code": "df['C여부'] = np.where(df['등급'] == 'C', 'C', 'A/B')"},
    "D011.1": {**RL, "chart": "scatter", "x": "외기습도", "y": "잔류금속"},
    "D012.1": {**RL, "chart": "scatter", "x": "H2/C2H4비", "y": "CNT수율", "filter": ["반응기 == R3"]},
    "D013.1": {"file": "data/L3_MES_export_202607.csv", "chart": "scatter", "x": "잔류금속", "y": "CNT수율", "by": "반응기"},
    "D014.1": {**DOE, "chart": "scatter", "x": "H2/C2H4비", "y": "수율", "by": "2존온도"},
    "D015.1": {**RL, "chart": "bar", "x": "촉매로트", "y": {"col": "CNT수율", "agg": "mean"}, "values": "{:.1f}"},
    "D016.1": {**DT, "chart": "hbar", "x": "원인", "y": {"col": "정지시간", "agg": "sum"}, "sort": "desc"},
    "D017.1": {**RL, "chart": "bar", "x": "반응기", "y": {"col": "IG/ID", "agg": "mean"}, "by": "근무조"},
    "D018.1": {**DT, "chart": "bar", "x": "월", "y": "count", "by": "반응기", "filter": ["원인 == 노즐 막힘"], "data_code": MONTH},
    "D019.1": {**DT, "chart": "bar", "x": "월", "y": {"col": "정지시간(h)", "agg": "sum"}, "by": "원인", "stack": True,
               "data_code": MONTH + "; df['정지시간(h)'] = df['정지시간(분)'] / 60"},
    "D020.1": {**RL, "chart": "bar", "x": "반응기", "y": "count", "by": "등급", "stack": True},
    "D021.1": {**RL, "chart": "bar", "x": "작업자", "y": {"col": "CNT수율", "agg": "mean"}, "sort": "desc"},
    "D022.1": {"file": "data/diameters.csv", "chart": "histogram", "x": "직경", "by": "시료",
               "filter": ["시료 in [TEM-01, TEM-02]"], "bins": list(range(3, 29))},
    "D023.1": {**RL, "chart": "histogram", "x": "CNT수율"},
    "D024.1": {**DOE, "chart": "heatmap", "x": "H2/C2H4비", "y": "2존온도", "z": {"col": "수율", "agg": "mean"}},
    "D025.1": {**RL, "chart": "heatmap", "x": "주차", "y": "반응기", "z": {"col": "잔류금속", "agg": "mean"}},
    "D026.1": {**DT, "chart": "heatmap", "x": "시", "y": {"col": "요일", "order": list("월화수목금토일")},
               "data_code": "df['요일'] = df['일자'].dt.dayofweek.map(dict(enumerate('월화수목금토일'))); "
                            "df['시'] = df['시작시각'].astype(str).str[:2].astype(int)"},
    "D027.1": {**RL, "chart": "heatmap", "corr": ["1존온도", "2존온도", "3존온도", "C2H4유량", "H2유량", "H2/C2H4비", "체류시간",
                                                  "외기습도", "CNT수율", "잔류금속", "산화개시온도", "IG/ID"], "cmap": "RdBu_r"},
    "D028.1": {**DT, "chart": "pie", "x": "원인"},
    "D029.1": {**RL, "chart": "pie", "x": "등급", "colors": {"A": "green", "B": "orange", "C": "red"}},
    "D030.1": {**DT, "chart": "pie", "x": "원인", "y": {"col": "정지시간", "agg": "sum"},
               "filter": ["일자 between 2026-08-01 and 2026-08-30"]},
    "DS01.1": {**RL, "chart": "scatter", "x": "체류시간", "y": "CNT수율"},
    "DS01.2": {**RL, "chart": "bar", "x": {"col": "체류시간", "bins": TAU}, "y": {"col": "CNT수율", "agg": "mean"}},
    "DS01.3": {**RL, "chart": "bar", "x": {"col": "체류시간", "bins": TAU}, "y": {"col": "CNT수율", "agg": "mean"}, "values": "n"},
    "DS01.4": {**RL, "chart": "heatmap", "x": {"col": "체류시간", "bins": TAU}, "y": "반응기", "z": {"col": "CNT수율", "agg": "mean"}},
    "DS02.1": {"file": TGA, "sheets": "all", "combine": True, "y2": False},
    "DS02.2": {"file": TGA, "sheets": ["R1-260326-1", "R4-260407-1", "R4-260721-1"], "combine": True, "y2": False},
    "DS02.3": {"file": TGA, "sheets": ["R1-260326-1", "R4-260407-1", "R4-260721-1"], "combine": True, "y2": False,
               "y1": {"min": 0, "max": 105}, "x": {"step": 100}, "title": "TGA (Air, 10 °C/min)"},
    "DS03.1": {**DT, "chart": "bar", "x": "반응기", "y": "count"},
    "DS03.2": {**DT, "chart": "bar", "x": "반응기", "y": "count", "by": "원인", "stack": True},
    "DS03.3": {**DT, "chart": "pie", "x": "원인"},
    "DS03.4": {**DT, "chart": "line", "x": "월", "y": "count", "filter": ["원인 == 노즐 막힘"], "data_code": MONTH},
    "DS04.1": {**ZONE, "chart": "line", "x": "시각", "y": "2존(°C)"},
    "DS04.2": {**ZONE, "chart": "line", "x": "시각", "y": "2존(°C)",
               "filter": ["시각 between 2026-06-17 20:00:00 and 2026-06-17 22:00:00"]},
    "DS04.3": {**ZONE, "chart": "histogram", "x": "편차", "bins": list(range(-4, 37, 2)),
               "filter": ["시각 between 2026-06-17 20:00:00 and 2026-06-17 22:00:00"],
               "data_code": "df['편차'] = df['2존(°C)'] - df['2존 SP(°C)']"},
}


def negatives(refs):
    """Wrong answers the checker must reject: another aggregate, a dropped filter, a different kind, wrong colours."""
    import copy
    out = {}
    for k, s in refs.items():
        s = copy.deepcopy(s)
        y = s.get("y")
        if s.get("chart") in ("bar", "hbar", "line") and isinstance(y, dict) and y.get("agg") == "mean":
            out[k + ":sum"] = {**s, "y": {**y, "agg": "sum"}}
        if s.get("filter"):
            out[k + ":nofilter"] = {kk: v for kk, v in s.items() if kk != "filter"}
        if s.get("chart") == "pie":
            out[k + ":asbar"] = {**s, "chart": "bar", "y": s.get("y", "count")}
        if s.get("colors") and isinstance(s["colors"], dict):
            out[k + ":colors"] = {**s, "colors": {kk: "blue" for kk in s["colors"]}}
        if s.get("stack"):
            out[k + ":nostack"] = {kk: v for kk, v in s.items() if kk != "stack"}
        if s.get("chart") == "heatmap" and isinstance(s.get("z"), dict):
            out[k + ":count"] = {**s, "z": {"col": None, "agg": "count"}}
    return out


if __name__ == "__main__":
    import argparse
    import json
    import os
    import sys
    import tempfile
    from pathlib import Path
    HERE = Path(__file__).resolve().parent
    sys.path.insert(0, str(HERE))
    import cnt_check
    import cnt_runs
    ap = argparse.ArgumentParser()
    ap.add_argument("--engines", default="matplotlib,echarts")
    ap.add_argument("--neg", action="store_true", help="also run the negative controls")
    ap.add_argument("--only")
    a = ap.parse_args()
    items = {f"{it['id']}.{i}": t["expect"] for it in json.loads((HERE / "cnt" / "dev" / "requests.json").read_text())["items"]
             for i, t in enumerate(it["turns"], 1)}
    cases = dict(REFS)
    if a.neg:
        cases.update(negatives(REFS))
    if a.only:
        cases = {k: v for k, v in cases.items() if k.split(":")[0] in a.only.split(",")}
    tmp = Path(tempfile.mkdtemp(prefix="cnt_refs_"))
    (tmp / "data").symlink_to(HERE / "cnt" / "data", target_is_directory=True)
    os.chdir(tmp)
    bad = 0
    for eng in a.engines.split(","):
        for k, spec in cases.items():
            base = k.split(":")[0]
            res, facts, dt = cnt_runs.draw_spec(spec, eng, tmp, k.replace(":", "_").replace(".", "_"))
            chk = cnt_check.check(items[base], facts, res, spec)
            want = ":" not in k
            ok = chk["pass"] == want
            bad += not ok
            if not ok or not want is False:
                print(f"{'OK ' if ok else 'BAD'} {eng:10} {k:18} pass={chk['pass']} {dt:4.1f}s {' | '.join(chk['failed'])[:220]}"
                      + (f" UNCHECKED {chk['unchecked']}" if chk["unchecked"] else ""), flush=True)
    print("problems:", bad)
