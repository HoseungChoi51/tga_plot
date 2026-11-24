"""Evidence for the consolidated report: for one run of one arm on one request, the prompt the model saw, what it
replied, what the checker and the reviewers said, and the plot it drew. Reads the three run layouts:

  TGA batch  eval/results/runs/<run>/<arm>/<rid>_r<rep>/   reply_N.txt, reasoning_N.txt, record.json, out/*.png
  CNT        eval/results/runs/<run>/<arm>/<item>_r<rep>/  record.json (turns), out/t<turn>/*.png
  Pi         eval/results/pi_ws/[luna/]<arm>/<rid>/        session.jsonl, spec.json | plot.py, plots anywhere below
"""
import csv
import json
import re
import sys
from functools import lru_cache
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
EVAL = ROOT / "eval"
RES = EVAL / "results"
sys.path.insert(0, str(EVAL))
sys.path.insert(0, str(ROOT))
csv.field_size_limit(10 ** 8)


@lru_cache(maxsize=None)
def rows(name):
    p = RES / f"{name}.csv"
    return list(csv.DictReader(open(p, encoding="utf-8"))) if p.exists() else []


@lru_cache(maxsize=None)
def tga_requests():
    import run_agent
    from requests_b import REQUESTS
    out = {rid: {"text": t, "file": f, "group": "A"} for rid, _, f, t in run_agent.read_prompts(ROOT / "tests" / "AGENT_TEST_PROMPTS.md")}
    out.update({n.split("_")[0]: {"text": t, "file": ", ".join(fs), "group": g} for n, g, fs, t in REQUESTS})
    return out


@lru_cache(maxsize=None)
def cnt_requests(split="dev"):
    d = json.loads((EVAL / "cnt" / split / "requests.json").read_text(encoding="utf-8"))
    return {i["id"]: i for i in (d["items"] if isinstance(d, dict) else d)}


def _read(p):
    return p.read_text(encoding="utf-8", errors="replace") if p and p.exists() else ""


def pngs(d):
    return sorted(d.rglob("*.png")) if d and d.exists() else []


# =================================================================== TGA batch runs
def tga(run, arm, rid, rep=1):
    """run: CSV name without batch_ (sx, luna, sx_think, sx_reason, luna_reason, t06, ...)."""
    r = next((x for x in rows(f"batch_{run}") if x["arm"] == arm and x["request"] == rid and x["repeat"] == str(rep)), None)
    if r is None:
        return None
    d = EVAL / r["run_dir"]
    if not d.exists():                                   # folders renamed after the run (t0 -> t0_aborted)
        alt = RES / "runs" / run / arm / f"{rid}_r{rep}"
        d = alt if alt.exists() else d
    replies = sorted(d.glob("reply_*.txt"), key=lambda p: int(re.search(r"(\d+)", p.stem).group(1)))
    reasons = sorted(d.glob("reasoning_*.txt"), key=lambda p: int(re.search(r"(\d+)", p.stem).group(1)))
    rec = json.loads(_read(d / "record.json") or "{}")
    req = tga_requests().get(rid, {})
    return {"kind": "tga", "run": run, "arm": arm, "id": rid, "rep": rep, "request": req.get("text", ""),
            "file": req.get("file", ""), "group": r["group"], "row": r, "replies": [_read(p) for p in replies],
            "reasoning": [_read(p) for p in reasons], "final": rec.get("final"), "errors": rec.get("errors") or [],
            "calls": rec.get("calls") or [], "pass": r["pass_all"] == "1", "ok_run": r["ok_run"] == "1",
            "failed": r["failed"], "images": pngs(d / "out"), "dir": d}


