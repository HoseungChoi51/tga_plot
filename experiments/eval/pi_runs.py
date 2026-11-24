"""Agent sessions in Pi: the model runs the tools itself (inspect, write spec.json / plot.py, plot, fix, answer).

    python experiments/eval/pi_runs.py                     12 requests x 3 arms -> eval/results/pi.csv
    python experiments/eval/pi_runs.py --only 02,B15 --arms P-ec
    python experiments/eval/pi_runs.py --name luna --pi-model centinels/gpt-6-luna --thinking off

Each session runs in a fresh workspace that holds only what the arm needs (no tests, answers or results):
  P-mpl / P-ec   plotkit.py, plotkit_echarts.py, echartkit/, guide/, AGENT*.md, the data file(s)
  R-mpl-brief    the data file(s) only
Afterwards the saved spec.json (P) or plot.py (R) is drawn again with the facts hook and scored like the batch.
"""
import argparse
import csv
import json
import os
import shutil
import subprocess
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent                     # experiments/
REPO = ROOT.parent                     # the library (plotkit, tests/inputs, prompts, echartkit, .venv)
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(HERE))
import paths  # noqa: E402
import arms  # noqa: E402
import check  # noqa: E402
import facts  # noqa: E402

PI_REQUESTS = ["02", "09", "12", "15", "20", "23", "B02", "B06", "B11", "B15", "B18", "B21"]
PI_ARMS = ["P-mpl", "P-ec", "R-mpl-brief"]
SCORE_LOCK = threading.Lock()       # the matplotlib facts hook is global: score one session at a time
WS_ROOT = Path(os.environ.get("EVAL_PI_WS", HERE / "results" / "pi_ws"))

RAW_AGENT = """You make plots of lab data with matplotlib for a lab team. Users write in Korean.
Work in the current folder:
1. Look at the data file(s) named in the request (they are under the current folder).
2. Write a Python script `plot.py` that reads the data and saves the figure file(s) into the folder `out/`
   (PNG at 300 dpi unless the user asks for something else; do not call plt.show()).
3. Run it with `python plot.py`, fix it until it works, and check the result.
4. Answer in Korean: the saved file path(s), the values you labelled, and anything you could not do.
""" + arms.ENV_LINE + arms.BRIEF


def build_ws(arm, req, ws):
    shutil.rmtree(ws, ignore_errors=True)
    (ws / "bin").mkdir(parents=True)
    for n in ("python", "python3"):          # a wrapper, not a symlink: a symlinked venv python loses the venv
        w = ws / "bin" / n
        w.write_text(f'#!/bin/sh\nexec "{arms.PY}" "$@"\n')
        w.chmod(0o755)
    for f in req["files"]:
        rel = paths.short(f)
        (ws / rel).parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(f, ws / rel)
    if arm.startswith("P-"):
        for f in ("plotkit.py", "plotkit_echarts.py", "AGENT.md", "AGENT_ECHARTS.md"):
            shutil.copy2((REPO if f.endswith(".py") else ROOT) / f, ws / f)
        (ws / "guide").mkdir()
        shutil.copy2(ROOT / "guide" / "guide_ko.png", ws / "guide" / "guide_ko.png")
        (ws / "echartkit").mkdir()
        for f in ("render.mjs", "translate.mjs", "dump.mjs", "package.json"):
            shutil.copy2(REPO / "echartkit" / f, ws / "echartkit" / f)
        (ws / "echartkit" / "node_modules").symlink_to(REPO / "echartkit" / "node_modules")


def prompt_for(arm):
    if arm == "P-mpl":
        return (ROOT / "AGENT.md").read_text(encoding="utf-8")
    if arm == "P-ec":
        return (ROOT / "AGENT_ECHARTS.md").read_text(encoding="utf-8")
    return RAW_AGENT


def summarize_log(path):
    tools, bash, texts, usage = 0, [], [], {"input": 0, "output": 0}
    for line in open(path, encoding="utf-8", errors="replace"):
        try:
            ev = json.loads(line)
        except json.JSONDecodeError:
            continue
        t = ev.get("type")
        if t == "tool_execution_start":
            tools += 1
            args = ev.get("args") or {}
            if isinstance(args, dict) and args.get("command"):
                bash.append(str(args["command"])[:200])
        if t == "message_end":
            msg = ev.get("message") or {}
            u = msg.get("usage") or {}
            usage["input"] += u.get("input") or u.get("input_tokens") or 0
            usage["output"] += u.get("output") or u.get("output_tokens") or 0
            if msg.get("role") == "assistant":
                for c in msg.get("content") or []:
                    if isinstance(c, dict) and c.get("type") == "text" and c.get("text", "").strip():
                        texts.append(c["text"].strip())
    return {"tool_calls": tools, "bash": bash, "answer": texts[-1] if texts else "", "usage": usage}


def score_ws(arm, req, ws, E):
    """Draw the session's final spec/script again with the facts hook; (ok_run, figs, note)."""
    if arm.startswith("P-"):
        specs = sorted(ws.rglob("spec*.json"), key=lambda p: p.stat().st_mtime)
        if not specs:
            return False, [], "no spec.json saved"
        spec = json.loads(specs[-1].read_text(encoding="utf-8"))
        f = spec.get("file")
        fix = lambda v: str((ws / v) if not Path(v).is_absolute() else v)  # noqa: E731
        spec["file"] = [fix(v) for v in f] if isinstance(f, list) else fix(f or req["files"][0])
        spec["output"] = {**(spec.get("output") or {}), "dir": str(ws / "_scored")}
        try:
            _, figs = facts.plotkit_facts(spec, "matplotlib" if arm == "P-mpl" else "echarts", ws / "_dump.json")
            return True, figs, specs[-1].name
        except Exception as e:
            return False, [], f"spec fails: {e!r}"[:300]
    scripts = sorted([p for p in ws.rglob("*.py") if "_rerun" not in p.parts], key=lambda p: p.stat().st_mtime)
    if not scripts:
        return False, [], "no script saved"
    rerun = ws / "_rerun"
    shutil.rmtree(rerun, ignore_errors=True)
    shutil.copytree(ws, rerun, ignore=shutil.ignore_patterns("_rerun", "bin", "*.jsonl", "out"), symlinks=True)
    script = next((p for p in scripts if p.name == "plot.py"), scripts[-1])
    figs, err = arms.run_mpl_script(script.read_text(encoding="utf-8"), rerun)
    return figs is not None, figs or [], err or script.name


