#!/usr/bin/env python3
"""make_expectations.py - compute ground-truth expectations for the CNT plotting eval.

Reads the request specs (dev/request_specs.py, sealed/request_specs.py), loads the
*written* data files in data/ with pandas (never generator internals), computes the values
each plot should show, and writes dev/requests.json and sealed/requests.json.
Finally writes SEALED.sha256 over every file in sealed/.

Run from eval/cnt/:   ../../.venv/bin/python make_expectations.py
"""
from __future__ import annotations

import datetime as dt
import glob
import hashlib
import json
import math
import sys
from functools import lru_cache
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent
PROD_START = pd.Timestamp("2026-03-02")

# --------------------------------------------------------------------------------------
# loading
# --------------------------------------------------------------------------------------


def read_l3(path: Path) -> pd.DataFrame:
    """Line-3 MES export: 5 preamble lines, ';' separator, decimal comma, 1 footer line."""
    df = pd.read_csv(path, sep=";", decimal=",", skiprows=5, skipfooter=1, engine="python",
                     encoding="utf-8-sig", dtype={"비고": str})
    df["일자"] = pd.to_datetime(df["일자"], format="%Y.%m.%d")
    return df


@lru_cache(maxsize=None)
def _read(path: str, sheet) -> pd.DataFrame:
    p = ROOT / path
    if path.endswith("run_log.xlsx"):
        if sheet in (None, "런로그"):
            return pd.read_excel(p, sheet_name="런로그", skiprows=[1])   # row 2 = units
        return pd.read_excel(p, sheet_name=sheet)
    if path.endswith(".xlsx"):
        return pd.read_excel(p, sheet_name=sheet if sheet is not None else 0)
    if "L3_MES" in path:
        return read_l3(p)
    df = pd.read_csv(p)
    if "시각" in df.columns:
        df["시각"] = pd.to_datetime(df["시각"])
    return df


@lru_cache(maxsize=None)
def sheet_names(path: str) -> tuple:
    return tuple(pd.ExcelFile(ROOT / path).sheet_names)


def load(d: dict) -> pd.DataFrame:
    src = d["source"]
    if isinstance(src, str) and "*" in src:
        srcs = sorted(str(Path(p).relative_to(ROOT)) for p in glob.glob(str(ROOT / src)))
    elif isinstance(src, str):
        srcs = [src]
    else:
        srcs = list(src)
    multi_file = len(srcs) > 1
    frames = []
    for s in srcs:
        sh = d.get("sheet")
        if s.endswith(".xlsx"):
            if sh == "*":
                sh = list(sheet_names(s))
            if isinstance(sh, (list, tuple)):
                for name in sh:
                    f = _read(s, name).copy()
                    f["_series"] = name
                    frames.append(f)
                continue
            f = _read(s, sh).copy()
        else:
            f = _read(s, None).copy()
        if multi_file:
            f["_series"] = Path(s).stem
        frames.append(f)
    return pd.concat(frames, ignore_index=True)


