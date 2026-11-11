"""Score a local LLM on tests/requests.json (Korean requests -> plotkit spec).

The model gets AGENT.md as the system prompt, plus the `inspect` result of the
test file and the Korean request, and must answer with the JSON spec. The spec
is checked key by key and then actually plotted.

Works with any OpenAI-compatible server (Ollama, LM Studio, vLLM, llama.cpp server):
    python tests/eval_llm.py --base-url http://localhost:11434/v1 --model <model name>
    python tests/eval_llm.py --base-url http://localhost:1234/v1 --model <model name> --only 02 10
    python tests/eval_llm.py --dry-run      # use the reference answers (checks this script)

Results: printed table + tests/eval_results.jsonl (raw model replies).
"""
import argparse
import json
import re
import sys
import tempfile
import time
from pathlib import Path

HERE = Path(__file__).parent
ROOT = HERE.parent
sys.path.insert(0, str(ROOT))
import plotkit  # noqa: E402

from run_agent import SPEC_ONLY, extract_json  # noqa: E402

TEST_X = {"value_at_x": (800.0, 8.01234), "peak": (559.6, 0.81234)}


def call_llm(base, model, key, system, user, max_tokens, timeout):
    import run_agent
    return run_agent.call_llm(base, model, key, [{"role": "system", "content": system},
                                                 {"role": "user", "content": user}], max_tokens, timeout)


def _same(a, b, key):
    if key.endswith("color") and a is not None and b is not None:
        from matplotlib.colors import to_hex
        try:
            return to_hex(plotkit._color(a, key)) == to_hex(plotkit._color(b, key))
        except Exception:  # noqa: BLE001
            return False
    if isinstance(a, (int, float)) and isinstance(b, (int, float)) and not isinstance(a, bool):
        return abs(float(a) - float(b)) < 1e-9
    if isinstance(a, list) and isinstance(b, list):
        if key == "output.format":
            return sorted(a) == sorted(b)
        return len(a) == len(b) and all(_same(x, y, key) for x, y in zip(a, b))
    if isinstance(a, str) and isinstance(b, str):
        return a.strip() == b.strip()
    return a == b


def _annot(spec, t):
    for name, a in spec["annotate"].items():
        if a.get("type") == t:
            return a
    return None


