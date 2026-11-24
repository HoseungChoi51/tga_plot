#!/usr/bin/env python3
"""Minimal local agent: one Korean request -> plot, with a local LLM.

Steps: inspect the file (no LLM) -> ONE model call writes the spec -> plotkit
draws it -> if plotkit reports an error, the error goes back to the model
(at most 2 retries) -> a Korean summary is printed from the result (no LLM).

    python experiments/run_agent.py --base-url http://localhost:11434/v1 --model <name> \\
        --file TGA.xlsx --request "1006R1-V normal 시트, x축 틱 간격 200, 피크 표시 2개"

Works with any OpenAI-compatible server (Ollama, LM Studio, vLLM, llama.cpp).
Add --no-think for Qwen3-style models to skip the thinking phase (faster).

Constrained decoding (EXPERIMENT_CD.md): --constrain sends a JSON Schema built from the file (real sheet and
column names, only known keys) as response_format, so the reply is always a valid spec of known keys and columns.

Engine experiment (see EXPERIMENT.md): --engine echarts draws with ECharts and uses
AGENT_ECHARTS.md as the system prompt. --batch runs every request in a prompts file and
scores it with tests/score.py:
    python experiments/run_agent.py --base-url ... --model ... --engine echarts --arm S \
        --batch tests/AGENT_TEST_PROMPTS.md --out results/batch_S.csv --no-think
"""
import argparse
import csv
import json
import re
import sys
import time
import urllib.request
from pathlib import Path

HERE = Path(__file__).resolve().parent                 # experiments/
sys.path.insert(0, str(HERE.parent))                   # the library
sys.path.insert(0, str(HERE))
import plotkit  # noqa: E402

SPEC_ONLY = """

## Test mode
You cannot run commands in this conversation. The `inspect` result is given below.
Do step 2 only: reply with the JSON spec for the user's request, inside one ```json block, and nothing else.
Use the file name exactly as shown in the inspect result."""


def call_llm(base, model, key, messages, max_tokens=4000, timeout=600, temperature=0, schema=None):
    body = {"model": model, "temperature": temperature, "max_tokens": max_tokens, "messages": messages}
    if schema is not None:
        body["response_format"] = {"type": "json_schema", "json_schema": {"name": "plot_spec", "strict": True, "schema": schema}}
    req = urllib.request.Request(base.rstrip("/") + "/chat/completions", data=json.dumps(body).encode(),
                                 headers={"Content-Type": "application/json",
                                          "Authorization": f"Bearer {key or 'none'}"})
    t0 = time.time()
    with urllib.request.urlopen(req, timeout=timeout) as r:
        resp = json.loads(r.read())
    dt = time.time() - t0
    msg = resp["choices"][0]["message"]
    u = resp.get("usage") or {}
    think = (u.get("completion_tokens_details") or {}).get("reasoning_tokens")
    if think is None:                       # some servers return the thinking text separately
        rc = msg.get("reasoning_content") or msg.get("reasoning") or ""
        think = len(rc) // 3 if rc else 0   # rough token estimate
    stats = {"llm_s": round(dt, 2), "prompt_tokens": u.get("prompt_tokens"),
             "output_tokens": u.get("completion_tokens"), "thinking_tokens": think}
    return msg.get("content") or "", stats


def extract_json(text):
    text = re.sub(r"<think>.*?</think>", "", text, flags=re.S)
    m = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, flags=re.S)
    raw = m.group(1) if m else text[text.find("{"): text.rfind("}") + 1]
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return json.loads(re.sub(r",\s*([}\]])", r"\1", raw))      # trailing commas


def summary_ko(res):
    lines = [f"저장 폴더: {res['output_dir']}"]
    for p in res["plots"]:
        lines.append(f"- {p['sheet']}: " + ", ".join(Path(s).name for s in p["saved"]))
        for a in p["annotations"]:
            sh = f" ({a['sheet']})" if p["sheet"] == "all" else ""
            if "peaks" in a:
                lines.append(f"    {a['name']}{sh}: " + ", ".join(f"{q['x']:.1f}" for q in a["peaks"]))
            elif "value" in a:
                v = "데이터 없음" if a["value"] is None else f"{a['value']:.2f} (x = {a['x_used']:g})"
                lines.append(f"    {a['name']}{sh}: {v}")
    for w in res.get("warnings", []):
        lines.append(f"주의: {w}")
    return "\n".join(lines)


