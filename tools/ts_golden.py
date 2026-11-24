"""Golden outputs from the Python plotkit, for the TypeScript port (ts/) to reproduce. Dev-time only.

    python tools/ts_golden.py            -> ts/test/golden/*.json.gz

Every case records what the Python implementation produces at each stage, so a TypeScript module can be tested on
its own: the tables a file reads to, the data preview, the normalized spec (or the error and hint), and for specs
that draw: the curve figures / chart model and the ECharts options, values, warnings and not_done.

Cases: every data file of the repo; the hand-written reference specs (tests/reference_specs.json, Set B, the CNT dev
references, the gallery); and the specs the study's models wrote (CNT turns, TGA replies), file names rebased onto
the data folders. Python runs with the working directory at the data folder, so file names stay relative, as the TS
side receives them ({name, bytes}).

JSON can not carry NaN, infinities or dates: they are written as {"$f": "nan" | "inf" | "-inf"} and
{"$date": "YYYY-MM-DDTHH:MM:SS"}. Arrays of 64 items or more are stored once in "pool" and referenced as
{"$pool": key} (see pooled()).
"""
import contextlib
import datetime as dt
import glob
import gzip
import hashlib
import json
import math
import os
import random
import re
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "experiments" / "eval"))
sys.path.insert(0, str(ROOT / "tools"))
from plotkit import agent, api, charts, core, echarts  # noqa: E402
from plotkit.core import PlotkitError  # noqa: E402

OUT = ROOT / "ts" / "test" / "golden"
BASES = {"tests/inputs": ROOT / "tests" / "inputs", "eval/inputs_b": ROOT / "experiments" / "eval" / "inputs_b",
         "eval/cnt": ROOT / "experiments" / "eval" / "cnt", "gallery": ROOT / "experiments" / "gallery"}
E2E_SAMPLE = 500                   # model-written specs drawn end to end (all reference specs are)


# =================================================================== JSON
def enc(v):
    if isinstance(v, dict):
        return {str(k): enc(x) for k, x in v.items()}
    if isinstance(v, (list, tuple)):
        return [enc(x) for x in v]
    if isinstance(v, np.ndarray):
        return [enc(x) for x in v.tolist()]
    if isinstance(v, (np.bool_,)):
        return bool(v)
    if isinstance(v, np.integer):
        return int(v)
    if isinstance(v, (float, np.floating)):
        v = float(v)
        if math.isnan(v):
            return {"$f": "nan"}
        if math.isinf(v):
            return {"$f": "inf" if v > 0 else "-inf"}
        return v
    if isinstance(v, (dt.datetime, dt.date)) or type(v).__name__ in ("Timestamp",):
        try:
            import pandas as pd
            if v is pd.NaT:
                return None
        except ImportError:
            pass
        return {"$date": v.isoformat()}
    if v is None or isinstance(v, (bool, int, str)):
        return v
    if type(v).__name__ in ("NaTType",):
        return None
    if hasattr(v, "item"):
        return enc(v.item())
    return str(v)


def pooled(obj):
    """Large arrays (data series repeat across cases) are stored once: {"cases": ..., "pool": {key: array}}, and
    each occurrence becomes {"$pool": key}."""
    pool = {}

    def walk(v):
        if isinstance(v, dict):
            return {k: walk(x) for k, x in v.items()}
        if isinstance(v, list):
            v = [walk(x) for x in v]
            if len(v) >= 64:
                key = hashlib.sha1(json.dumps(v, separators=(",", ":"), ensure_ascii=False).encode()).hexdigest()[:16]
                pool.setdefault(key, v)
                return {"$pool": key}
        return v
    return {"cases": [walk(c) for c in obj], "pool": pool}      # the case list itself is not pooled


def write(name, obj):
    OUT.mkdir(parents=True, exist_ok=True)
    data = json.dumps(pooled(enc(obj)), ensure_ascii=False, separators=(",", ":"), allow_nan=False).encode("utf-8")
    with open(OUT / f"{name}.json.gz", "wb") as raw, gzip.GzipFile(fileobj=raw, mode="wb", compresslevel=9, mtime=0) as fh:
        fh.write(data)                                   # mtime 0: the same data gives the same file
    print(f"{name}: {len(data) / 1e6:.1f} MB raw")


@contextlib.contextmanager
def cwd(p):
    old = os.getcwd()
    os.chdir(p)
    try:
        yield
    finally:
        os.chdir(old)


