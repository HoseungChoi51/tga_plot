"""Score one agent answer (a spec) against tests/expected_requests.json, for the engine experiment.

After each request in a Pi session (the agent saved its last spec as spec.json):
    python experiments/tests/score.py --arm S --request 07 --seconds 41 --calls 2
        arm 0 = matplotlib + AGENT.md, arm S = ECharts + AGENT_ECHARTS.md (engine follows the arm)
        appends a row to results/arm<ARM>.csv and keeps the spec in results/specs/<ARM>_<request>.json

Check the harness itself (no model): every hand-written reference spec must pass on both engines:
    python experiments/tests/score.py --reference                 (both engines, all 24)
    python experiments/tests/score.py --reference --engine echarts --request 15

Check types in expected_requests.json:
    {"spec": "x.step", "eq": 200}                 value in the normalized spec (numbers compared to 1e-6)
    {"spec": "title.color", "color": "navy"}      same colour, any spelling (navy, #000080, 남색)
    {"sheets": [...]}                             exactly these sheets were plotted
    {"columns": {"x": "B"}}                       column letters used, on every plotted sheet
    {"combined": true}                            all sheets in one figure
    {"annotation": "peak", "present": false}      label in the result (or not)
    {"annotation": "residue", "x_used": 700, "text_regex": "..."}   and its value / text
    {"annotation": "peak", "count": 1}            number of peaks labelled
    {"annotation_type": "vline", "x": 450, "text_contains": "..."}  an annotation of that type in the spec
    {"shade": [300, 450]}                         a band (or echarts markArea, or code axvspan) over that range
    {"formats": ["pdf", "png"]}                   these files were written for every plot
    {"png_px": [4800, 3000]}                      the PNG size in pixels
"""
import argparse
import csv
import json
import re
import struct
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent          # experiments/
REPO = ROOT.parent                                     # the library
sys.path.insert(0, str(REPO))
from plotkit import core as plotkit  # noqa: E402

EXPECTED = json.loads((ROOT / "tests" / "expected_requests.json").read_text(encoding="utf-8"))
REFERENCE = json.loads((REPO / "tests" / "reference_specs.json").read_text(encoding="utf-8"))
RESULTS = ROOT / "results"
ARM_ENGINE = {"0": "matplotlib", "S": "echarts", "E": "echarts"}


def _get(d, path):
    for part in path.split("."):
        if not isinstance(d, dict) or part not in d:
            return None
        d = d[part]
    return d


def _same(a, b):
    if isinstance(a, (int, float)) and isinstance(b, (int, float)) and not isinstance(a, bool) and not isinstance(b, bool):
        return abs(a - b) <= 1e-6 * max(1, abs(b))
    if isinstance(a, (list, tuple)) and isinstance(b, (list, tuple)):
        return len(a) == len(b) and all(_same(x, y) for x, y in zip(a, b))
    return a == b


def _hex(c):
    from matplotlib.colors import to_hex
    try:
        return to_hex(plotkit.KOREAN_COLORS.get(str(c), c))
    except (ValueError, TypeError):
        return None


def _png_size(path):
    with open(path, "rb") as fh:
        head = fh.read(24)
    return list(struct.unpack(">II", head[16:24]))


def _annotations(result, name):
    return [a for p in result["plots"] for a in p["annotations"] if a.get("name") == name]


def _shaded(spec, lo, hi):
    for a in spec["annotate"].values():
        if a.get("type") == "band" and _same(a.get("x_min"), lo) and _same(a.get("x_max"), hi):
            return True
    patch = json.dumps(spec.get("echarts") or {})
    if "markArea" in patch and re.search(rf"\b{lo:g}\b", patch) and re.search(rf"\b{hi:g}\b", patch):
        return True
    code = spec.get("code") or ""
    return "axvspan" in code and re.search(rf"\b{lo:g}\b", code) is not None and re.search(rf"\b{hi:g}\b", code) is not None


def check(c, spec, result):
    """None if the check holds, else a short reason."""
    if "spec" in c:
        got = _get(spec, c["spec"])
        if "color" in c:
            return None if got is not None and _hex(got) == _hex(c["color"]) else f'{c["spec"]} = {got!r}, want {c["color"]}'
        return None if _same(got, c["eq"]) else f'{c["spec"]} = {got!r}, want {c["eq"]!r}'
    if "sheets" in c:
        got = sorted({s for p in result["plots"] for s in p["columns_used"]})
        return None if got == sorted(c["sheets"]) else f"plotted sheets {got}, want {sorted(c['sheets'])}"
    if "columns" in c:
        for p in result["plots"]:
            for sheet, used in p["columns_used"].items():
                for role, letter in c["columns"].items():
                    got = (used.get(role) or "").split(" ")[0]
                    if got != letter:
                        return f"{sheet}: {role} column {got or 'none'}, want {letter}"
        return None
    if "combined" in c:
        got = len(result["plots"]) == 1 and result["plots"][0]["sheet"] == "all"
        return None if got == c["combined"] else f"combined = {got}"
    if "annotation" in c:
        anns = _annotations(result, c["annotation"])
        shown = [a for a in anns if a.get("value") is not None or a.get("peaks")]
        if "present" in c and bool(shown) != c["present"]:
            return f'{c["annotation"]} label {"missing" if c["present"] else "still shown"}'
        if not shown and any(k in c for k in ("x_used", "text_regex", "count")):
            return f'{c["annotation"]} label missing'
        for a in shown:
            if "x_used" in c and not _same(a.get("x_used"), c["x_used"]):
                return f'{c["annotation"]} at x = {a.get("x_used")}, want {c["x_used"]}'
            if "text_regex" in c and not re.search(c["text_regex"], a.get("text", "")):
                return f'{c["annotation"]} text {a.get("text")!r} does not match {c["text_regex"]!r}'
            if "count" in c and len(a.get("peaks", [])) != c["count"]:
                return f'{c["annotation"]}: {len(a.get("peaks", []))} labelled, want {c["count"]}'
        return None
    if "annotation_type" in c:
        for a in spec["annotate"].values():
            if a.get("type") != c["annotation_type"]:
                continue
            if "x" in c and not _same(a.get("x"), c["x"]):
                continue
            if "text_contains" in c and c["text_contains"] not in (a.get("text") or ""):
                continue
            return None
        return f'no {c["annotation_type"]} matching {c}'
    if "shade" in c:
        return None if _shaded(spec, *c["shade"]) else f"no shading over {c['shade'][0]}..{c['shade'][1]}"
    if "formats" in c:
        for p in result["plots"]:
            exts = sorted({Path(s).suffix.lstrip(".") for s in p["saved"] if Path(s).exists()})
            if exts != sorted(c["formats"]):
                return f"{p['sheet']}: wrote {exts}, want {sorted(c['formats'])}"
        return None
    if "png_px" in c:
        for p in result["plots"]:
            for s in p["saved"]:
                if s.endswith(".png") and _png_size(s) != c["png_px"]:
                    return f"{Path(s).name} is {_png_size(s)} px, want {c['png_px']}"
        return None
    return f"unknown check {c}"


