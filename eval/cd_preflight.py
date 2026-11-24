"""Check a server really does constrained decoding before spending a run on it (a few short calls).

    python eval/cd_preflight.py --base-url http://strixhalo:8084/v1 --model qwen3.8-flash-next     # llama.cpp / vLLM
    python eval/cd_preflight.py --backend anthropic --model claude-haiku-5-5 --effort low           # ANTHROPIC_API_KEY

1. probe     a one-field schema with a const value the prompt does not mention. A server that ignores the schema
             answers the prompt instead; one that enforces it can only write {"probe": "cd-ok-7f3"}.
2. schemas   every distinct schema the runs will send (CNT dev + sealed requests, both hatches, TGA Set A/B) is sent
             once with a short request: HTTP 200 means the server compiled it, and the reply must parse and fit.
             The sealed requests' text is never read or printed: only their file lists are used.
Exit status 0 only if everything passed.
"""
import argparse
import json
import os
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(HERE))
import cd  # noqa: E402
import spec_schema as ss  # noqa: E402

PROBE = {"type": "object", "properties": {"probe": {"const": "cd-ok-7f3"}}, "required": ["probe"],
         "additionalProperties": False}


def call(a, key, messages, schema, max_tokens):
    if a.backend == "anthropic":
        return cd.call_anthropic(a.model, key, messages, 0.0, max_tokens, schema=schema, effort=a.effort,
                                 base=a.base_url if a.base_url_set else None)
    import cnt_runs
    return cnt_runs.call_llm(a.base_url, a.model, key, messages, 0.0, max_tokens, schema=schema, cd_param=a.cd_param)


def request_shapes(profiles):
    """(label, files, root, kinds, hatch, profile, inspect, base_names) for every schema the harnesses build."""
    out = []
    for split in ("dev", "sealed"):
        p = HERE / "cnt" / split / "requests.json"
        if not p.exists():
            continue
        items = json.loads(p.read_text(encoding="utf-8"))
        items = items["items"] if isinstance(items, dict) else items
        for files in sorted({tuple(i["files"]) for i in items}):
            for hatch in ("code", "echarts"):
                for prof in profiles:
                    out.append((f"cnt {files[0]}{' +' + str(len(files) - 1) if len(files) > 1 else ''} {hatch} {prof}",
                                list(files), HERE / "cnt", ("curve", "chart"), hatch, prof, False, False))
    import run_batch
    for files in sorted({tuple(r["files"]) for r in run_batch.requests()}):
        for hatch in ("code", "echarts"):
            for prof in profiles:
                out.append((f"tga {Path(files[0]).name} {hatch} {prof}", [Path(f).name for f in files], Path(files[0]).parent,
                            ("curve",), hatch, prof, True, True))
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--backend", choices=("openai", "anthropic"), default="openai")
    ap.add_argument("--base-url", default="http://strixhalo:8084/v1")
    ap.add_argument("--model", default="qwen3.8-flash-next")
    ap.add_argument("--cd-param", choices=("response_format", "json_schema"), default="response_format")
    ap.add_argument("--effort")
    ap.add_argument("--profiles", default=None, help="default: full,flat (openai) or flat (anthropic)")
    ap.add_argument("--asks", choices=("last", "first"), default="last")
    ap.add_argument("--max", type=int, default=0, help="send at most this many schemas (0 = all)")
    a = ap.parse_args()
    a.base_url_set = any(x == "--base-url" or x.startswith("--base-url=") for x in sys.argv)
    key = Path(os.path.expanduser(os.environ["EVAL_API_KEY_FILE"])).read_text().strip() if os.environ.get("EVAL_API_KEY_FILE") \
        else os.environ.get("ANTHROPIC_API_KEY", "") if a.backend == "anthropic" else ""
    profiles = (a.profiles or ("flat" if a.backend == "anthropic" else "full,flat")).split(",")
    ok_all = True

    msgs = [{"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "Say hello in Korean, in one short sentence."}]
    try:
        text, _, st = call(a, key, msgs, PROBE, 40)
        enforced = cd.first_json(text) == {"probe": "cd-ok-7f3"}
    except Exception as e:  # noqa: BLE001
        text, enforced, st = f"ERROR {e}", False, {}
    print(f"probe: {'ENFORCED' if enforced else 'NOT ENFORCED'}  reply={text[:120]!r}  {st.get('llm_s')} s")
    if not enforced:
        print("  The server does not apply the schema. llama.cpp: try --cd-param json_schema; vLLM: start it with "
              "structured outputs enabled. Do not run +cd arms until this passes.")
        return 1

    shapes = request_shapes(profiles)
    if a.max:
        shapes = shapes[:a.max]
    seen = set()
    for label, files, root, kinds, hatch, prof, inspect, base_names in shapes:
        con, _ = cd.schemas(files, root, kinds, hatch, prof, a.asks, inspect=inspect, base_names=base_names)
        h = json.dumps(con, sort_keys=True)
        if h in seen:
            continue
        seen.add(h)
        lim = ss.limits(con)
        if a.backend == "anthropic" and not lim["anthropic_ok"] and not a.base_url_set:   # limits of Anthropic's own API
            print(f"SKIP {label}: over the Anthropic limits {lim}")
            ok_all = False
            continue
        sys_p = "Reply with a plot spec as JSON." + (ss.FLAT_NOTE if prof == "flat" else "")
        msgs = [{"role": "system", "content": sys_p},
                {"role": "user", "content": f"파일 {files[0]}: 첫 번째 시트를 기본 설정으로 그려줘."}]
        t0 = time.time()
        try:
            text, _, st = call(a, key, msgs, con, 600)
            obj = cd.first_json(text)
            errs = ["not JSON"] if obj is None else ss.best_alternative_errors(obj, con)
            if obj is not None and not errs and prof == "flat":
                ss.flat_to_spec(obj)
            res = "ok" if not errs else f"REPLY DOES NOT FIT: {errs[0]}"
            if errs and st.get("finish") in ("length", "max_tokens"):
                res = "ok (cut at max_tokens; schema compiled)"
                errs = []
        except Exception as e:  # noqa: BLE001
            res, errs = f"FAILED: {str(e)[:300]}", ["x"]
        ok_all &= not errs
        print(f"{'ok ' if not errs else 'BAD'} {label:60s} {time.time() - t0:5.1f} s  {res if errs else ''}")
    print("all passed" if ok_all else "some schemas failed: see above")
    return 0 if ok_all else 1


if __name__ == "__main__":
    sys.exit(main())