PI_MODEL = "strixhalo/qwen3.8-flash-next"     # a provider/model in ~/.pi/agent/models.json (see HANDOFF.md)
PI_THINKING = "off"


def one(arm, req, E, timeout):
    ws = WS_ROOT / arm / req["id"]
    msg = "파일: " + ", ".join(str(paths.short(f)) for f in req["files"]) + "\n" + req["text"]
    cmd = ["pi", "-p", "--model", PI_MODEL, "--thinking", PI_THINKING, "--no-session", "--mode", "json", "--no-extensions",
           "--no-skills", "--no-context-files", "--no-prompt-templates", "--no-mcp",
           "--append-system-prompt", prompt_for(arm), msg]
    for refused in range(arms.PI_REFUSAL_RETRIES + 1):   # a session the proxy's filter refused starts again from scratch
        build_ws(arm, req, ws)
        env = {**os.environ, "PATH": f"{ws / 'bin'}:{os.environ.get('PATH', '')}"}
        if arm == "P-ec":
            env["PLOTKIT_ENGINE"] = "echarts"
        t0 = time.time()
        with open(ws / "session.jsonl", "w") as out, open(ws / "stderr.txt", "w") as err:
            try:
                rc = subprocess.run(cmd, cwd=ws, env=env, stdin=subprocess.DEVNULL, stdout=out, stderr=err,
                                    timeout=timeout).returncode
            except subprocess.TimeoutExpired:
                rc = "timeout"
        secs = round(time.time() - t0, 1)
        if arms.PI_REFUSED not in (ws / "session.jsonl").read_text(encoding="utf-8", errors="replace"):
            break
        time.sleep(min(3 * (refused + 1), 15))
    log = summarize_log(ws / "session.jsonl")
    with SCORE_LOCK:
        ok_run, figs, note = score_ws(arm, req, ws, E)
        ok, res = check.run_checks(figs, E[req["id"]]) if ok_run else (False, [])
    cats = lambda cs: all(r["ok"] for r in res if r["cat"] in cs)  # noqa: E731
    return {"arm": arm, "request": req["id"], "set": req["set"], "group": req["group"], "rc": rc, "refused": refused, "seconds": secs,
            "ok_run": int(ok_run), "pass_all": int(ok), "pass_ask": int(ok_run and cats(("data", "ask"))),
            "tool_calls": log["tool_calls"], "plot_runs": sum(("plot" in b) for b in log["bash"]),
            "input_tokens": log["usage"]["input"], "output_tokens": log["usage"]["output"], "note": note,
            "failed": " | ".join(f"[{r['cat']}] {r['check']}: {r['why']}" for r in res if not r["ok"])[:800],
            "answer": log["answer"][:600].replace("\n", " "), "workspace": str(ws)}


def main():
    from run_batch import requests
    ap = argparse.ArgumentParser()
    ap.add_argument("--only")
    ap.add_argument("--arms", default=",".join(PI_ARMS))
    ap.add_argument("--workers", type=int, default=4)
    ap.add_argument("--timeout", type=int, default=3600)
    ap.add_argument("--pi-model", default=PI_MODEL)
    ap.add_argument("--thinking", default=PI_THINKING)
    ap.add_argument("--name", default="", help="another model's sessions: results/pi_<name>.csv, workspaces in pi_ws/<name>/")
    a = ap.parse_args()
    globals()["PI_MODEL"], globals()["PI_THINKING"] = a.pi_model, a.thinking
    if a.name:
        globals()["WS_ROOT"] = WS_ROOT / a.name
    E = json.loads((HERE / "expected_facts.json").read_text(encoding="utf-8"))
    ids = a.only.split(",") if a.only else PI_REQUESTS
    reqs = [r for r in requests() if r["id"] in ids]
    out = HERE / "results" / (f"pi_{a.name}.csv" if a.name else "pi.csv")
    done = set()
    if out.exists():
        done = {(r["arm"], r["request"]) for r in csv.DictReader(open(out, encoding="utf-8"))}
    tasks = [(arm, r) for r in reqs for arm in a.arms.split(",") if (arm, r["id"]) not in done]
    print(f"{len(tasks)} sessions", flush=True)
    new = not out.exists()
    with open(out, "a", newline="", encoding="utf-8") as fh, ThreadPoolExecutor(a.workers) as pool:
        w = None
        futs = {pool.submit(one, arm, r, E, a.timeout): (arm, r["id"]) for arm, r in tasks}
        for f in as_completed(futs):
            try:
                row = f.result()
            except Exception as e:
                print("CRASH", futs[f], repr(e), flush=True)
                continue
            if w is None:
                w = csv.DictWriter(fh, fieldnames=list(row))
                if new:
                    w.writeheader()
            w.writerow(row)
            fh.flush()
            print(f"{row['arm']:12s} {row['request']:4s} {'PASS' if row['pass_all'] else 'fail'} tools={row['tool_calls']} "
                  f"{row['seconds']}s {row['note'][:60]} {row['failed'][:120]}", flush=True)


if __name__ == "__main__":
    main()
