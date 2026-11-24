"""Run the evaluation: arms x requests x repeats, scored on figure facts.

    EVAL_API_KEY=... python experiments/eval/run_batch.py --name t0 --temperature 0
    EVAL_API_KEY=... python experiments/eval/run_batch.py --name t07 --temperature 0.7 --repeat 3
    python experiments/eval/run_batch.py --name pilot --only 02,12,B02 --arms P-mpl,R-mpl-brief
    python experiments/eval/run_batch.py --name cd_sx --no-think --arms P-mpl,P-mpl+cd,P-ec,P-ec+cd --repeat 3 ...   (EXPERIMENT_CD.md)

Rows go to eval/results/batch_<name>.csv; each run's replies, script/spec, images and facts to
eval/results/runs/<name>/<arm>/<request>_r<repeat>/.
"""
import argparse
import csv
import json
import os
import sys
import time
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent                     # experiments/
REPO = ROOT.parent                     # the library (plotkit, tests/inputs, prompts, echartkit, .venv)
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(HERE))
import paths  # noqa: E402

FIELDS = ["time", "run", "arm", "set", "group", "request", "temperature", "repeat", "ok_run", "pass_all",
          "pass_ask", "pass_data", "pass_conv", "n_checks", "n_failed", "first_try", "model_calls", "seconds",
          "exec_seconds", "prompt_tokens", "output_tokens", "route", "loc", "subprocess", "network", "delete",
          "exec", "write_outside", "failed", "errors", "run_dir", "cd", "schema_ok_first", "schema_ok_all", "schema_error"]


def requests():
    import run_agent
    from requests_b import REQUESTS
    out = []
    for rid, name, file, text in run_agent.read_prompts(ROOT / "tests" / "AGENT_TEST_PROMPTS.md"):
        out.append({"id": rid, "set": "A", "group": "A", "files": [str(REPO / file)], "text": text})
    for name, group, files, text in REQUESTS:
        out.append({"id": name.split("_")[0], "set": "B", "group": group, "files": [str(ROOT / f) for f in files],
                    "text": text})
    return out


def route(arm, final):
    if not arm.startswith("P-") or not isinstance(final, dict):
        return ""
    return "code" if final.get("code") else "echarts" if final.get("echarts") else "keys"


def one(task):
    import arms
    import check
    arm, req, rep, temp, name, base, model, key, checks, extra = task
    arms.CD = extra.pop("cd", {}) if isinstance(extra, dict) else {}
    arms.EXTRA_BODY = extra
    run_dir = HERE / "results" / "runs" / name / arm / f"{req['id']}_r{rep}"
    rec = arms.run_arm(arm, req["files"], req["text"], run_dir, base, model, key, temperature=temp)
    if rec["ok_run"]:
        ok, res = check.run_checks(rec["figures"], checks)
    else:
        ok, res = False, [{"check": "run", "cat": "data", "ok": False, "why": "no plot after retries"}]
    cats = lambda cs: all(r["ok"] for r in res if r["cat"] in cs)  # noqa: E731
    has_conv = any(r["cat"] == "conv" for r in res)
    st = arms.code_stats(rec["final"]) if not arm.startswith("P-") else {}
    calls = rec["calls"]
    row = {"time": time.strftime("%Y-%m-%d %H:%M:%S"), "run": name, "arm": arm, "set": req["set"],
           "group": req["group"], "request": req["id"], "temperature": temp, "repeat": rep,
           "ok_run": int(rec["ok_run"]), "pass_all": int(ok), "pass_ask": int(rec["ok_run"] and cats(("data", "ask"))),
           "pass_data": int(rec["ok_run"] and cats(("data",))),
           "pass_conv": "" if not has_conv else int(rec["ok_run"] and cats(("conv",))),
           "n_checks": len(res), "n_failed": sum(not r["ok"] for r in res),
           "first_try": int(ok and len(calls) == 1), "model_calls": len(calls), "seconds": rec["seconds"],
           "exec_seconds": rec["exec_seconds"], "prompt_tokens": sum(c.get("prompt_tokens") or 0 for c in calls),
           "output_tokens": sum(c.get("output_tokens") or 0 for c in calls), "route": route(arm, rec["final"]),
           **{k: st.get(k, "") for k in ("loc", "subprocess", "network", "delete", "exec", "write_outside")},
           "failed": " | ".join(f"[{r['cat']}] {r['check']}: {r['why']}" for r in res if not r["ok"])[:1500],
           "errors": " || ".join(e[:300] for e in rec["errors"])[:1500], "run_dir": str(run_dir.relative_to(HERE)),
           "cd": arms.cd.parse_arm(arm)[1] or "",
           "schema_ok_first": "" if not calls or "schema_ok" not in calls[0] else int(calls[0]["schema_ok"]),
           "schema_ok_all": "" if not calls or "schema_ok" not in calls[0] else int(all(c.get("schema_ok") for c in calls)),
           "schema_error": next((c.get("schema_error") for c in calls if c.get("schema_error")), "")[:200]}
    (run_dir / "checks.json").write_text(json.dumps(res, ensure_ascii=False, default=str), encoding="utf-8")
    return row


