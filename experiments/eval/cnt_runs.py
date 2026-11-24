"""CNT plant study: the requests in eval/cnt/<split>/requests.json (single requests and multi-turn sessions)
on each arm, with the model on a llama.cpp server, checked turn by turn against the expectations.

  P-mpl / P-ec   prompts/v2 (core + the engine's hatch) -> JSON spec -> plotkit/chartkit (matplotlib / ECharts)
  P-hyb          the matplotlib prompt (the "code" hatch allowed); drawn with ECharts unless the spec uses "code"
  R-mpl          a short prompt + a data brief -> a Python matplotlib script, run in a sandbox (accuracy ceiling)
  <P arm>+cd     the same, with the reply constrained by a per-request JSON Schema (constrained decoding)
  <P arm>+cdflat the same, constrained to the flat settings-list form (fits the Anthropic API's schema limits)

Constrained-decoding study (EXPERIMENT_CD.md), thinking off as in every run here:
    python experiments/eval/cnt_runs.py --split dev --name cd1 --arms P-mpl,P-mpl+cd,P-ec,P-ec+cd --repeat 3
    python experiments/eval/cnt_runs.py --split dev --name cdh --backend anthropic --model claude-haiku-5-5 --effort low \
        --arms P-mpl,P-mpl+cdflat --repeat 3

    EVAL_API_KEY_FILE=~/.config/pi/strix.key python experiments/eval/cnt_runs.py --split dev --name dev1 \\
        --base-url http://strixhalo:8084/v1 --model qwen3.8-flash-next --arms P-mpl,P-ec --repeat 1 --workers 2

Every model call records llama.cpp's timings (prompt tokens, tokens served from the prompt cache, prefill and
decode milliseconds). Results: eval/results/cnt_<name>.csv (one row per turn) and
eval/results/runs/cnt_<name>/<arm>/<item>_r<repeat>/record.json. Resumes: finished (arm, item, repeat) are skipped.
"""
import argparse
import concurrent.futures as cf
import csv
import json
import os
import re
import shutil
import subprocess
import sys
import threading
import time
import urllib.request
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent                     # experiments/
REPO = ROOT.parent                     # the library (plotkit, tests/inputs, prompts, echartkit, .venv)
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(HERE))
import cd  # noqa: E402

CNT = HERE / "cnt"
PY = str(REPO / ".venv" / "bin" / "python") if (REPO / ".venv" / "bin" / "python").exists() else sys.executable
MPLCACHE = HERE / "results" / ".mplcache"
ARMS = ("P-mpl", "P-ec", "P-hyb", "R-mpl")

RAW = """You write Python scripts that draw plots with pandas and matplotlib for a CNT production team.
Users write in Korean (sometimes English). Each turn you get the user's request and a preview of the data files;
in a follow-up turn the user asks to change the plot you made last time.

Reply with the complete script inside one ```python block, and nothing else. The script must:
- read the data file(s) by the paths shown in the preview (Excel, CSV or text files; read Korean headers as they are;
  some sheets have a units row under the header; one CSV export uses semicolons and decimal commas);
- compute what the request needs (filters, group means, sums, counts, pivots, bins, moving averages, computed values)
  and draw it; save every figure into OUT_DIR (PNG at 300 dpi unless the user asks for something else);
  do not call plt.show();
- run without asking anything: where the request is unclear, make a reasonable choice.
Environment: Python 3 with pandas, numpy, scipy, matplotlib and openpyxl. Korean text needs a Korean font;
"Noto Sans CJK KR" is installed (plt.rcParams["font.family"] = "Noto Sans CJK KR"). There is no internet.

## The data
Production run logs (one row per run: date, week, shift, reactor R1–R4, catalyst lot, zone temperatures, gas flows,
residence time, humidity, yield, throughput, TGA purity, Raman I_G/I_D, grade), a downtime log, a DOE grid,
TEM diameters, reactor temperature logs, TGA exports (temperature °C, weight %, derivative weight %/°C, one sheet
per batch) and Raman spectra. A TGA plot here: x = temperature, left y = weight %, right y = derivative weight;
"잔류량" = the weight at 800 °C; "피크" = the DTG peak temperature; "onset" = the extrapolated onset temperature
(the tangent at the steepest drop meets the baseline). Write values the user asks to show on the plot as text."""

_lock = threading.Lock()


# =================================================================== prompts and previews
PROMPT_DIR = REPO / "prompts" / "v2"