def run(base, model, key, file, request, no_think=False, retries=2, verbose=True,
        engine=None, agent_md=None, temperature=0, constrain=False):
    engine = plotkit.engine_name(engine)
    agent_md = agent_md or ("AGENT_ECHARTS.md" if engine == "echarts" else "AGENT.md")
    system = (HERE / agent_md).read_text(encoding="utf-8") + SPEC_ONLY
    t_start = time.time()
    inspect = plotkit.dumps(plotkit.inspect_file(file))
    user = f"inspect 결과 (python plotkit.py inspect \"{Path(file).name}\"):\n" \
           f"{inspect.replace(str(file), Path(file).name)}\n\n사용자 요청:\n{request}"
    if no_think:
        user += " /no_think"
    messages = [{"role": "system", "content": system}, {"role": "user", "content": user}]
    schema = None
    if constrain:
        import spec_schema
        info = spec_schema.data_info([Path(file).name], Path(file).parent, inspect=True)
        schema = spec_schema.build(info, kinds=("curve",), hatch="echarts" if engine == "echarts" else "code")
    calls = []
    for attempt in range(retries + 1):
        reply, stats = call_llm(base, model, key, messages, temperature=temperature, schema=schema)
        calls.append(stats)
        try:
            spec = extract_json(reply)
            spec["file"] = str(Path(file).parent / Path(str(spec.get("file") or file)).name)
            res = plotkit.plot(spec, engine=engine)
            break
        except (plotkit.PlotkitError, json.JSONDecodeError, ValueError) as e:
            msg = f"plotkit error: {e.message} | hint: {e.hint}" if isinstance(e, plotkit.PlotkitError) \
                else f"your reply was not valid JSON: {e}"
            if verbose:
                print(f"[try {attempt + 1}] {msg}")
            messages += [{"role": "assistant", "content": reply},
                         {"role": "user", "content": msg + "\nReply with the corrected JSON spec only."}]
    else:
        return {"ok": False, "calls": calls, "seconds": round(time.time() - t_start, 1)}
    return {"ok": True, "spec": spec, "result": res, "calls": calls,
            "seconds": round(time.time() - t_start, 1)}


def read_prompts(path):
    """[(id, name, file, request)] from a file shaped like tests/AGENT_TEST_PROMPTS.md."""
    out, name, buf, inside = [], None, [], False
    for line in Path(path).read_text(encoding="utf-8").splitlines():
        if line.startswith("## "):
            name = line[3:].strip()
        elif line.startswith("```text"):
            inside, buf = True, []
        elif line.startswith("```") and inside:
            inside = False
            first = buf[0] if buf else ""
            file = first.split(":", 1)[1].strip() if first.startswith("파일:") else None
            out.append((name[:2], name, file, "\n".join(buf[1:] if file else buf).strip()))
        elif inside:
            buf.append(line)
    return out


