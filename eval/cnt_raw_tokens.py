"""Raw-code reply length in Qwen tokens: count a sample of the opencode raw-code replies with the deployed model's tokenizer
(strixhalo has no /tokenize, so each reply is sent as a 1-token chat request and the empty-message prompt size is subtracted)
and scale the per-turn character counts. Run when strixhalo is idle.

    EVAL_API_KEY_FILE=~/.config/pi/strix.key python eval/cnt_raw_tokens.py   -> eval/results/cnt_raw_tokens.json
"""
import json
import os
import random
import statistics
import urllib.request
from pathlib import Path

HERE = Path(__file__).resolve().parent
key = Path(os.path.expanduser(os.environ["EVAL_API_KEY_FILE"])).read_text().strip()
replies, turns = [], []
for rec in sorted((HERE / "results" / "runs" / "cnt_sealed_oc" / "R-mpl").glob("*/record.json")):
    for t in json.loads(rec.read_text(encoding="utf-8"))["turns"]:
        rs = [c["reply"] for c in t["calls"] if "reply" in c]
        replies += rs
        turns.append(sum(len(r) for r in rs))
sample = random.Random(3).sample(replies, 40)


def prompt_tokens(text):
    body = {"model": "qwen3.8-flash-next", "messages": [{"role": "user", "content": text}], "max_tokens": 1,
            "chat_template_kwargs": {"enable_thinking": False}}
    req = urllib.request.Request("http://strixhalo:8084/v1/chat/completions", data=json.dumps(body).encode(),
                                 headers={"Content-Type": "application/json", "Authorization": f"Bearer {key}"})
    with urllib.request.urlopen(req, timeout=120) as r:
        return json.loads(r.read())["usage"]["prompt_tokens"]


base = prompt_tokens("")
ratios = [len(text) / (prompt_tokens(text) - base) for text in sample]
cpt = statistics.median(ratios)
q = lambda xs, p: sorted(xs)[int(p * (len(xs) - 1))]  # noqa: E731
out = {"chars_per_token": round(cpt, 3), "replies": len(replies), "turns": len(turns),
       "reply_tokens_p50": round(statistics.median(len(r) for r in replies) / cpt),
       "turn_tokens_p50": round(statistics.median(turns) / cpt), "turn_tokens_p90": round(q(turns, .9) / cpt)}
(HERE / "results" / "cnt_raw_tokens.json").write_text(json.dumps(out, indent=1), encoding="utf-8")
print(out)