def system_prompt(arm, prompt_dir=None, cd_note=False):
    d = Path(prompt_dir) if prompt_dir else PROMPT_DIR
    arm, profile = cd.parse_arm(arm)
    if arm.startswith("P-"):
        core = (d / "core.md").read_text(encoding="utf-8")
        hatch = "hatch_mpl.md" if arm in ("P-mpl", "P-hyb") else "hatch_ec.md"   # P-hyb: ECharts, matplotlib only for "code"
        return core + (d / hatch).read_text(encoding="utf-8") + cd.prompt_suffix(profile, cd_note)
    return RAW


_PREVIEWS = {}


def preview_text(files):
    """The same data preview for every arm: sheets, rows, columns with letter, type and values."""
    import chartkit
    parts = []
    for f in files:
        if f in _PREVIEWS:
            parts.append(_PREVIEWS[f])
            continue
        p = CNT / f
        paths = sorted(p.parent.glob(p.name)) if any(c in f for c in "*?") else [p]
        lines = []
        for path in paths:
            rel = path.relative_to(CNT).as_posix()
            try:
                pv = chartkit.preview(str(path))
            except Exception as e:  # noqa: BLE001
                lines.append(f"파일 {rel}: 읽기 실패 ({e})")
                continue
            sheets = pv["sheets"]
            lines.append(f"파일 {rel}" + (f" (시트 {len(sheets)}개)" if len(sheets) > 1 else ""))
            for sh in sheets[:12]:
                if "error" in sh:
                    lines.append(f"  시트 '{sh['sheet']}': {sh['error']}")
                    continue
                cols = []
                for c in sh["columns"]:
                    if c["type"] == "number":
                        d = f"{c['col']} {c['name']} [수치 {c['min']}~{c['max']}" + (f"; 값 {c['values']}" if c.get("values") else "") + "]"
                    elif c["type"] == "date":
                        d = f"{c['col']} {c['name']} [날짜 {c['min']}~{c['max']}]"
                    else:
                        d = f"{c['col']} {c['name']} [텍스트 {c['n_values']}종: {', '.join(map(str, c['values']))}]"
                    cols.append(d)
                lines.append(f"  시트 '{sh['sheet']}' ({sh['rows']}행): " + " | ".join(cols))
            if len(sheets) > 12:
                lines.append(f"  … 시트 {len(sheets) - 12}개 더: " + ", ".join(s["sheet"] for s in sheets[12:]))
        txt = "\n".join(lines)
        _PREVIEWS[f] = txt
        parts.append(txt)
    return "데이터 미리보기:\n" + "\n".join(parts)


def first_message(arm, item, text):
    msg = f"{preview_text(item['files'])}\n\n"
    if arm == "R-mpl":
        msg += 'OUT_DIR = "out"\n\n'
    return msg + f"사용자 요청:\n{text}"


# =================================================================== the model
def call_llm(base, model, key, messages, temperature, max_tokens, timeout=900, think=False, schema=None,
             cd_param="response_format", strict=True):
    body = {"model": model, "messages": messages, "temperature": temperature, "max_tokens": max_tokens,
            "chat_template_kwargs": {"enable_thinking": think}, "cache_prompt": True,
            **cd.openai_fields(schema, cd_param, strict)}
    req = urllib.request.Request(base.rstrip("/") + "/chat/completions", data=json.dumps(body).encode(),
                                 headers={"Content-Type": "application/json", **({"Authorization": f"Bearer {key}"} if key else {})})
    t0 = time.time()
    with urllib.request.urlopen(req, timeout=timeout) as r:
        d = json.loads(r.read())
    dt = time.time() - t0
    ch = d["choices"][0]
    msg = ch["message"]
    text = msg.get("content") or ""
    tm = d.get("timings") or {}
    us = d.get("usage") or {}
    stats = {"llm_s": round(dt, 3), "prompt_tokens": us.get("prompt_tokens") or tm.get("prompt_n"),
             "output_tokens": us.get("completion_tokens") or tm.get("predicted_n"),
             "cached_tokens": tm.get("cache_n", (us.get("prompt_tokens_details") or {}).get("cached_tokens")),
             "prompt_n": tm.get("prompt_n"), "prefill_ms": tm.get("prompt_ms"), "decode_ms": tm.get("predicted_ms"),
             "finish": ch.get("finish_reason")}
    return text, msg.get("reasoning_content") or "", stats