def main():
    import arms
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--name", required=True)
    ap.add_argument("--arms", default=",".join(arms.ARMS))
    ap.add_argument("--only", help="request ids, e.g. 02,12,B05")
    ap.add_argument("--sets", default="A,B")
    ap.add_argument("--temperature", type=float, default=0.6)
    ap.add_argument("--repeat", type=int, default=1)
    ap.add_argument("--workers", type=int, default=6)
    ap.add_argument("--base-url", default="https://centinels.ml2-alpha.com/v1")
    ap.add_argument("--model", default="odin")
    ap.add_argument("--no-think", action="store_true", help="chat_template_kwargs.enable_thinking=false for every arm")
    ap.add_argument("--reasoning-effort", help="reasoning_effort for every call (OpenAI-style models), e.g. none, minimal, low")
    ap.add_argument("--pi-model", help="call the model through the Pi CLI instead, e.g. centinels/gpt-6-luna (Pi holds the key)")
    ap.add_argument("--pi-thinking", default="off", help="Pi thinking level with --pi-model")
    ap.add_argument("--prompt-dir", help="layer-v2 prompts for the protocol arms, e.g. prompts/v2")
    ap.add_argument("--backend", choices=("openai", "anthropic"), default="openai",
                    help="anthropic: the Messages API (ANTHROPIC_API_KEY), e.g. --model claude-haiku-5-5 --effort low")
    ap.add_argument("--cd-param", choices=("response_format", "json_schema"), default="response_format")
    ap.add_argument("--effort", help="anthropic backend: output_config.effort")
    ap.add_argument("--asks", choices=("last", "first"), default="last")
    ap.add_argument("--cd-note", action="store_true", help="+cd arms: tell the model the reply is schema-constrained")
    a = ap.parse_args()
    if a.backend == "anthropic" and any(x.endswith("+cd") for x in a.arms.split(",")):
        ap.error("the Anthropic API cannot take the full schema (limits); use +cdflat")
    if a.prompt_dir:                       # read by arms.system_prompt in every worker process
        os.environ["EVAL_PROMPT_DIR"] = str(paths.datapath(a.prompt_dir))
    key = os.environ.get("EVAL_API_KEY", "")
    if not key and os.environ.get("EVAL_API_KEY_FILE"):
        key = Path(os.path.expanduser(os.environ["EVAL_API_KEY_FILE"])).read_text().strip()
    extra = {"chat_template_kwargs": {"enable_thinking": False}} if a.no_think else {}
    if a.reasoning_effort:
        extra["reasoning_effort"] = a.reasoning_effort
    if a.pi_model:
        extra = {"pi": {"model": a.pi_model, "thinking": a.pi_thinking}}
    if a.backend == "anthropic":
        extra = {}
        key = key or os.environ.get("ANTHROPIC_API_KEY", "")
    base_set = any(x == "--base-url" or x.startswith("--base-url=") for x in sys.argv)
    extra["cd"] = {"backend": a.backend, "param": a.cd_param, "effort": a.effort, "asks": a.asks, "note": a.cd_note,
                   "base": a.base_url if (a.backend == "anthropic" and base_set) else None}
    for x in a.arms.split(","):
        if arms.cd.parse_arm(x)[0] not in arms.ARMS:
            ap.error(f"unknown arm {x}")
    E = json.loads((HERE / "expected_facts.json").read_text(encoding="utf-8"))
    only = set(a.only.split(",")) if a.only else None
    reqs = [r for r in requests() if r["set"] in a.sets.split(",") and (not only or r["id"] in only)]
    tasks = [(arm, r, rep, a.temperature, a.name, a.base_url, a.model, key, E[r["id"]], extra)
             for rep in range(1, a.repeat + 1) for r in reqs for arm in a.arms.split(",")]
    out = HERE / "results" / f"batch_{a.name}.csv"
    out.parent.mkdir(parents=True, exist_ok=True)
    if a.pi_model and any("+cd" in x for x in a.arms.split(",")):
        ap.error("constrained decoding cannot go through Pi")
    done = set()
    if out.exists():                                   # resume: skip runs already in the CSV
        for r in csv.DictReader(open(out, encoding="utf-8")):
            done.add((r["arm"], r["request"], r["repeat"]))
    tasks = [t for t in tasks if (t[0], t[1]["id"], str(t[2])) not in done]
    print(f"{len(tasks)} runs ({len(done)} already done) -> {out.relative_to(ROOT)}", flush=True)
    new = not out.exists()
    fields = FIELDS if new else next(csv.reader(open(out, encoding="utf-8")))     # an older CSV keeps its columns
    with open(out, "a", newline="", encoding="utf-8") as fh, ProcessPoolExecutor(a.workers) as pool:
        w = csv.DictWriter(fh, fieldnames=fields, extrasaction="ignore")
        if new:
            w.writeheader()
        futs = {pool.submit(one, t): t for t in tasks}
        n = 0
        for f in as_completed(futs):
            t = futs[f]
            n += 1
            try:
                row = f.result()
            except Exception as e:
                print(f"[{n}/{len(tasks)}] {t[0]} {t[1]['id']} r{t[2]} CRASH {e!r}", flush=True)
                continue
            w.writerow(row)
            fh.flush()
            print(f"[{n}/{len(tasks)}] {row['arm']:12s} {row['request']:4s} r{row['repeat']} "
                  f"{'PASS' if row['pass_all'] else 'fail'} ask={row['pass_ask']} calls={row['model_calls']} "
                  f"{row['seconds']}s {row['failed'][:120]}", flush=True)


if __name__ == "__main__":
    main()
