"""Constrained decoding for the evaluation harnesses (eval/cnt_runs.py and eval/run_batch.py).

Arm names: a protocol arm with a suffix runs the same prompt and data preview, but the model's reply is constrained
by a JSON Schema built for that request (spec_schema.py):

  P-mpl+cd       full profile: the spec as prompts/v2 / AGENT.md describe it, decoded under its schema
  P-mpl+cdflat   flat profile: the spec as a flat settings list (FLAT_NOTE is added to the prompt); converted back
                 to a spec before plotkit sees it. The only profile the Anthropic API accepts (schema limits).

Backends:
  openai     any OpenAI-compatible server. The schema goes in "response_format" (llama.cpp server, vLLM, SGLang)
             or, with --cd-param json_schema, in llama.cpp's own top-level "json_schema" field.
  anthropic  the Messages API: output_config.format (structured outputs), output_config.effort, thinking disabled.
             Key from ANTHROPIC_API_KEY (or --api-key). Use it as a stand-in for a small local model, e.g.
             --model claude-haiku-5-5 --effort low.
"""
import json
import os
import re
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
import spec_schema as ss  # noqa: E402

PROFILES = {"cd": "full", "cd2": "full2", "cdabc": "fullabc", "cdflat": "flat"}
# cd2: full + sheets-before-chart branches, for engines that keep the schema's order (untested: OpenCode Go sorts keys).
# cdabc: the full schema + a prompt note to write keys alphabetically: OpenCode Go's structured outputs accept object
#        keys only in alphabetical order, so an optional key that sorts before one already written is dropped.
CD_NOTE = "\n\nYour reply is decoded under a JSON schema: write the JSON object itself, without the ```json fence."
ABC_NOTE = ("\n\n## Reply format (key order)\nWrite the JSON object itself, without the ```json fence, and write the keys of "
            "every object in alphabetical order, at every level: for example {\"asks\": [...], \"by\": ..., \"chart\": ..., "
            "\"file\": ..., \"sheets\": ..., \"title\": ..., \"x\": {\"col\": ..., \"max\": ..., \"min\": ...}, \"y\": {...}}. "
            "The reply is decoded under a schema that accepts keys only in that order; a key written out of order is lost.")


def parse_arm(arm):
    """'P-mpl+cdflat' -> ('P-mpl', 'flat'); 'P-mpl' -> ('P-mpl', None)."""
    base, _, suf = arm.partition("+")
    if suf and suf not in PROFILES:
        raise ValueError(f"unknown arm suffix +{suf} (use +cd, +cd2, +cdabc or +cdflat)")
    return base, PROFILES.get(suf)


def prompt_suffix(profile, note=False):
    """What a constrained arm adds to the system prompt: the flat format (needed), the alphabetical-order note
    (cdabc), the no-fence note (optional)."""
    if profile == "fullabc":
        return ABC_NOTE
    return (ss.FLAT_NOTE if profile == "flat" else "") + (CD_NOTE if (profile and note) else "")


def openai_fields(schema, param="response_format", strict=True):
    if schema is None:
        return {}
    if param == "json_schema":
        return {"json_schema": schema}
    return {"response_format": {"type": "json_schema", "json_schema": {"name": "plot_spec", "strict": strict, "schema": schema}}}


def first_json(text):
    """The JSON object in a reply (fenced or bare), or None."""
    text = re.sub(r"<think>.*?</think>", "", text or "", flags=re.S)
    m = re.search(r"```(?:json)?\s*\n(.*?)```", text, flags=re.S)
    raw = m.group(1) if m else text[text.find("{"): text.rfind("}") + 1]
    try:
        return json.loads(raw)
    except (json.JSONDecodeError, ValueError):
        return None


def conformance(text, schema):
    """(ok, first error) of a reply against a schema: does the model's own reply fit, as written?"""
    obj = first_json(text)
    if obj is None:
        return False, "not JSON"
    errs = ss.best_alternative_errors(obj, schema)
    return (not errs), (errs[0] if errs else "")


# =================================================================== Anthropic Messages API
ANTHROPIC_URL = os.environ.get("ANTHROPIC_BASE_URL", "https://api.anthropic.com")
ANTHROPIC_VERSION = os.environ.get("ANTHROPIC_VERSION", "2026-10-21")      # as in the effort docs
# some gateways (Cloudflare) refuse Python's default "Python-urllib" agent with HTTP 403 / error code 1010
USER_AGENT = os.environ.get("EVAL_USER_AGENT", "plotkit-eval/1.0")