def extract_json(reply):
    reply = re.sub(r"<think>.*?</think>", "", reply, flags=re.S)
    m = re.search(r"```(?:json)?\s*\n(.*?)```", reply, flags=re.S)
    txt = m.group(1) if m else reply[reply.find("{"): reply.rfind("}") + 1]
    return json.loads(txt)


def extract_code(reply):
    reply = re.sub(r"<think>.*?</think>", "", reply, flags=re.S)
    m = re.search(r"```(?:python|py)?\s*\n(.*?)```", reply, flags=re.S)
    if m:
        return m.group(1)
    raise ValueError("no ```python block in the reply")


# =================================================================== drawing
def sandbox(cmd, run_dir, timeout=120):
    MPLCACHE.mkdir(parents=True, exist_ok=True)
    env = {"PATH": "/usr/bin:/bin", "HOME": str(run_dir), "MPLBACKEND": "Agg", "MPLCONFIGDIR": str(MPLCACHE),
           "LANG": "C.UTF-8", "PYTHONIOENCODING": "utf-8"}
    full = ["bwrap", "--ro-bind", "/", "/", "--dev", "/dev", "--proc", "/proc", "--tmpfs", "/tmp",
            "--ro-bind", str(HERE), str(HERE), "--bind", str(run_dir), str(run_dir), "--bind", str(MPLCACHE), str(MPLCACHE),
            "--unshare-net", "--die-with-parent", "--chdir", str(run_dir), *cmd]
    try:
        p = subprocess.run(full, capture_output=True, text=True, timeout=timeout, env=env)
        return p.returncode, p.stdout, p.stderr
    except subprocess.TimeoutExpired:
        return -9, "", f"timed out after {timeout} s"


def draw_spec(spec, engine, run_dir, turn):
    """Draw a spec in a fresh process; output always goes to run_dir/out."""
    spec = dict(spec)
    out = dict(spec.get("output") or {}) if isinstance(spec.get("output"), dict) else ({"format": spec["output"]} if spec.get("output") else {})
    out["dir"] = str(run_dir / "out" / f"t{turn}")
    spec["output"] = out
    sp = run_dir / f"spec_t{turn}.json"
    sp.write_text(json.dumps(spec, ensure_ascii=False, indent=1), encoding="utf-8")
    res = run_dir / f"draw_t{turn}.json"
    res.unlink(missing_ok=True)
    env = {**os.environ, "MPLBACKEND": "Agg", "MPLCONFIGDIR": str(MPLCACHE)}
    p = subprocess.run([PY, "-I", str(HERE / "cnt_draw.py"), str(sp), engine, str(res)], cwd=run_dir,
                       capture_output=True, text=True, timeout=300, env=env)
    if not res.exists():
        return {"ok": False, "error": "draw crashed: " + (p.stderr.strip().splitlines() or ["?"])[-1], "hint": ""}, [], 0.0
    d = json.loads(res.read_text(encoding="utf-8"))
    return d["result"], d["facts"], d["draw_s"]


def run_script(code, run_dir, turn):
    script = run_dir / f"plot_t{turn}.py"
    script.write_text(code.replace('OUT_DIR = "out"', f'OUT_DIR = "out/t{turn}"'), encoding="utf-8")
    (run_dir / "out" / f"t{turn}").mkdir(parents=True, exist_ok=True)
    fpath = run_dir / f"facts_t{turn}.json"
    fpath.unlink(missing_ok=True)
    t0 = time.time()
    rc, so, se = sandbox([PY, "-I", str(HERE / "_chart_runner.py"), str(script), str(fpath)], run_dir)
    dt = time.time() - t0
    figs = json.loads(fpath.read_text(encoding="utf-8"))["figures"] if fpath.exists() else []
    if rc != 0:
        err = "\n".join(l for l in (se or "").strip().splitlines()[-20:])
        return {"ok": False, "error": f"The script failed (exit {rc}):\n{err}", "hint": ""}, figs, dt
    if not figs:
        return {"ok": False, "error": "The script ran but saved no figure into OUT_DIR.", "hint": ""}, [], dt
    return {"ok": True}, figs, dt


def route_of(spec):
    if not isinstance(spec, dict):
        return "script"
    r = [k for k in ("data_code", "code", "echarts") if spec.get(k)]
    return "+".join(r) if r else "keys"


