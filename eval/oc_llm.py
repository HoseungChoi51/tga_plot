"""Qwen3.8 Flash through opencode, for runs that should not wait on strixhalo.

A private `opencode serve` (127.0.0.1, own password) relays each call to the opencode-go provider through
/api/experimental/generate/text. That endpoint takes one prompt with no system role, no temperature and no token
counts, so the chat is flattened into one prompt and the provider's default temperature applies. Session and agent
calls are not used: they add opencode's coding-agent prompt and its instruction files.

    OPENCODE_SERVER_PASSWORD=$(cat pass) opencode serve --hostname 127.0.0.1 --port 4917 &
    OC_PASS_FILE=pass python eval/cnt_runs_oc.py ...
"""
import base64
import json
import os
import time
import urllib.error
import urllib.request
from pathlib import Path

URL = os.environ.get("OC_URL", "http://127.0.0.1:4917")
MODEL = os.environ.get("OC_MODEL", "opencode-go/qwen3.8-flash")


def _auth():
    pw = Path(os.path.expanduser(os.environ["OC_PASS_FILE"])).read_text().strip()
    return "Basic " + base64.b64encode(f"opencode:{pw}".encode()).decode()


def flatten(messages):
    """System prompt first, then the request; a longer chat becomes a transcript ending at the last user message."""
    system = "\n\n".join(m["content"] for m in messages if m["role"] == "system")
    chat = [m for m in messages if m["role"] != "system"]
    if len(chat) == 1:
        return f"{system}\n\n---\n\n{chat[0]['content']}"
    parts = [system, "---", "The conversation so far is below. Reply as the assistant to the last [user] message, "
             "in the same reply format as your earlier replies."]
    parts += [f"[{m['role']}]\n{m['content']}" for m in chat]
    return "\n\n".join(parts)


def call_llm(base, model, key, messages, temperature, max_tokens, timeout=600, think=False):
    """Same signature and return as cnt_runs.call_llm; base, key, temperature and max_tokens are not used."""
    provider, mid = (model if "/" in model else MODEL).split("/", 1)
    body = json.dumps({"prompt": flatten(messages),
                       "model": {"id": mid, "providerID": provider, "variant": "low" if think else "none"}},
                      ensure_ascii=False).encode()
    req = urllib.request.Request(URL + "/api/experimental/generate/text", data=body,
                                 headers={"Content-Type": "application/json", "Authorization": _auth()})
    waits = [2, 5, 10, 20, 40, 60]
    t0 = time.time()
    for i in range(len(waits) + 1):
        try:
            with urllib.request.urlopen(req, timeout=timeout) as r:
                text = json.loads(r.read())["data"]["text"]
            break
        except urllib.error.HTTPError as e:
            if e.code not in (429, 500, 502, 503, 504) or i == len(waits):
                raise RuntimeError(f"opencode HTTP {e.code}: {e.read()[:300]!r}") from None
        except (urllib.error.URLError, TimeoutError, ConnectionError):
            if i == len(waits):
                raise
        time.sleep(waits[i])
    dt = time.time() - t0
    return text, "", {"llm_s": round(dt, 3), "prompt_tokens": None, "output_tokens": None, "cached_tokens": None,
                      "prompt_n": None, "prefill_ms": None, "decode_ms": None, "finish": None,
                      "prompt_chars": len(body), "output_chars": len(text), "attempts": i + 1}