def err(e):
    return {"error": e.message, "hint": e.hint}


# =================================================================== files
def data_files():
    out = []
    for key, base in BASES.items():
        sub = base / "data" if key in ("eval/cnt", "gallery") else base
        for p in sorted(sub.rglob("*")):
            if p.is_file() and p.suffix.lower() in (".xlsx", ".xlsm", ".xls", ".csv", ".txt", ".tsv", ".dat"):
                out.append((key, p.relative_to(base).as_posix()))
    return out


def reader_cases():
    cases = []
    for key, name in data_files():
        c = {"base": key, "name": name}
        with cwd(BASES[key]):
            try:
                tabs, dec = core.read_tables(name)
                c["tables"] = tabs
                c["decimal"] = dec
            except PlotkitError as e:
                c["tables_error"] = err(e)
            try:
                c["preview"] = charts.preview(name)
            except PlotkitError as e:
                c["preview_error"] = err(e)
            c["preview_text"] = agent.preview([name])
        cases.append(c)
    return cases


# =================================================================== specs
def rebase(spec, base=None):
    """(base key, spec with file names relative to it) or None. Accepts old absolute paths from the study's machines.
    base: the data folder when the caller knows it (the gallery's specs name data/... under experiments/gallery)."""
    if base is not None:
        return base, spec
    f = spec.get("file") if isinstance(spec, dict) else None
    if f is None:
        for k in ("files", "path", "input", "file_name", "filename"):
            if isinstance(spec, dict) and k in spec:
                f = spec[k]
                break
    if f is None:
        return None
    files = f if isinstance(f, list) else [f]
    keys, names = set(), []
    for x in files:
        x = str(x).replace("\\", "/")
        hit = None
        for key, marker in (("tests/inputs", "tests/inputs/"), ("eval/inputs_b", "eval/inputs_b/"),
                            ("gallery", "gallery/"), ("eval/cnt", "eval/cnt/")):
            if marker in x:
                hit = (key, x.split(marker, 1)[1])
                break
        if hit is None and (x.startswith("data/") or "/" not in x):
            hit = ("eval/cnt", x) if x.startswith("data/") else None
        if hit is None:
            return None
        keys.add(hit[0])
        names.append(hit[1])
    if len(keys) != 1:
        return None
    key = keys.pop()
    s = dict(spec)
    for k in ("file", "files", "path", "input", "file_name", "filename"):
        if k in s:
            s[k] = names if isinstance(s[k], list) else names[0]
            break
    if isinstance(s.get("output"), dict) and "dir" in s["output"]:
        s["output"] = {k: v for k, v in s["output"].items() if k != "dir"}
    return key, s


def reference_specs():
    out = []
    ref = json.loads((ROOT / "tests" / "reference_specs.json").read_text(encoding="utf-8"))
    out += [(f"A {k}", v) for k, v in ref.items() if not k.startswith("_") and isinstance(v, dict)]
    refb = json.loads((ROOT / "experiments" / "eval" / "reference_b.json").read_text(encoding="utf-8"))
    out += [(f"B {k}", v) for k, v in refb.items() if not k.startswith("_") and isinstance(v, dict)]
    from cnt_dev_refs import REFS
    out += [(f"CNT {k}", v) for k, v in REFS.items()]
    for p in sorted((ROOT / "experiments" / "gallery" / "specs").glob("*.json")):
        out.append((f"G {p.stem[:2]}", json.loads(p.read_text(encoding="utf-8")), "gallery"))
    import ts_extra                                   # chart paths the study's specs never reach
    out += [(f"X {i:02d}", s_, "eval/cnt") for i, s_ in enumerate(ts_extra.CHART_X)]
    out += [(f"Y {i:02d}", s_, "tests/inputs") for i, s_ in enumerate(ts_extra.CHART_Y)]
    out += [(f"Z {i:02d}", s_, "eval/cnt") for i, s_ in enumerate(ts_extra.CHART_Z)]
    return out


def model_specs():
    seen, out = set(), []
    for p in sorted(glob.glob(str(ROOT / "experiments/eval/results/runs/**/record.json"), recursive=True)):
        try:
            rec = json.loads(Path(p).read_text(encoding="utf-8"))
        except Exception:  # noqa: BLE001
            continue
        if not str(rec.get("arm", "")).startswith("P-"):
            continue
        cand = []
        if rec.get("turns"):
            cand = [t.get("spec") for t in rec["turns"]]
        else:
            for r in sorted(Path(p).parent.glob("reply_*.txt")):
                try:
                    cand.append(agent.parse_reply(r.read_text(encoding="utf-8")))
                except PlotkitError:
                    pass
            cand.append(rec.get("final"))
        for s in cand:
            if not isinstance(s, dict):
                continue
            k = json.dumps(s, sort_keys=True, ensure_ascii=False)
            if k in seen:
                continue
            seen.add(k)
            out.append((f"M {hashlib.sha1(k.encode()).hexdigest()[:10]}", s))
    return out