# --------------------------------------------------------------------------------------
# helpers available to spec expressions as H.*
# --------------------------------------------------------------------------------------
class H:
    PROD_START = PROD_START

    @staticmethod
    def runlog() -> pd.DataFrame:
        return _read("data/run_log.xlsx", "런로그").copy()

    @staticmethod
    def downtime() -> pd.DataFrame:
        return _read("data/downtime.xlsx", "정지이력").copy()

    @staticmethod
    def week_of(dates: pd.Series) -> pd.Series:
        return ((pd.to_datetime(dates) - PROD_START).dt.days // 7 + 1).astype(int)

    @staticmethod
    def cut(s: pd.Series, edges, fmt="{:g}–{:g}", right=False) -> pd.Series:
        labels = [fmt.format(a, b) for a, b in zip(edges[:-1], edges[1:])]
        return pd.cut(s, edges, labels=labels, right=right)

    @staticmethod
    def mid(s: pd.Series, edges, right=False) -> pd.Series:
        mids = [(a + b) / 2 for a, b in zip(edges[:-1], edges[1:])]
        return pd.cut(s, edges, labels=mids, right=right).astype(float)

    # ---- TGA
    @staticmethod
    def tga(sheet: str) -> pd.DataFrame:
        return _read("data/tga_batches.xlsx", sheet)

    @staticmethod
    def tga_w(sheet: str, T: float) -> float:
        t = H.tga(sheet)
        return float(np.interp(T, t["온도 (°C)"], t["중량 (%)"]))

    @staticmethod
    def tga_loss(sheet: str, t1: float, t2: float) -> float:
        return H.tga_w(sheet, t1) - H.tga_w(sheet, t2)

    @staticmethod
    def dtg_peak(sheet: str, lo=450, hi=800) -> float:
        t = H.tga(sheet)
        m = t[(t["온도 (°C)"] >= lo) & (t["온도 (°C)"] <= hi)]
        return float(m.loc[m["미분중량 (%/°C)"].idxmax(), "온도 (°C)"])

    @staticmethod
    def tga_onset(sheet: str, base_T=500.0) -> float:
        """Extrapolated onset: tangent at the DTG maximum (450-800 °C) meets the
        horizontal baseline through W(base_T)."""
        t = H.tga(sheet)
        m = t[(t["온도 (°C)"] >= 450) & (t["온도 (°C)"] <= 800)]
        i = m["미분중량 (%/°C)"].idxmax()
        Ti, Wi, Di = t.loc[i, "온도 (°C)"], t.loc[i, "중량 (%)"], t.loc[i, "미분중량 (%/°C)"]
        return float(Ti - (H.tga_w(sheet, base_T) - Wi) / Di)

    # ---- Raman
    @staticmethod
    def raman(stem: str) -> pd.DataFrame:
        return _read(f"data/raman/{stem}.csv", None)

    @staticmethod
    def raman_corrected(stem: str, b1=1100.0, b2=1800.0, half=10.0) -> pd.DataFrame:
        r = H.raman(stem)
        X, Y = r.iloc[:, 0].to_numpy(), r.iloc[:, 1].to_numpy()

        def at(a):
            return Y[(X >= a - half) & (X <= a + half)].mean()

        base = at(b1) + (at(b2) - at(b1)) * (X - b1) / (b2 - b1)
        return pd.DataFrame({"x": X, "y": Y - base})

    @staticmethod
    def raman_ratio(stem: str, baseline: bool = False) -> float:
        if baseline:
            r = H.raman_corrected(stem)
            X, Y = r["x"].to_numpy(), r["y"].to_numpy()
        else:
            r = H.raman(stem)
            X, Y = r.iloc[:, 0].to_numpy(), r.iloc[:, 1].to_numpy()
        g = Y[(X >= 1550) & (X <= 1620)].max()
        d = Y[(X >= 1300) & (X <= 1400)].max()
        return float(g / d)

    @staticmethod
    def raman_norm(df: pd.DataFrame, lo=1550.0, hi=1620.0) -> pd.DataFrame:
        """Divide each spectrum (by _series) by its maximum intensity in the G window."""
        df = df.copy()
        X, Y = "Raman Shift (cm-1)", "Intensity (a.u.)"
        gmax = df[(df[X] >= lo) & (df[X] <= hi)].groupby("_series")[Y].max()
        df["정규화 강도"] = df[Y] / df["_series"].map(gmax)
        return df

    @staticmethod
    def raman_bl_norm(df: pd.DataFrame) -> pd.DataFrame:
        """Linear baseline through 1100/1800 cm-1 (±10 cm-1 means) removed, then G max = 1."""
        parts = []
        for stem in sorted(df["_series"].unique()):
            r = H.raman_corrected(stem)
            g = r["y"][(r["x"] >= 1550) & (r["x"] <= 1620)].max()
            parts.append(pd.DataFrame({"_series": stem, "Raman Shift (cm-1)": r["x"],
                                       "정규화 강도": r["y"] / g}))
        return pd.concat(parts, ignore_index=True)

    @staticmethod
    def raman_ratio_table(df: pd.DataFrame, baseline=False) -> pd.DataFrame:
        stems = sorted(df["_series"].unique())
        return pd.DataFrame({"시료": stems, "IG/ID": [H.raman_ratio(s, baseline) for s in stems]})

    @staticmethod
    def tga_residue_table(rl: pd.DataFrame, T=800.0) -> pd.DataFrame:
        sheets = list(sheet_names("data/tga_batches.xlsx"))
        w = [H.tga_w(s, T) for s in sheets]
        out = pd.DataFrame({"런ID": sheets, "TGA 잔량(wt%)": w, "TGA Fe(wt%)": [v * 0.699 for v in w]})
        return out.merge(rl[["런ID", "잔류금속"]], on="런ID", how="left")

    # ---- stats
    @staticmethod
    def linreg(x, y) -> dict:
        x = np.asarray(x, float)
        y = np.asarray(y, float)
        b, a = np.polyfit(x, y, 1)
        r = np.corrcoef(x, y)[0, 1]
        return {"slope": float(b), "intercept": float(a), "r2": float(r * r)}


# --------------------------------------------------------------------------------------
# value computation per chart kind
# --------------------------------------------------------------------------------------

def rnd(v, nd=3):
    if v is None:
        return None
    if isinstance(v, (np.integer,)):
        return int(v)
    if isinstance(v, (float, np.floating)):
        if math.isnan(v):
            return None
        return round(float(v), nd)
    if isinstance(v, (pd.Timestamp, dt.datetime)):
        return pd.Timestamp(v).isoformat(sep=" ")
    if isinstance(v, dt.date):
        return v.isoformat()
    return v


def key(v):
    if isinstance(v, (pd.Timestamp, dt.datetime, dt.date)):
        return rnd(v)
    if isinstance(v, (float, np.floating)):
        f = float(v)
        return f"{f:g}"
    if isinstance(v, (np.integer, int)):
        return str(int(v))
    return str(v)


def _agg(df, x, y, agg, by=None):
    keys = [by, x] if by else x
    g = df.groupby(keys, observed=True, sort=True)
    if agg in (None, "count") or y is None:
        return g.size()
    return g[y].agg(agg)


def _order(s: pd.Series, d: dict) -> pd.Series:
    srt = d.get("sort")
    if srt == "desc":
        s = s.sort_values(ascending=False, kind="mergesort")
    elif srt == "asc":
        s = s.sort_values(ascending=True, kind="mergesort")
    elif isinstance(srt, list):
        s = s.reindex(srt)
    if d.get("top"):
        s = s.head(int(d["top"]))
    return s


def v_bar(df, d, nd):
    s = _agg(df, d["x"], d.get("y"), d.get("agg"))
    s = _order(s, d)
    out = {"order": [key(k) for k in s.index], "values": {key(k): rnd(v, nd) for k, v in s.items()}}
    return out, s


def v_pie(df, d, nd):
    s = _agg(df, d["x"], d.get("y"), d.get("agg"))
    s = _order(s, d)
    tot = s.sum()
    out = {"order": [key(k) for k in s.index], "values": {key(k): rnd(v, nd) for k, v in s.items()},
           "shares_pct": {key(k): rnd(v / tot * 100, 2) for k, v in s.items()}, "total": rnd(tot, nd)}
    return out, s


def v_grouped(df, d, nd):
    x, by, y, agg = d["x"], d["by"], d.get("y"), d.get("agg")
    if by == "_measure":
        p = df.groupby(x, observed=True, sort=True)[list(y)].agg(agg)
    else:
        if agg in (None, "count") or y is None:
            p = df.groupby([x, by], observed=True, sort=True).size().unstack(by)
        else:
            p = df.pivot_table(index=x, columns=by, values=y, aggfunc=agg, observed=True)
    if d.get("fill") is not None:
        p = p.fillna(d["fill"])
        if agg in (None, "count") and by != "_measure":
            p = p.astype(int)
    if d.get("normalize") == "x":
        p = p.div(p.sum(axis=1), axis=0) * 100
    if isinstance(d.get("sort"), list):
        p = p.reindex(d["sort"])
    out = {"x": [key(k) for k in p.index], "series": [key(c) for c in p.columns],
           "values": {key(i): {key(c): rnd(p.loc[i, c], nd) for c in p.columns} for i in p.index}}
    if d.get("_totals"):
        out["totals"] = {key(i): rnd(p.loc[i].sum(), nd) for i in p.index}
    return out, p


def _series_stats(xs, ys, nd, max_points):
    xs = list(xs)
    ys = np.asarray(ys, float)
    st = {"n": int(len(ys)), "x_range": [rnd(min(xs), nd), rnd(max(xs), nd)],
          "y_range": [rnd(np.nanmin(ys), nd), rnd(np.nanmax(ys), nd)]}
    if len(ys) <= max_points:
        st["points"] = [[rnd(a, nd) if not isinstance(a, str) else a, rnd(b, nd)] for a, b in zip(xs, ys)]
    return st


def v_line(df, d, nd):
    x, y, by, agg = d["x"], d.get("y"), d.get("by"), d.get("agg")
    series = {}
    if isinstance(y, (list, tuple)) and by:
        for b, g in df.groupby(by, sort=True, observed=True):
            for c in y:
                sub = g[[x, c]].dropna()
                series[f"{key(b)} {c}"] = (sub[x].tolist(), sub[c].to_numpy())
    elif isinstance(y, (list, tuple)):
        for c in y:
            sub = df[[x, c]].dropna()
            series[c] = (sub[x].tolist(), sub[c].to_numpy())
    elif agg:
        s = _agg(df, x, y, agg, by)
        if by:
            for b in s.index.get_level_values(0).unique():
                ss = s.loc[b]
                series[key(b)] = (list(ss.index), ss.to_numpy())
        else:
            series[d.get("name", y or "count")] = (list(s.index), s.to_numpy())
    elif by:
        for b, sub in df.groupby(by, sort=True, observed=True):
            series[key(b)] = (sub[x].tolist(), sub[y].to_numpy())
    else:
        series[d.get("name", y)] = (df[x].tolist(), df[y].to_numpy())
    roll = d.get("rolling")
    if roll:
        new = {}
        for name, (xs, ys) in series.items():
            if roll.get("keep", True):
                new[name] = (xs, ys)
            r = pd.Series(ys).rolling(roll["window"], min_periods=roll.get("min_periods", roll["window"]),
                                      center=roll.get("center", False)).mean()
            ok = r.notna().to_numpy()
            new[f"{name} {roll.get('label', 'MA')}"] = ([xx for xx, k in zip(xs, ok) if k], r.to_numpy()[ok])
        series = new
    if d.get("cumsum"):
        series = {k: (xs, np.cumsum(ys)) for k, (xs, ys) in series.items()}
    maxp = d.get("max_points", 60)
    out = {"n_series": len(series),
           "series": {k: _series_stats(xs, ys, nd, maxp) for k, (xs, ys) in series.items()}}
    return out, series


def _num(s: pd.Series) -> np.ndarray:
    if pd.api.types.is_datetime64_any_dtype(s):
        return (s - PROD_START).dt.total_seconds().to_numpy() / 86400.0
    return s.to_numpy(float)


def v_scatter(df, d, nd):
    x, y, by = d["x"], d["y"], d.get("by")
    sub = df[[c for c in [x, y, by] if c]].dropna(subset=[x, y])
    out = {"n": int(len(sub)), "x_range": [rnd(sub[x].min(), nd), rnd(sub[x].max(), nd)],
           "y_range": [rnd(sub[y].min(), nd), rnd(sub[y].max(), nd)],
           "pearson_r": rnd(np.corrcoef(_num(sub[x]), _num(sub[y]))[0, 1], 3)}
    if by:
        out["series"] = {key(k): int(v) for k, v in sub.groupby(by, observed=True).size().items()}
    if len(sub) <= d.get("max_points", 30):
        out["points"] = [[rnd(a, nd), rnd(b, nd)] for a, b in zip(sub[x], sub[y])]
    return out, sub


def v_hist(df, d, nd):
    x, by, bins = d["x"], d.get("by"), d.get("bins")
    vals = df[x].dropna().to_numpy(float)
    out = {"n": int(vals.size), "range": [rnd(vals.min(), nd), rnd(vals.max(), nd)]}

    def counts(v):
        if bins is None:
            return None
        if isinstance(bins, int):
            c, e = np.histogram(v, bins=bins, range=(vals.min(), vals.max()))
        else:
            c, e = np.histogram(v, bins=np.asarray(bins, float))
        res = {"edges": [rnd(a, 4) for a in e], "counts": [int(a) for a in c]}
        if d.get("density"):
            w = np.diff(e)
            res["density"] = [rnd(a, 5) for a in c / (c.sum() * w)]
        return res

    if bins is not None and not by:
        out["bins"] = counts(vals)
    if by:
        out["by"] = {}
        for k, sub in df.groupby(by, observed=True, sort=True):
            v = sub[x].dropna().to_numpy(float)
            st = {"n": int(v.size), "range": [rnd(v.min(), nd), rnd(v.max(), nd)]}
            if bins is not None:
                st["bins"] = counts(v)
            out["by"][key(k)] = st
    return out, vals


def v_heatmap(df, d, nd):
    if d.get("corr"):
        p = df[list(d["corr"])].astype(float).corr()
    else:
        rows, cols, val, agg = d["y"], d["x"], d.get("value"), d.get("agg")
        if agg in (None, "count") or val is None:
            p = df.groupby([rows, cols], observed=True, sort=True).size().unstack(cols)
        else:
            p = df.pivot_table(index=rows, columns=cols, values=val, aggfunc=agg, observed=True)
        if d.get("row_order"):
            p = p.reindex(d["row_order"])
        if d.get("col_order"):
            p = p.reindex(columns=d["col_order"])
        if d.get("fill") is not None:
            p = p.fillna(d["fill"])
            if agg in (None, "count") or val is None:
                p = p.astype(int)
    out = {"rows": [key(k) for k in p.index], "cols": [key(c) for c in p.columns],
           "matrix": [[rnd(v, nd) for v in row] for row in p.to_numpy()]}
    return out, p


KINDS = {"bar": v_bar, "hbar": v_bar, "pie": v_pie, "grouped_bar": v_grouped,
         "stacked_bar": v_grouped, "line": v_line, "scatter": v_scatter,
         "histogram": v_hist, "heatmap": v_heatmap}

PUBLIC_DATA_KEYS = ["source", "sheet", "x", "y", "by", "value", "filter", "agg", "sort", "top",
                    "bins", "derive", "normalize", "rolling", "cumsum", "corr", "fill", "density",
                    "note"]


def prepare(d: dict) -> pd.DataFrame:
    df = load(d)
    ctx = {"pd": pd, "np": np, "H": H}
    for col, expr in (d.get("derive") or {}).items():
        df[col] = eval(expr, ctx, {"df": df})
    if d.get("filter"):
        df = df.query(d["filter"], engine="python")
    if d.get("_prep"):
        df = eval(d["_prep"], ctx, {"df": df})
    return df


def compute_turn(t: dict) -> dict:
    kind = t["kind"]
    d = t["data"]
    nd = t.get("nd", 3)
    df = prepare(d)
    values, plot = KINDS[kind](df, d, nd)
    ctx = {"pd": pd, "np": np, "H": H}
    loc = {"df": df, "plot": plot, "values": values}
    if t.get("values_extra"):
        for k, expr in t["values_extra"].items():
            values[k] = _jsonable(eval(expr, ctx, loc), nd)
    asks = []
    for a in t.get("asks", []):
        a = dict(a)
        if "expr" in a:
            a["value"] = _jsonable(eval(a.pop("expr"), ctx, loc), a.pop("nd", nd))
        asks.append(a)
    pub = {k: d[k] for k in PUBLIC_DATA_KEYS if k in d and d[k] is not None}
    exp = {"kind": kind, "data": pub, "values": values, "asks": asks,
           "alternatives": list(t.get("alts", []))}
    if t.get("alt_values"):
        exp["alternative_values"] = {}
        for name, alt in t["alt_values"].items():
            at = dict(t)
            at.update({"kind": alt.get("kind", kind), "data": {**d, **alt.get("data", {})},
                       "asks": [], "values_extra": None, "alt_values": None})
            exp["alternative_values"][name] = compute_turn(at)["values"]
    if t.get("tolerance"):
        exp["tolerance"] = t["tolerance"]
    return exp


def _jsonable(v, nd):
    if isinstance(v, dict):
        return {key(k): _jsonable(x, nd) for k, x in v.items()}
    if isinstance(v, (list, tuple, np.ndarray)):
        return [_jsonable(x, nd) for x in v]
    if isinstance(v, pd.Series):
        return {key(k): _jsonable(x, nd) for k, x in v.items()}
    return rnd(v, nd)


# --------------------------------------------------------------------------------------
# build
# --------------------------------------------------------------------------------------
PREP_TAGS = {"filter", "groupby", "pivot", "binning", "sort", "topN", "daterange", "derive",
             "join", "rolling", "normalize", "cumsum", "corr", "parse"}

META = {
    "world": "한결나노텍(가상) 울산 2공장 CNT 2라인 FC-CVD; data under eval/cnt/data/ (see README.md)",
    "paths": "file paths are relative to eval/cnt/",
    "reading_notes": [
        "run_log.xlsx sheet 런로그: row 1 = headers, row 2 = units -> skip it (pd.read_excel(..., skiprows=[1])).",
        "L3_MES_export_202607.csv: 5 preamble lines, ';' separator, decimal comma, footer line '총 N건'.",
    ],
    "tolerance_default": {
        "counts": "exact",
        "aggregates": "abs <= max(0.5% of |value|, 0.01)",
        "ranges": "abs <= max(0.5% of |value|, 0.05)",
        "shares_pct": "abs <= 0.2 percentage points",
        "computed": "per ask ('tol'); otherwise as aggregates",
        "categories": "same set; order checked only when data.sort is given",
    },
    "value_conventions": {
        "bar/hbar/pie": "values = category -> aggregated value (count when agg is count/None); pie adds shares_pct",
        "grouped_bar/stacked_bar": "values = x category -> {series -> value}",
        "line": "series name -> n, x_range, y_range (+ points when n <= 60)",
        "scatter": "n, x_range, y_range, pearson_r, series counts (+ points when n <= 30)",
        "histogram": "n, range, and bin edges/counts when bins were specified",
        "heatmap": "rows, cols, matrix (row-major)",
        "series names": "series names are descriptive; graders should match by content, not by exact label text",
    },
    "turn_semantics": "for sessions, each turn's expect describes the full plot expected after that turn",
}


def build(split: str) -> dict:
    spec_path = ROOT / split / "request_specs.py"
    ns: dict = {"__file__": str(spec_path)}
    exec(compile(spec_path.read_text(encoding="utf-8"), str(spec_path), "exec"), ns)
    items = []
    for it in ns["ITEMS"]:
        turns = []
        needs_all = set()
        for t in it["turns"]:
            exp = compute_turn(t)
            needs = sorted(set(t.get("needs", [])))
            needs_all |= set(needs)
            turns.append({"text": t["text"], "needs": needs, "expect": exp})
        files = sorted({f for t in it["turns"] for f in _files_of(t["data"]) + list(t.get("extra_files", []))})
        items.append({"id": it["id"], "persona": it["persona"], "split": split,
                      "type": "session" if len(turns) > 1 else "single",
                      "files": files, "turns": turns})
    return {"meta": {**META, "split": split, "personas": ns["PERSONAS"]}, "items": items}


def _files_of(d):
    src = d["source"]
    srcs = [src] if isinstance(src, str) else list(src)
    out = []
    for s in srcs:
        if "*" in s:
            out += sorted(str(Path(p).relative_to(ROOT)) for p in glob.glob(str(ROOT / s)))
        else:
            out.append(s)
    return out


def summarize(doc: dict) -> dict:
    singles = [i for i in doc["items"] if i["type"] == "single"]
    sessions = [i for i in doc["items"] if i["type"] == "session"]
    kinds_single, kinds_all = {}, {}
    flags = {"prep": 0, "computed": 0, "style": 0, "underspecified": 0}
    flags_all = dict(flags)
    nturns = 0
    for it in doc["items"]:
        for t in it["turns"]:
            nturns += 1
            k = t["expect"]["kind"]
            kinds_all[k] = kinds_all.get(k, 0) + 1
            nd = set(t["needs"])
            f = {"prep": bool(nd & PREP_TAGS), "computed": "computed" in nd, "style": "style" in nd,
                 "underspecified": "underspecified" in nd}
            for kk, vv in f.items():
                flags_all[kk] += vv
                if it["type"] == "single":
                    flags[kk] += vv
            if it["type"] == "single":
                kinds_single[k] = kinds_single.get(k, 0) + 1
    return {"singles": len(singles), "sessions": len(sessions), "turns_total": nturns,
            "session_turns": [len(s["turns"]) for s in sessions],
            "kinds_single": kinds_single, "kinds_all_turns": kinds_all,
            "flags_single": flags, "flags_all_turns": flags_all,
            "personas": sorted({i["persona"] for i in doc["items"]})}


def sha_manifest():
    lines = []
    for p in sorted((ROOT / "sealed").rglob("*")):
        if p.is_file() and "__pycache__" not in p.parts:
            h = hashlib.sha256(p.read_bytes()).hexdigest()
            lines.append(f"{h}  {p.relative_to(ROOT).as_posix()}")
    (ROOT / "SEALED.sha256").write_text("\n".join(lines) + "\n", encoding="utf-8")
    return len(lines)


def check() -> int:
    """Recompute every expectation and compare with the written JSON; verify SEALED.sha256 and
    that every referenced data file opens."""
    bad = 0
    for split in ["dev", "sealed"]:
        doc = build(split)
        fresh = json.dumps(doc, ensure_ascii=False, indent=1) + "\n"
        on_disk = (ROOT / split / "requests.json").read_text(encoding="utf-8")
        same = fresh == on_disk
        bad += not same
        files = sorted({f for it in doc["items"] for f in it["files"]})
        for f in files:
            p = ROOT / f
            if f.endswith(".xlsx"):
                pd.ExcelFile(p).sheet_names
            elif "L3_MES" in f:
                read_l3(p)
            else:
                pd.read_csv(p, nrows=5)
        nturn = sum(len(it["turns"]) for it in doc["items"])
        print(f"{split}: {len(doc['items'])} items / {nturn} turns recomputed -> "
              f"{'IDENTICAL to requests.json' if same else 'MISMATCH'}; {len(files)} data files open OK")
    want = {}
    for line in (ROOT / "SEALED.sha256").read_text(encoding="utf-8").splitlines():
        h, f = line.split("  ", 1)
        want[f] = h
    have = {p.relative_to(ROOT).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in (ROOT / "sealed").rglob("*") if p.is_file() and "__pycache__" not in p.parts}
    ok = want == have
    bad += not ok
    print(f"SEALED.sha256: {len(want)} entries, {'OK' if ok else 'MISMATCH'}")
    return bad


def main():
    if "--check" in sys.argv:
        sys.exit(1 if check() else 0)
    splits = sys.argv[1:] or ["dev", "sealed"]
    for split in splits:
        doc = build(split)
        out = ROOT / split / "requests.json"
        out.write_text(json.dumps(doc, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
        print(split, json.dumps(summarize(doc), ensure_ascii=False))
    if "sealed" in splits:
        print("SEALED.sha256 entries:", sha_manifest())


if __name__ == "__main__":
    main()