# =================================================================== one run (all turns of one item)
def run_item(arm, item, rep, args, key):
    run_dir = HERE / "results" / "runs" / f"cnt_{args.name}" / arm / f"{item['id']}_r{rep}"
    if run_dir.exists():
        shutil.rmtree(run_dir)
    run_dir.mkdir(parents=True)
    (run_dir / "data").symlink_to(CNT / "data", target_is_directory=True)
    base_arm, profile = cd.parse_arm(arm)
    messages = [{"role": "system", "content": system_prompt(arm, args.prompt_dir, args.cd_note)}]
    con_schema = full_schema = None
    if base_arm.startswith("P-"):           # the schema of this request; the full one also scores free arms' replies
        con_schema, full_schema = cd.schemas(item["files"], CNT, ("curve", "chart"), cd.hatch_for(base_arm), profile,
                                             args.asks)
        if profile and args.cd_compat == "gufo":     # Strix Halo's server: see eval/cd_gufo.py
            import cd_gufo
            con_schema = cd_gufo.gufo(con_schema)
        if profile:
            (run_dir / "schema.json").write_text(json.dumps(con_schema, ensure_ascii=False), encoding="utf-8")
    own_schema = con_schema if profile == "flat" else full_schema
    turns_out = []
    for ti, turn in enumerate(item["turns"], 1):
        t_turn = time.time()
        user = first_message(arm, item, turn["text"]) if ti == 1 else f"사용자 요청 (이어서):\n{turn['text']}"
        messages.append({"role": "user", "content": user})
        calls, result, facts, spec, draw_s, engine = [], None, [], None, 0.0, None
        for attempt in range(args.retries + 1):
            try:
                mt = args.max_tokens if arm.startswith("P-") else args.max_tokens_raw
                if args.backend == "anthropic":
                    text, reasoning, stats = cd.call_anthropic(args.model, key, messages, args.temperature, mt,
                                                               schema=con_schema, effort=args.effort,
                                                               base=args.base_url if args.base_url_set else None)
                else:
                    text, reasoning, stats = call_llm(args.base_url, args.model, key, messages, args.temperature, mt,
                                                      schema=con_schema, cd_param=args.cd_param,
                                                      strict=args.cd_compat != "gufo")
            except Exception as e:  # noqa: BLE001
                calls.append({"error": f"{type(e).__name__}: {e}"})
                result = {"ok": False, "error": f"model call failed: {e}", "hint": ""}
                break
            if own_schema is not None:          # does the reply fit the schema as written (free arms: the full one)
                stats["schema_ok"], stats["schema_error"] = cd.conformance(text, own_schema)
            calls.append({"reply": text, **stats})
            messages.append({"role": "assistant", "content": text})
            try:
                if arm == "R-mpl":
                    spec = extract_code(text)
                    result, facts, draw_s = run_script(spec, run_dir, ti)
                else:
                    spec = extract_json(text)
                    if profile == "flat":
                        calls[-1]["flat"] = spec
                        spec = cd.ss.flat_to_spec(spec)
                    engine = "matplotlib" if base_arm == "P-mpl" or (base_arm == "P-hyb" and spec.get("code")) else "echarts"
                    if base_arm == "P-hyb" and engine == "matplotlib":
                        spec = {k: v for k, v in spec.items() if k != "echarts"}
                    result, facts, draw_s = draw_spec(spec, engine, run_dir, ti)
            except (ValueError, json.JSONDecodeError) as e:
                result = {"ok": False, "error": f"your reply could not be read: {e}", "hint":
                          "reply with one ```json block" if arm.startswith("P-") else "reply with one ```python block"}
            if result.get("ok"):
                break
            if attempt < args.retries:
                fb = (f"plotkit error: {result.get('error')}" + (f"\nhint: {result.get('hint')}" if result.get("hint") else "")) \
                    if arm.startswith("P-") else result.get("error", "")
                messages.append({"role": "user", "content": fb + "\n\n고쳐서 다시 보내 주세요."})
        expect = turn.get("expect") or {}
        chk = {"pass": None}
        try:
            import cnt_check
            chk = cnt_check.check(expect, facts, result, spec if isinstance(spec, dict) else None, item=item, turn=ti)
        except ImportError:
            pass
        turns_out.append({"turn": ti, "text": turn["text"], "calls": calls, "spec": spec, "engine": engine,
                          "result": result, "facts": facts, "draw_s": draw_s, "check": chk,
                          "turn_s": round(time.time() - t_turn, 3)})
    rec = {"arm": arm, "item": item["id"], "repeat": rep, "split": item.get("split"), "persona": item.get("persona"),
           "type": item.get("type"), "cd": (profile or "") + ("+gufo" if profile and args.cd_compat == "gufo" else ""), "backend": args.backend, "model": args.model,
           "effort": args.effort or "", "turns": turns_out}
    (run_dir / "record.json").write_text(json.dumps(rec, ensure_ascii=False, indent=1, default=str), encoding="utf-8")
    return rec, run_dir