def spec_case(cid, spec, base=None):
    rb = rebase(spec, base)
    if rb is None:
        return None
    key, s = rb
    chart = charts.is_chart_spec(s)
    c = {"id": cid, "base": key, "spec": s, "kind": "chart" if chart else "curve"}
    with cwd(BASES[key]):
        try:
            norm = charts.normalize(s) if chart else core.normalize_spec(s)
            c["normalized"] = api._clean(norm)
            c["normalized_full"] = norm                  # with plotkit's internal "_" keys, for the stage tests
        except PlotkitError as e:
            c["normalize_error"] = err(e)
        except Exception as e:  # noqa: BLE001
            c["normalize_crash"] = f"{type(e).__name__}: {e}"
    return c


def frame_json(df):
    """A loaded chart table: column names, pandas dtypes, values (dates as $date), and the column letters."""
    cols = [str(c) for c in df.columns]
    return {"columns": cols, "dtypes": [str(t) for t in df.dtypes],
            "data": {c: [None if (v is None or (isinstance(v, float) and v != v)) else v for v in df[c].tolist()]
                     for c in cols},
            "letters": dict(df.attrs.get("letters", {}))}


SVG_IDS = {"A 01", "A 02", "A 09", "A 12", "A 20", "B B02_heat_flow_peaks", "G 03", "G 19", "CNT D001.1", "CNT D010.1",
           "CNT D018.1", "CNT DS02.1", "X 05", "X 18", "X 24", "X 37", "X 54", "X 61", "X 70", "Y 05", "Y 20", "Y 25", "Y 36"}


def draw_case(c):
    """End to end on the ECharts engine, plus the stage outputs."""
    s = c["spec"]
    if s.get("data_code") or s.get("code") or "normalized" not in c:
        return c
    with cwd(BASES[c["base"]]):
        try:
            kind, routed = core.route(s)
            c["route"] = kind
            if kind == "chart":
                norm = charts.normalize(routed)
                c["norm_full"] = norm
                frame = charts.load_frame(norm)
                c["frame"] = frame_json(frame)
                model = charts.layout(norm, charts.build_model(norm, frame))
                c["model"] = {k: v for k, v in model.items() if k != "df"}
                opt, (w, h) = charts.echarts_option(norm, model)
                c["static_option"], c["size_px"] = opt, [w, h]
                if routed is not s:
                    c["routed_spec"] = routed
            else:
                norm = core.normalize_spec(routed)
                c["norm_full"] = norm
                jobs, warnings = core.build_jobs(norm)
                c["job_warnings"] = warnings
                c["jobs"] = [{k: v for k, v in j.items() if k != "cols"} | {"cols": {r: {kk: vv for kk, vv in col.items()
                              if kk != "values"} for r, col in j["cols"].items()}} for j in jobs]
                c["figures"] = [{"figure": f, "annotations": a} for _, f, a in echarts.resolve(norm, jobs)]
            res = api.echarts_options(s, full=True)
            c["result"] = res
            if c["id"] in SVG_IDS:
                import tempfile
                with tempfile.TemporaryDirectory() as td:
                    r = api.render(s, td, formats=("svg",))
                    c["svg"] = [Path(f).read_text(encoding="utf-8") for f in r["saved"]]
        except PlotkitError as e:
            c["draw_error"] = err(e)
        except Exception as e:  # noqa: BLE001 - a Python bug: the TS port must answer a PlotkitError here
            c["draw_crash"] = f"{type(e).__name__}: {e}"
    return c