# =================================================================== CNT runs
def cnt(run, arm, item, rep=1, turn=1):
    r = next((x for x in rows(f"cnt_{run}") if x["arm"] == arm and x["item"] == item and x["repeat"] == str(rep)
              and x["turn"] == str(turn)), None)
    if r is None:
        return None
    d = EVAL / r["run_dir"]
    rec = json.loads(_read(d / "record.json") or "{}")
    t = (rec.get("turns") or [{}] * turn)[turn - 1] if rec.get("turns") and len(rec["turns"]) >= turn else {}
    calls = [c for c in t.get("calls", []) if c.get("reply") or c.get("error")]
    return {"kind": "cnt", "run": run, "arm": arm, "id": item, "rep": rep, "turn": turn, "request": t.get("text", ""),
            "row": r, "replies": [c.get("reply", "") for c in calls], "spec": t.get("spec"), "pass": r["pass"] == "1",
            "ok_run": r["ok_run"] == "1", "failed": r["failed"] or r.get("error", ""), "images": pngs(d / "out" / f"t{turn}"),
            "dir": d, "kind_of_chart": r.get("kind"), "turns": rec.get("turns") or []}


# =================================================================== Pi sessions
def pi(arm, rid, luna=False):
    r = next((x for x in rows("pi_luna" if luna else "pi") if x["arm"] == arm and x["request"] == rid), None)
    if r is None:
        return None
    rel = r["workspace"].split("eval/results/pi_ws/", 1)[-1]
    d = RES / "pi_ws" / rel
    answer, tools = "", []
    for line in _read(d / "session.jsonl").splitlines():
        try:
            ev = json.loads(line)
        except json.JSONDecodeError:
            continue
        if ev.get("type") == "tool_execution_start":
            a = ev.get("args") or {}
            tools.append(a.get("command") or ("write " + str(a.get("path", ""))) if isinstance(a, dict) else str(a))
        if ev.get("type") == "message_end" and (ev.get("message") or {}).get("role") == "assistant":
            for c in ev["message"].get("content") or []:
                if isinstance(c, dict) and c.get("type") == "text" and c.get("text", "").strip():
                    answer = c["text"].strip()
    spec = next((p for p in sorted(d.rglob("spec*.json")) if "_scored" not in p.parts), None)
    script = next((p for p in sorted(d.rglob("plot.py")) if "_rerun" not in p.parts), None)
    imgs = [p for p in pngs(d) if "_rerun" not in p.parts and "_scored" not in p.parts] or pngs(d / "_scored")
    req = tga_requests().get(rid, {})
    return {"kind": "pi", "arm": arm, "id": rid, "luna": luna, "request": req.get("text", ""), "row": r,
            "answer": answer or r.get("answer", ""), "tools": tools, "spec": _read(spec), "script": _read(script),
            "pass": r["pass_all"] == "1", "failed": r["failed"], "images": imgs, "dir": d}


# =================================================================== reviews
def review(run, rid, arm):
    """Blind-review grade(s) for repeat 1 of a TGA batch run (review_sx.csv, review_luna.csv)."""
    out = [x for x in rows(f"review_{run}") if x["request"] == rid and x["arm"] == arm]
    return [(x["verdict"], x.get("defects", ""), x.get("grader", "")) for x in out]


# =================================================================== excerpts
def excerpt(text, patterns, context=2, limit=24):
    """Lines of `text` around the first matches of the regex patterns, with the matches marked (returns list of
    (line, is_match)); the whole text if it is short."""
    lines = (text or "").splitlines()
    if len(lines) <= limit and not patterns:
        return [(l, False) for l in lines]
    keep, hits = set(), set()
    for i, l in enumerate(lines):
        if any(re.search(p, l) for p in patterns):
            hits.add(i)
            keep.update(range(max(0, i - context), min(len(lines), i + context + 1)))
    if not keep:
        return [(l, False) for l in lines[:limit]]
    out, last = [], -2
    for i in sorted(keep)[: limit * 2]:
        if i != last + 1 and out:
            out.append(("…", False))
        out.append((lines[i], i in hits))
        last = i
    return out[: limit + 6]