FIELDS = ["time", "run", "arm", "split", "item", "type", "persona", "turn", "n_turns", "repeat", "kind", "ok_run", "pass",
          "n_checks", "n_failed", "failed", "unchecked", "model_calls", "prompt_tokens", "cached_tokens", "prefill_ms",
          "output_tokens", "decode_ms", "llm_s", "draw_s", "turn_s", "route", "unsupported", "n_asks", "error", "run_dir",
          "cd", "model", "schema_ok_first", "schema_ok_all", "schema_error"]


def rows_of(rec, run_dir, args):
    out = []
    for t in rec["turns"]:
        calls = [c for c in t["calls"] if "reply" in c]
        spec = t["spec"]
        asks = spec.get("asks") if isinstance(spec, dict) and isinstance(spec.get("asks"), list) else []
        chk = t["check"] or {}
        s = lambda k: sum((c.get(k) or 0) for c in calls)  # noqa: E731
        out.append({"time": time.strftime("%Y-%m-%d %H:%M:%S"), "run": args.name, "arm": rec["arm"], "split": rec["split"],
                    "item": rec["item"], "type": rec["type"], "persona": rec["persona"], "turn": t["turn"],
                    "n_turns": len(rec["turns"]), "repeat": rec["repeat"],
                    "kind": ((t.get("check") or {}).get("kind_expected") or ""),
                    "ok_run": int(bool((t["result"] or {}).get("ok"))),
                    "pass": "" if chk.get("pass") is None else int(bool(chk["pass"])),
                    "n_checks": chk.get("n_checks", ""), "n_failed": chk.get("n_failed", ""),
                    "failed": " | ".join(chk.get("failed", []))[:600], "unchecked": " | ".join(chk.get("unchecked", []))[:300],
                    "model_calls": len(t["calls"]), "prompt_tokens": s("prompt_tokens"), "cached_tokens": s("cached_tokens"),
                    "prefill_ms": round(s("prefill_ms")), "output_tokens": s("output_tokens"), "decode_ms": round(s("decode_ms")),
                    "llm_s": round(s("llm_s"), 2), "draw_s": round(t["draw_s"], 2), "turn_s": t["turn_s"],
                    "route": route_of(spec), "n_asks": len(asks),
                    "unsupported": sum(1 for a in asks if isinstance(a, dict) and str(a.get("how", "")).lower() == "unsupported"),
                    "error": "" if (t["result"] or {}).get("ok") else str((t["result"] or {}).get("error", ""))[:300],
                    "run_dir": str(run_dir.relative_to(HERE)), "cd": rec.get("cd", ""), "model": rec.get("model", ""),
                    "schema_ok_first": "" if not calls or "schema_ok" not in calls[0] else int(calls[0]["schema_ok"]),
                    "schema_ok_all": "" if not calls or "schema_ok" not in calls[0] else int(all(c.get("schema_ok") for c in calls)),
                    "schema_error": next((c.get("schema_error") for c in calls if c.get("schema_error")), "")[:200]})
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--split", default="dev")
    ap.add_argument("--name", required=True)
    ap.add_argument("--base-url", default="http://strixhalo:8084/v1")
    ap.add_argument("--model", default="qwen3.8-flash-next")
    ap.add_argument("--arms", default="P-mpl,P-ec")
    ap.add_argument("--repeat", type=int, default=1)
    ap.add_argument("--workers", type=int, default=2)
    ap.add_argument("--temperature", type=float, default=0.2)
    ap.add_argument("--max-tokens", type=int, default=3000)
    ap.add_argument("--max-tokens-raw", type=int, default=8000)
    ap.add_argument("--retries", type=int, default=2)
    ap.add_argument("--only", help="comma-separated item ids")
    ap.add_argument("--prompt-dir", help="a folder with core.md, hatch_mpl.md, hatch_ec.md (default prompts/v2)")
    ap.add_argument("--backend", choices=("openai", "anthropic"), default="openai",
                    help="openai: any OpenAI-compatible server (llama.cpp); anthropic: the Messages API (ANTHROPIC_API_KEY)")
    ap.add_argument("--cd-param", choices=("response_format", "json_schema"), default="response_format",
                    help="openai backend: where the schema goes (json_schema = llama.cpp's own field)")
    ap.add_argument("--effort", help="anthropic backend: output_config.effort, e.g. low")
    ap.add_argument("--cd-compat", choices=("none", "gufo"), default="none",
                    help="gufo: adapt constrained schemas for Strix Halo's server (eval/cd_gufo.py), strict false")
    ap.add_argument("--asks", choices=("last", "first"), default="last",
                    help="+cd arms: asks optional and last (as the prompt examples), or required and first (a small plan)")
    ap.add_argument("--cd-note", action="store_true", help="+cd arms: tell the model its reply is schema-constrained (no fence)")
    a = ap.parse_args()
    a.base_url_set = any(x == "--base-url" or x.startswith("--base-url=") for x in sys.argv)
    if a.backend == "anthropic":
        if not a.base_url_set and a.model == ap.get_default("model"):
            ap.error("--backend anthropic needs --model, e.g. --model claude-haiku-5-5")
        if not (os.environ.get("ANTHROPIC_API_KEY") or os.environ.get("EVAL_API_KEY_FILE")):
            ap.error("--backend anthropic needs ANTHROPIC_API_KEY (or EVAL_API_KEY_FILE)")
        bad = [x for x in a.arms.split(",") if x.endswith("+cd")]
        if bad and not a.base_url_set:          # Anthropic's own API limits; gateways (e.g. OpenCode Go) may take more
            ap.error(f"{', '.join(bad)}: the Anthropic API cannot take the full schema (limits); use +cdflat")
    key = Path(os.path.expanduser(os.environ["EVAL_API_KEY_FILE"])).read_text().strip() if os.environ.get("EVAL_API_KEY_FILE") else ""
    if a.backend == "anthropic" and not key:
        key = os.environ["ANTHROPIC_API_KEY"]
    for x in a.arms.split(","):
        b, _ = cd.parse_arm(x)
        if b not in ARMS:
            ap.error(f"unknown arm {x}")
    data = json.loads((CNT / a.split / "requests.json").read_text(encoding="utf-8"))
    items = data["items"] if isinstance(data, dict) else data
    if a.only:
        want = set(a.only.split(","))
        items = [it for it in items if it["id"] in want]
    arms = a.arms.split(",")
    out = HERE / "results" / f"cnt_{a.name}.csv"
    done = set()
    if out.exists():
        for r in csv.DictReader(open(out, encoding="utf-8")):
            if str(r["turn"]) == str(r["n_turns"]):
                done.add((r["arm"], r["item"], r["repeat"]))
    tasks = [(arm, it, rep) for rep in range(1, a.repeat + 1) for it in items for arm in arms
             if (arm, it["id"], str(rep)) not in done]
    print(f"{len(tasks)} runs ({len(done)} already done) -> {out.relative_to(ROOT)}", flush=True)
    new = not out.exists()
    fields = FIELDS if new else next(csv.reader(open(out, encoding="utf-8")))     # an older CSV keeps its columns
    fh = open(out, "a", newline="", encoding="utf-8")
    w = csv.DictWriter(fh, fieldnames=fields, extrasaction="ignore")
    if new:
        w.writeheader()
    n = 0

    def one(t):
        arm, it, rep = t
        rec, rd = run_item(arm, it, rep, a, key)
        return rows_of(rec, rd, a)

    with cf.ThreadPoolExecutor(max_workers=a.workers) as ex:
        futs = {ex.submit(one, t): t for t in tasks}
        for f in cf.as_completed(futs):
            arm, it, rep = futs[f]
            n += 1
            try:
                rows = f.result()
            except Exception as e:  # noqa: BLE001
                print(f"[{n}/{len(tasks)}] {arm} {it['id']} r{rep} CRASH {type(e).__name__}: {e}", flush=True)
                continue
            with _lock:
                for r in rows:
                    w.writerow(r)
                fh.flush()
            summ = " ".join(f"t{r['turn']}:{'PASS' if r['pass'] == 1 else ('fail' if r['pass'] == 0 else '?')}"
                            f"({r['turn_s']:.0f}s)" for r in rows)
            print(f"[{n}/{len(tasks)}] {arm:6} {it['id']:6} r{rep} {summ} {rows[-1]['failed'][:120]}", flush=True)
    fh.close()


if __name__ == "__main__":
    main()