def basics():
    """Vectors for the foundations: Python number formatting, repr, round, difflib, colours, ticks."""
    import difflib
    from matplotlib.ticker import MaxNLocator
    from plotkit import colors
    rng = random.Random(3)
    vals = [0.0, -0.0, 0.5, 1.5, 2.5, 0.125, 0.375, 1e16, 1e15, 123456789.0, 1e-5, 1e-4, 0.0001234, 599.0, 8.0117,
            -3.14159, 1 / 3, 2 / 3, 99.95, 0.05, 1234.5678, 7.0, 1e300, 5e-324, 1.0254, 0.1 + 0.2]
    vals += [rng.uniform(-1, 1) * 10 ** rng.randint(-8, 12) for _ in range(300)]
    vals += [round(rng.uniform(0, 1000), rng.randint(0, 3)) + rng.choice([0, 0.5, 0.05, 0.005]) for _ in range(200)]
    specs = [".0f", ".1f", ".2f", ".3f", ".4f", ".6f", "f", ".4g", ".3g", "g", ".10g", ".1g", ".2g", "e", ".2e", ".1%",
             ",.0f", ",.2f", "", ".3", "+.1f", "8.2f", "<8.1f", "^9.2f", "08.2f", ".0%", "G", "E"]
    fmt = [[v, sp, format(v, sp)] for v in vals for sp in specs]
    ints = [[v, sp, format(v, sp)] for v in (0, 5, -12, 1234567, 10 ** 12) for sp in ("", "d", ",", ".2f", ",d", "5d", ".1%")]
    reprs = [[v, repr(v)] for v in vals]
    rounds = [[v, k, round(v, k)] for v in vals if abs(v) < 1e15 for k in (0, 1, 2, 3, 4, 10)]
    words = sorted(set(list(core.DEFAULTS) + list(core.TOP_ALIASES) + list(core.AXIS_ALIASES) + list(charts.TOP_KEYS)
                       + list(core.DEFAULTS["y1"]) + ["연도", "반응기", "CNT수율", "잔류금속"]))
    probes = []
    for w in words[:200]:
        m = list(w)
        if len(m) > 2:
            m[rng.randrange(len(m))] = rng.choice("aeiouxyz_가")
        probes.append("".join(m))
    close = [[w, poss, n_, c, difflib.get_close_matches(w, poss, n=n_, cutoff=c)]
             for w in probes for poss, n_, c in ((list(core.DEFAULTS), 1, 0.5), (sorted(charts.TOP_KEYS), 3, 0.6),
                                                 (words, 3, 0.5))]
    ratios = [[a, b, difflib.SequenceMatcher(None, a, b).ratio()] for a, b in zip(probes, words[:200])]
    cnames = ["navy", "Red", "tab:blue", "C3", "C12", "0.5", "#abc", "#aabbcc", "#abcd", "#aabbccdd", "xkcd:sky blue", "grey",
              "none", "r", "g", "1", "0", "nope", "#12", "1.5", "빨강"]
    cols = [[c, colors.is_color_like(c), colors.to_hex(c) if colors.is_color_like(c) else None] for c in cnames]
    ticks = []
    for _ in range(1500):
        a = rng.choice([1e-6, 1e-3, 1, 10, 100, 1e4, 1e7]) * rng.gauss(0, 1)
        w = abs(rng.choice([1e-9, 1e-4, 0.1, 1, 50, 1e3, 1e6]) * rng.random())
        for nb in ("auto", 4, 6, 7, 10):
            ticks.append([a, a + w, nb, MaxNLocator(nbins=nb, steps=[1, 2, 2.5, 5, 10]).tick_values(a, a + w).tolist()])
    return [{"format": fmt, "format_int": ints, "repr": reprs, "round": rounds, "close": close, "ratio": ratios, "colors": cols,
             "ticks": ticks}]


def main():
    random.seed(7)
    write("basics", basics())
    if "--basics" in sys.argv:
        return
    write("reader", reader_cases())
    refs = [x for x in (spec_case(*r) for r in reference_specs()) if x]
    models = [x for x in (spec_case(i, s) for i, s in model_specs()) if x]
    print(f"{len(refs)} reference specs, {len(models)} model specs")
    write("specs", refs + models)
    drawable = [m for m in models if "normalized" in m and not m["spec"].get("data_code") and not m["spec"].get("code")]
    errors = [m for m in models if "normalize_error" in m]
    sample = random.sample(drawable, min(E2E_SAMPLE, len(drawable)))
    e2e = [draw_case(c) for c in refs + sample]
    write("draw_curves", [c for c in e2e if c["kind"] == "curve" or c.get("route") == "curve"])
    write("draw_charts", [c for c in e2e if c.get("route") == "chart" or (c["kind"] == "chart" and "route" not in c)])
    print(f"{len(errors)} model specs fail normalization; {len(e2e)} drawn end to end")


if __name__ == "__main__":
    main()