def call_anthropic(model, key, messages, temperature, max_tokens, schema=None, effort=None, think=False,
                   timeout=600, base=None):
    """Same return as cnt_runs.call_llm: (text, reasoning, stats). The system prompt is cached (it is ~5k tokens)."""
    key = key or os.environ.get("ANTHROPIC_API_KEY", "")
    system = "\n\n".join(m["content"] for m in messages if m["role"] == "system")
    chat = [{"role": m["role"], "content": m["content"]} for m in messages if m["role"] != "system"]
    body = {"model": model, "max_tokens": max_tokens, "messages": chat, "temperature": temperature,
            "system": [{"type": "text", "text": system, "cache_control": {"type": "ephemeral"}}]}
    if not think:
        body["thinking"] = {"type": "disabled"}
    oc = {}
    if effort:
        oc["effort"] = effort
    if schema is not None:
        oc["format"] = {"type": "json_schema", "schema": schema}
    if oc:
        body["output_config"] = oc
    url = (base or ANTHROPIC_URL).rstrip("/") + "/v1/messages"
    headers = {"content-type": "application/json", "x-api-key": key,
               "anthropic-version": ANTHROPIC_VERSION, "user-agent": USER_AGENT}
    if "opencode.ai" in url:
        # OpenCode Go asks for a stable session id per conversation (routing, prompt caching): one id for all turns
        # and retries of a conversation, from its system prompt and first user message
        import uuid
        first = next((m["content"] for m in chat if m["role"] == "user"), "")
        headers["x-opencode-session"] = str(uuid.uuid5(uuid.NAMESPACE_URL, f"{model}\n{system}\n{first}"))
    req = urllib.request.Request(url, data=json.dumps(body, ensure_ascii=False).encode(), headers=headers)
    waits = [2, 5, 10, 20, 40, 60, 90]
    t0 = time.time()
    for i in range(len(waits) + 1):
        try:
            with urllib.request.urlopen(req, timeout=timeout) as r:
                d = json.loads(r.read())
            break
        except urllib.error.HTTPError as e:
            msg = e.read()[:600].decode("utf-8", "replace")
            if e.code not in (429, 500, 502, 503, 504, 529) or i == len(waits):
                raise RuntimeError(f"Anthropic HTTP {e.code}: {msg}") from None
        except (urllib.error.URLError, TimeoutError, ConnectionError):
            if i == len(waits):
                raise
        time.sleep(waits[i])
    dt = time.time() - t0
    text = "".join(b.get("text", "") for b in d.get("content", []) if b.get("type") == "text")
    reasoning = "".join(b.get("thinking", "") for b in d.get("content", []) if b.get("type") == "thinking")
    u = d.get("usage") or {}
    prompt = (u.get("input_tokens") or 0) + (u.get("cache_read_input_tokens") or 0) + (u.get("cache_creation_input_tokens") or 0)
    stats = {"llm_s": round(dt, 3), "prompt_tokens": prompt, "output_tokens": u.get("output_tokens"),
             "cached_tokens": u.get("cache_read_input_tokens"), "prompt_n": None, "prefill_ms": None, "decode_ms": None,
             "finish": d.get("stop_reason")}
    return text, reasoning, stats


# =================================================================== schemas per request
_CACHE = {}


def schemas(files, root, kinds, hatch, profile, asks="last", inspect=False, base_names=False):
    """(constrained schema or None, full schema for the conformance metric). Cached per request shape.
    base_names: the TGA harness shows and resolves files by their base name."""
    key = (tuple(map(str, files)), str(root), kinds, hatch, profile, asks, inspect, base_names)
    if key not in _CACHE:
        info = ss.data_info(files, root, inspect=inspect)
        if base_names:
            info["files"] = list(dict.fromkeys(Path(f).name for f in info["files"]))
        full = ss.build(info, kinds, hatch, "full", asks)
        con = None if profile is None else full if profile in ("full", "fullabc") else ss.build(info, kinds, hatch, profile, asks)
        _CACHE[key] = (con, full)
    return _CACHE[key]


def hatch_for(base_arm):
    """Which drawing hatch the arm's prompt teaches: matplotlib prompts "code", the ECharts prompt "echarts"."""
    return "echarts" if base_arm == "P-ec" else "code"
