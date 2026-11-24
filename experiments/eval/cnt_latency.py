"""E1: how long a turn takes, the way the assistant would run it: one warm process, the model on the llama.cpp
server, the plot drawn in the same process (ECharts: one Node call), up to 2 retries.

    EVAL_API_KEY_FILE=... python experiments/eval/cnt_latency.py --split sealed --arms P-ec,P-mpl --users 1 --name lat1
    python experiments/eval/cnt_latency.py ... --users 2          # two people at once (the server has 2 slots)
    python experiments/eval/cnt_latency.py ... --arms R-mpl --only S001,S002,...   # raw code, a few requests

Writes eval/results/cnt_latency_<name>.csv: per turn the wall time split into prefill, decode, drawing and
retries, with llama.cpp's own timings, so the numbers can be projected to a faster server
(prefill and decode scale with its speed; drawing does not).
"""
import argparse
import concurrent.futures as cf
import csv
import json
import os
import sys
import threading
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent.parent))      # the library
sys.path.insert(0, str(HERE.parent))             # experiments/
sys.path.insert(0, str(HERE))
import cnt_runs  # noqa: E402

FIELDS = ["arm", "users", "item", "turn", "calls", "ok", "turn_s", "llm_s", "prefill_ms", "decode_ms", "prompt_tokens",
          "cached_tokens", "output_tokens", "draw_s", "first_call_cached"]
_lock = threading.Lock()
_draw_lock = threading.Lock()


def draw_inprocess(spec, engine, run_dir, turn):
    import plotkit
    from plotkit import PlotkitError
    spec = dict(spec)
    out = dict(spec.get("output") or {}) if isinstance(spec.get("output"), dict) else ({"format": spec["output"]} if spec.get("output") else {})
    out["dir"] = str(run_dir / "out" / f"t{turn}")
    spec["output"] = out
    files = spec.get("file") or spec.get("files") or []
    files = files if isinstance(files, list) else [files]
    spec["file"] = [f if os.path.isabs(str(f)) else str(run_dir / str(f)) for f in files]
    spec.pop("files", None)
    t0 = time.time()
    with _draw_lock:                       # pyplot is not thread-safe; a real server would use processes
        try:
            r = plotkit.plot(spec, engine=engine)
        except PlotkitError as e:
            r = {"ok": False, "error": e.message, "hint": e.hint}
        except Exception as e:  # noqa: BLE001
            r = {"ok": False, "error": f"{type(e).__name__}: {e}", "hint": ""}
    return r, time.time() - t0


def run_item(arm, item, args, key, users):
    run_dir = HERE / "results" / "runs" / f"cnt_lat_{args.name}" / arm / item["id"]
    run_dir.mkdir(parents=True, exist_ok=True)
    if not (run_dir / "data").exists():
        (run_dir / "data").symlink_to(cnt_runs.CNT / "data", target_is_directory=True)
    messages = [{"role": "system", "content": cnt_runs.system_prompt(arm)}]
    rows = []
    for ti, turn in enumerate(item["turns"], 1):
        t_turn = time.time()
        user = cnt_runs.first_message(arm, item, turn["text"]) if ti == 1 else f"사용자 요청 (이어서):\n{turn['text']}"
        messages.append({"role": "user", "content": user})
        calls, draw_s, ok = [], 0.0, False
        for attempt in range(3):
            text, _, st = cnt_runs.call_llm(args.base_url, args.model, key, messages, args.temperature,
                                            3000 if arm.startswith("P-") else 8000)
            calls.append(st)
            messages.append({"role": "assistant", "content": text})
            try:
                if arm == "R-mpl":
                    code = cnt_runs.extract_code(text)
                    t0 = time.time()
                    r, _, _ = cnt_runs.run_script(code, run_dir, ti)
                    draw_s += time.time() - t0
                else:
                    spec = cnt_runs.extract_json(text)
                    r, dt = draw_inprocess(spec, "matplotlib" if arm == "P-mpl" else "echarts", run_dir, ti)
                    draw_s += dt
            except (ValueError, json.JSONDecodeError) as e:
                r = {"ok": False, "error": f"your reply could not be read: {e}", "hint": ""}
            if r.get("ok"):
                ok = True
                break
            messages.append({"role": "user", "content": f"plotkit error: {r.get('error')}\nhint: {r.get('hint', '')}\n\n고쳐서 다시 보내 주세요."})
        s = lambda k: sum((c.get(k) or 0) for c in calls)  # noqa: E731
        rows.append({"arm": arm, "users": users, "item": item["id"], "turn": ti, "calls": len(calls), "ok": int(ok),
                     "turn_s": round(time.time() - t_turn, 3), "llm_s": round(s("llm_s"), 3),
                     "prefill_ms": round(s("prefill_ms")), "decode_ms": round(s("decode_ms")),
                     "prompt_tokens": s("prompt_tokens"), "cached_tokens": s("cached_tokens"),
                     "output_tokens": s("output_tokens"), "draw_s": round(draw_s, 3),
                     "first_call_cached": calls[0].get("cached_tokens")})
    return rows


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--split", default="dev")
    ap.add_argument("--name", required=True)
    ap.add_argument("--arms", default="P-ec")
    ap.add_argument("--users", type=int, default=1)
    ap.add_argument("--base-url", default="http://strixhalo:8084/v1")
    ap.add_argument("--model", default="qwen3.8-flash-next")
    ap.add_argument("--temperature", type=float, default=0.2)
    ap.add_argument("--only")
    a = ap.parse_args()
    key = Path(os.path.expanduser(os.environ["EVAL_API_KEY_FILE"])).read_text().strip() if os.environ.get("EVAL_API_KEY_FILE") else ""
    items = json.loads((cnt_runs.CNT / a.split / "requests.json").read_text(encoding="utf-8"))["items"]
    if a.only:
        items = [it for it in items if it["id"] in set(a.only.split(","))]
    out = HERE / "results" / f"cnt_latency_{a.name}.csv"
    new = not out.exists()
    fh = open(out, "a", newline="", encoding="utf-8")
    w = csv.DictWriter(fh, fieldnames=FIELDS)
    if new:
        w.writeheader()
    for arm in a.arms.split(","):
        # users > 1: that many people work through the list at the same time
        with cf.ThreadPoolExecutor(max_workers=a.users) as ex:
            for rows in ex.map(lambda it, arm=arm: run_item(arm, it, a, key, a.users), items):
                with _lock:
                    for r in rows:
                        w.writerow(r)
                    fh.flush()
                print(arm, rows[0]["item"], " ".join(f"{r['turn_s']:.1f}s" for r in rows), flush=True)
    fh.close()


if __name__ == "__main__":
    main()