def score(request, spec, engine, outdir):
    """Run plotkit on the spec and check it. Returns (passed, [reasons], result or None)."""
    exp = EXPECTED[request]
    s = json.loads(json.dumps(spec, ensure_ascii=False))
    if isinstance(s, dict):
        s.setdefault("output", {})
        if isinstance(s["output"], dict):
            s["output"] = {**s["output"], "dir": str(outdir)}
    try:
        norm = plotkit.normalize_spec(s)
        result = plotkit.plot(s, engine=engine)
    except plotkit.PlotkitError as e:
        return False, [f"plotkit error: {e.message} | {e.hint}"], None
    reasons = [r for r in (check(c, norm, result) for c in exp["checks"]) if r]
    files = [Path(f).name for f in norm["file"]]
    if Path(exp["file"]).name not in files:
        reasons.insert(0, f"file {files}, want {Path(exp['file']).name}")
    return not reasons, reasons, result


def append_row(arm, row):
    RESULTS.mkdir(exist_ok=True)
    path = RESULTS / f"arm{arm}.csv"
    new = not path.exists()
    with open(path, "a", newline="", encoding="utf-8-sig") as fh:
        w = csv.DictWriter(fh, fieldnames=list(row))
        if new:
            w.writeheader()
        w.writerow(row)
    return path


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--arm", choices=list(ARM_ENGINE), help="0 (matplotlib) or S (ECharts)")
    ap.add_argument("--request", help="request number, e.g. 07")
    ap.add_argument("--spec", default="spec.json", help="the spec the agent wrote (default spec.json)")
    ap.add_argument("--engine", choices=plotkit.ENGINES, help="override the arm's engine")
    ap.add_argument("--seconds", type=float, help="wall time of the request, as you timed it")
    ap.add_argument("--calls", type=int, help="number of plot runs the agent made")
    ap.add_argument("--tokens", help="tokens, if the agent shows them")
    ap.add_argument("--note", default="")
    ap.add_argument("--reference", action="store_true", help="check the hand-written reference specs (no model)")
    a = ap.parse_args()
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    if a.reference:
        engines = [a.engine] if a.engine else list(plotkit.ENGINES)
        reqs = [a.request.zfill(2)] if a.request else [k for k in EXPECTED if not k.startswith("_")]
        fails = 0
        for eng in engines:
            for r in reqs:
                spec = REFERENCE.get(f"{r}@{eng}", REFERENCE[r])
                t0 = time.time()
                ok, why, _ = score(r, spec, eng, RESULTS / "reference" / eng / r)
                fails += not ok
                print(f"{'ok  ' if ok else 'FAIL'} {eng:10s} {r}  {time.time() - t0:5.1f}s  {'; '.join(why)}")
        print("\nALL PASSED" if not fails else f"\n{fails} FAILED")
        sys.exit(1 if fails else 0)

    if not (a.arm and a.request):
        ap.error("--arm and --request are needed (or --reference)")
    r = a.request.zfill(2)
    if r not in EXPECTED:
        ap.error(f"unknown request {r}")
    spec_path = Path(a.spec)
    spec = json.loads(spec_path.read_text(encoding="utf-8-sig"))
    engine = a.engine or ARM_ENGINE[a.arm]
    ok, why, _ = score(r, spec, engine, RESULTS / "out" / a.arm / r)
    (RESULTS / "specs").mkdir(parents=True, exist_ok=True)
    (RESULTS / "specs" / f"{a.arm}_{r}.json").write_text(json.dumps(spec, ensure_ascii=False, indent=1), encoding="utf-8")
    row = {"time": time.strftime("%Y-%m-%d %H:%M"), "arm": a.arm, "engine": engine, "request": r, "pass": int(ok),
           "first_try": int(ok and a.calls == 1) if a.calls is not None else "", "plot_calls": a.calls or "",
           "seconds": a.seconds or "", "tokens": a.tokens or "", "failed_checks": " | ".join(why), "note": a.note}
    path = append_row(a.arm, row)
    print(("PASS" if ok else "FAIL") + f"  arm {a.arm} request {r} ({engine})" + ("" if ok else ":\n  - " + "\n  - ".join(why)))
    print(f"recorded in {path.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