def batch(a):
    sys.path.insert(0, str(HERE / "tests"))
    import score as scorer
    arm = a.arm or ("S" if plotkit.engine_name(a.engine) == "echarts" else "0")
    out = Path(a.out or f"results/batch_{arm}.csv")
    out.parent.mkdir(parents=True, exist_ok=True)
    only = {r.zfill(2) for r in a.only.split(",")} if a.only else None
    fields = ["time", "arm", "engine", "model", "repeat", "request", "pass", "first_try", "model_calls",
              "seconds", "prompt_tokens", "output_tokens", "thinking_tokens", "failed_checks", "spec"]
    new = not out.exists()
    passed = total = 0
    with open(out, "a", newline="", encoding="utf-8-sig") as fh:
        w = csv.DictWriter(fh, fieldnames=fields)
        if new:
            w.writeheader()
        for rep in range(1, a.repeat + 1):
            for rid, name, file, request in read_prompts(a.batch):
                if only and rid not in only:
                    continue
                file = str(HERE / file) if file and not Path(file).is_absolute() else file
                res = run(a.base_url, a.model, a.api_key, file, request, a.no_think, verbose=False,
                          engine=a.engine, agent_md=a.agent_md, temperature=a.temperature, constrain=a.constrain)
                spec = res.get("spec")
                if res["ok"]:
                    ok, why, _ = scorer.score(rid, spec, plotkit.engine_name(a.engine),
                                              HERE / "results" / "batch_out" / arm / f"{rid}_{rep}")
                else:
                    ok, why = False, ["no valid spec after retries"]
                calls = res["calls"]
                total += 1
                passed += ok
                w.writerow({"time": time.strftime("%Y-%m-%d %H:%M"), "arm": arm, "engine": plotkit.engine_name(a.engine),
                            "model": a.model, "repeat": rep, "request": rid, "pass": int(ok),
                            "first_try": int(ok and len(calls) == 1), "model_calls": len(calls),
                            "seconds": res["seconds"],
                            "prompt_tokens": sum(c["prompt_tokens"] or 0 for c in calls),
                            "output_tokens": sum(c["output_tokens"] or 0 for c in calls),
                            "thinking_tokens": sum(c["thinking_tokens"] or 0 for c in calls),
                            "failed_checks": " | ".join(why), "spec": json.dumps(spec, ensure_ascii=False) if spec else ""})
                fh.flush()
                print(f"{'PASS' if ok else 'FAIL'} {name:28s} {res['seconds']:6.1f}s  calls {len(calls)}"
                      + ("" if ok else "  " + "; ".join(why)))
    print(f"\n{passed}/{total} passed. Rows appended to {out}")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--base-url", default="http://localhost:11434/v1")
    ap.add_argument("--model", required=True)
    ap.add_argument("--api-key", default="")
    ap.add_argument("--file")
    ap.add_argument("--request")
    ap.add_argument("--no-think", action="store_true")
    ap.add_argument("--temperature", type=float, default=0.0, help="sampling temperature (default 0)")
    ap.add_argument("--engine", choices=plotkit.ENGINES, help="default: $PLOTKIT_ENGINE or matplotlib")
    ap.add_argument("--agent-md", help="system prompt file (default AGENT.md, or AGENT_ECHARTS.md for echarts)")
    ap.add_argument("--batch", help="run every request in this prompts file, e.g. tests/AGENT_TEST_PROMPTS.md")
    ap.add_argument("--only", help="with --batch: comma-separated request numbers, e.g. 07,20")
    ap.add_argument("--repeat", type=int, default=1, help="with --batch: run the whole set this many times")
    ap.add_argument("--constrain", action="store_true", help="constrained decoding: response_format with the spec's JSON Schema")
    ap.add_argument("--arm", help="with --batch: label for the results (default 0 or S from the engine)")
    ap.add_argument("--out", help="with --batch: CSV to append to (default results/batch_<arm>.csv)")
    a = ap.parse_args()
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    if a.batch:
        return batch(a)
    if not (a.file and a.request):
        ap.error("--file and --request are needed (or --batch)")
    out = run(a.base_url, a.model, a.api_key, a.file, a.request, a.no_think, engine=a.engine, agent_md=a.agent_md,
              temperature=a.temperature, constrain=a.constrain)
    if out["ok"]:
        print("spec:", json.dumps(out["spec"], ensure_ascii=False))
        print(summary_ko(out["result"]))
    else:
        print("실패: 모델이 올바른 spec을 만들지 못했습니다.")
    for i, c in enumerate(out["calls"], 1):
        print(f"model call {i}: {c['llm_s']}s, in {c['prompt_tokens']} / out {c['output_tokens']} tokens "
              f"(thinking {c['thinking_tokens']})")
    print(f"total {out['seconds']}s")


if __name__ == "__main__":
    main()
