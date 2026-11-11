#!/usr/bin/env python3
"""Minimal local agent: one Korean request -> plot, with a local LLM.

Steps: inspect the file (no LLM) -> ONE model call writes the spec -> plotkit
draws it -> if plotkit reports an error, the error goes back to the model
(at most 2 retries) -> a Korean summary is printed from the result (no LLM).

    python run_agent.py --base-url http://localhost:11434/v1 --model <name> \\
        --file TGA.xlsx --request "1006R1-V normal 시트, x축 틱 간격 200, 피크 표시 2개"

Works with any OpenAI-compatible server (Ollama, LM Studio, vLLM, llama.cpp).
Add --no-think for Qwen3-style models to skip the thinking phase (faster).
"""
import argparse
import json
import re
import sys
import time
import urllib.request
from pathlib import Path

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE))
import plotkit  # noqa: E402

SPEC_ONLY = """

## Test mode
You cannot run commands in this conversation. The `inspect` result is given below.
Do step 2 only: reply with the JSON spec for the user's request, inside one ```json block, and nothing else.
Use the file name exactly as shown in the inspect result."""


def call_llm(base, model, key, messages, max_tokens=4000, timeout=600):
    body = {"model": model, "temperature": 0, "max_tokens": max_tokens, "messages": messages}
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


def run(base, model, key, file, request, no_think=False, retries=2, verbose=True):
    system = (HERE / "AGENT.md").read_text(encoding="utf-8") + SPEC_ONLY
    t_start = time.time()
    inspect = plotkit.dumps(plotkit.inspect_file(file))
    user = f"inspect 결과 (python plotkit.py inspect \"{Path(file).name}\"):\n" \
           f"{inspect.replace(str(file), Path(file).name)}\n\n사용자 요청:\n{request}"
    if no_think:
        user += " /no_think"
    messages = [{"role": "system", "content": system}, {"role": "user", "content": user}]
    calls = []
    for attempt in range(retries + 1):
        reply, stats = call_llm(base, model, key, messages)
        calls.append(stats)
        try:
            spec = extract_json(reply)
            spec["file"] = str(Path(file).parent / Path(str(spec.get("file") or file)).name)
            res = plotkit.plot(spec)
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


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--base-url", default="http://localhost:11434/v1")
    ap.add_argument("--model", required=True)
    ap.add_argument("--api-key", default="")
    ap.add_argument("--file", required=True)
    ap.add_argument("--request", required=True)
    ap.add_argument("--no-think", action="store_true")
    a = ap.parse_args()
    out = run(a.base_url, a.model, a.api_key, a.file, a.request, a.no_think)
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
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