def check(spec, file_path, expect):
    """Return list of (check, ok, got)."""
    out = []
    tables, decimal = plotkit.read_tables(file_path, spec["read"])
    names = list(tables)
    for k, want in expect.items():
        try:
            if k == "sheets_resolved":
                got = plotkit._select_sheets(names, spec["sheets"], file_path)
                ok = got == want
            elif k.startswith("col["):
                role = k[4:-1]
                sheet = plotkit._select_sheets(names, spec["sheets"], file_path)[0]
                t = plotkit.analyze_table(tables[sheet], decimal, spec["read"].get("header_row"),
                                          spec["read"].get("data_start_row"))
                cols, _ = plotkit._resolve_columns(spec, t, sheet)
                got = cols[role]["letter"] if role in cols else None
                ok = got == want
            elif k == "absent":
                t = re.match(r"annot\[(\w+)\]", want).group(1)
                got = _annot(spec, t)
                ok = got is None
            elif k == "code_contains":
                got = spec.get("code") or ""
                ok = want in got
            elif k.startswith("annot["):
                t, field = re.match(r"annot\[(\w+)\]\.(\w+)", k).groups()
                a = _annot(spec, t)
                if a is None:
                    got, ok = "missing", False
                elif field.startswith("rendered"):
                    x, y = TEST_X.get(t, (a.get("x"), a.get("y")))
                    primary = "x" if t in ("peak", "vline") else "y"
                    got = plotkit._fmt(a.get("text", ""), x, y, primary)
                    ok = (got == want if field == "rendered" else
                          (want in got) if field == "rendered_contains" else (want not in got))
                else:
                    default = {"method": "nearest", "count": 1}.get(field)
                    got = a.get(field, default)
                    ok = _same(got, want, field)
            else:
                cur = spec
                for part in k.split("."):
                    cur = cur.get(part) if isinstance(cur, dict) else None
                got = cur
                ok = _same(got, want, k)
        except plotkit.PlotkitError as e:
            got, ok = f"error: {e.message}", False
        out.append((k, ok, got))
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--base-url", default="http://localhost:11434/v1")
    ap.add_argument("--model", default="")
    ap.add_argument("--api-key", default="")
    ap.add_argument("--dry-run", action="store_true", help="use reference specs instead of a model")
    ap.add_argument("--only", nargs="*", help="run only test ids starting with these, e.g. 02 10")
    ap.add_argument("--no-think", action="store_true", help='append "/no_think" (Qwen3-style hybrid models)')
    ap.add_argument("--max-tokens", type=int, default=4000)
    ap.add_argument("--timeout", type=int, default=600)
    args = ap.parse_args()
    if not args.dry_run and not args.model:
        ap.error("--model is required (or use --dry-run)")

    system = (ROOT / "AGENT.md").read_text(encoding="utf-8") + SPEC_ONLY
    cases = json.loads((HERE / "requests.json").read_text(encoding="utf-8"))
    if args.only:
        cases = [c for c in cases if any(c["id"].startswith(o) for o in args.only)]
    log = open(HERE / "eval_results.jsonl", "w", encoding="utf-8")
    passed_cases = total_checks = passed_checks = 0
    tmp = Path(tempfile.mkdtemp(prefix="plotkit_eval_"))
    timings = []
    for c in cases:
        fpath = HERE / "inputs" / c["file"]
        inspect = plotkit.dumps(plotkit.inspect_file(str(fpath)))
        inspect = inspect.replace(str(fpath), c["file"])
        user = f"inspect 결과 (python plotkit.py inspect \"{c['file']}\"):\n{inspect}\n\n사용자 요청:\n{c['request']}"
        if args.no_think:
            user += " /no_think"
        reply, err, stats = "", None, {"llm_s": 0.0}
        try:
            if args.dry_run:
                reply = "```json\n" + json.dumps(c["reference"], ensure_ascii=False) + "\n```"
            else:
                reply, stats = call_llm(args.base_url, args.model, args.api_key, system, user,
                                        args.max_tokens, args.timeout)
            spec_raw = extract_json(reply)
        except Exception as e:  # noqa: BLE001
            spec_raw, err = None, f"{type(e).__name__}: {e}"
        results = []
        plot_ok = False
        if spec_raw is not None:
            spec_run = dict(spec_raw)
            files = spec_run.get("file", c["file"])
            files = files if isinstance(files, list) else [files]
            spec_run["file"] = [str(HERE / "inputs" / Path(str(f)).name) for f in files]
            spec_run.setdefault("output", {})
            if isinstance(spec_run["output"], dict):
                spec_run["output"] = {**spec_run["output"], "dir": str(tmp / c["id"])}
            try:
                spec = plotkit.normalize_spec(spec_run)
                results = check(spec, str(fpath), c["expect"])
                t1 = time.time()
                res = plotkit.plot(spec_run)
                stats["plot_s"] = round(time.time() - t1, 2)
                plot_ok = res["ok"]
            except plotkit.PlotkitError as e:
                err = f"{e.message} | {e.hint}"
            except Exception as e:  # noqa: BLE001
                err = f"{type(e).__name__}: {e}"
        results.append(("plot runs", plot_ok, err or "ok"))
        n_ok = sum(ok for _, ok, _ in results)
        total_checks += len(results)
        passed_checks += n_ok
        case_ok = n_ok == len(results)
        passed_cases += case_ok
        timings.append(stats)
        tok = (f"  in {stats.get('prompt_tokens')} / out {stats.get('output_tokens')} tok"
               f" (thinking {stats.get('thinking_tokens')})" if not args.dry_run else "")
        print(f"{'PASS' if case_ok else 'FAIL'} {c['id']:28s} {n_ok:2d}/{len(results):2d} checks"
              f"  model {stats['llm_s']:5.1f}s  plot {stats.get('plot_s', 0):4.1f}s{tok}")
        for k, ok, got in results:
            if not ok:
                want = c["expect"].get(k, "")
                print(f"      x {k}: got {got!r}" + (f", want {want!r}" if want != "" else ""))
        log.write(json.dumps({"id": c["id"], "request": c["request"], "reply": reply, "spec": spec_raw,
                              "checks": results, "error": err, "stats": stats}, ensure_ascii=False, default=str) + "\n")
    log.close()
    print(f"\n{passed_cases}/{len(cases)} requests fully correct, {passed_checks}/{total_checks} checks passed")
    if timings and not args.dry_run:
        import statistics as st
        ls = [t["llm_s"] for t in timings]
        outs = [t.get("output_tokens") or 0 for t in timings]
        print(f"model time per request: median {st.median(ls):.1f}s, max {max(ls):.1f}s, total {sum(ls):.0f}s; "
              f"output tokens median {st.median(outs):.0f}")
    print(f"plots: {tmp}   replies: {HERE / 'eval_results.jsonl'}")


if __name__ == "__main__":
    main()
