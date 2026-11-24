"""python -m plotkit COMMAND ...

  prompt   [--engine echarts|matplotlib]          the system prompt
  preview  FILE ... [--base DIR]                  the data preview the model sees
  validate SPEC.json|--json '{...}' [--base DIR]  check a spec: {"ok", "kind", "spec", "warnings", "not_done"}
  options  SPEC.json|--json '{...}' [--base DIR]  the live ECharts options and the shared result
  render   SPEC.json|--json '{...}' --out DIR [--format png,pdf] [--engine echarts|matplotlib] [--summary-csv]
  schema   [--json | --md]                        the spec as JSON Schema / key reference (no flag: the old key list)
  serve                                           JSON lines on stdin/stdout, for an app that runs Python as a sidecar

  inspect FILE | plot SPEC.json | example         the older command line (plotkit.core), unchanged

Errors print {"ok": false, "error": ..., "hint": ...} and exit with code 2. --allow-unsandboxed lets data_code run
without bubblewrap (see plotkit.sandbox).

serve reads one request per line, {"id": 1, "method": "options", "params": {"spec": {...}, "base": "..."}}, and
answers one line, {"id": 1, "ok": true, "result": ...} or {"id": 1, "ok": false, "error": ..., "hint": ...}.
Methods: prompt {engine}, preview {files, base}, validate {spec, base}, options {spec, base}, render {spec, out_dir,
formats, engine, base, summary_csv}, schema {}, retry_message {error, hint}, parse_reply {text}, request_options
{reasoning, provider, model}. allow_unsandboxed in params applies to that request.
"""
import json
import sys
from pathlib import Path

from . import agent, api, core, schema
from .core import PlotkitError

NEW = ("prompt", "preview", "validate", "options", "option", "render", "schema", "serve")


def _spec(rest):
    if not rest:
        raise PlotkitError("give a spec: SPEC.json or --json '{...}'")
    if rest[0] == "--json":
        try:
            return json.loads(" ".join(rest[1:]))
        except json.JSONDecodeError as e:
            raise PlotkitError(f"the JSON is invalid: {e}", "check quotes and commas")
    try:
        return json.loads(Path(rest[0]).read_text(encoding="utf-8-sig"))
    except FileNotFoundError:
        raise PlotkitError(f"spec file not found: {rest[0]}")
    except json.JSONDecodeError as e:
        raise PlotkitError(f"{rest[0]} is not valid JSON: {e}", "check quotes and commas")


def _opt(rest, name, default=None, flag=False):
    """Take --name [value] out of rest (changed in place)."""
    if name not in rest:
        return default
    i = rest.index(name)
    if flag:
        del rest[i]
        return True
    if i + 1 >= len(rest):
        raise PlotkitError(f"{name} needs a value")
    v = rest[i + 1]
    del rest[i:i + 2]
    return v


METHODS = {
    "prompt": lambda p: agent.system_prompt(p.get("engine", "echarts")),
    "preview": lambda p: agent.preview(p["files"], p.get("base")),
    "validate": lambda p: api.validate(p["spec"], p.get("base"), allow_unsandboxed=p.get("allow_unsandboxed")),
    "options": lambda p: api.echarts_options(p["spec"], p.get("base"), full=True,
                                             allow_unsandboxed=p.get("allow_unsandboxed")),
    "render": lambda p: api.render(p["spec"], p["out_dir"], p.get("formats", ["png"]), p.get("engine", "echarts"),
                                   p.get("base"), summary_csv=p.get("summary_csv", False),
                                   allow_unsandboxed=p.get("allow_unsandboxed")),
    "schema": lambda p: schema.schema(),
    "retry_message": lambda p: agent.retry_message(p),
    "parse_reply": lambda p: agent.parse_reply(p["text"]),
    "request_options": lambda p: agent.request_options(p.get("reasoning", False), p.get("provider", "openai-compatible"),
                                                       p.get("model")),
    "first_message": lambda p: agent.first_message(p["request"], p["files"], p.get("base")),
    "followup_message": lambda p: agent.followup_message(p["request"], p.get("last_spec")),
}


def serve(stdin=None, stdout=None):
    """Answer JSON-line requests until stdin closes. One request at a time, in order."""
    stdin = stdin or sys.stdin
    stdout = stdout or sys.stdout
    for line in stdin:
        line = line.strip()
        if not line:
            continue
        rid = None
        try:
            req = json.loads(line)
            rid = req.get("id")
            method = req.get("method")
            if method not in METHODS:
                raise PlotkitError(f"unknown method {method!r}", "methods: " + ", ".join(METHODS))
            out = {"id": rid, "ok": True, "result": METHODS[method](req.get("params") or {})}
        except PlotkitError as e:
            out = {"id": rid, "ok": False, "error": e.message, "hint": e.hint}
        except (json.JSONDecodeError, KeyError, TypeError, ValueError) as e:
            out = {"id": rid, "ok": False, "error": f"bad request: {type(e).__name__}: {e}", "hint": "see python -m plotkit --help"}
        except Exception as e:  # noqa: BLE001 - keep the sidecar alive; the app sees the error
            out = {"id": rid, "ok": False, "error": f"{type(e).__name__}: {e}", "hint": "this is a plotkit bug; please report it"}
        stdout.write(json.dumps(out, ensure_ascii=False, default=str) + "\n")
        stdout.flush()


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    if hasattr(sys.stdin, "reconfigure"):
        sys.stdin.reconfigure(encoding="utf-8")
    if not argv or argv[0] in ("-h", "--help", "help"):
        print(__doc__)
        return 0
    cmd, rest = argv[0], argv[1:]
    if cmd not in NEW:
        return core.main(argv)
    allow = True if _opt(rest, "--allow-unsandboxed", flag=True) else None
    try:
        if cmd == "prompt":
            sys.stdout.write(agent.system_prompt(_opt(rest, "--engine", "echarts")))
            return 0
        if cmd == "schema":
            if _opt(rest, "--json", flag=True):
                sys.stdout.write(schema.dumps())
            elif _opt(rest, "--md", flag=True):
                sys.stdout.write(schema.markdown())
            else:
                return core.main(["schema"])
            return 0
        if cmd == "serve":
            serve()
            return 0
        base = _opt(rest, "--base")
        if cmd == "preview":
            if not rest:
                raise PlotkitError("usage: python -m plotkit preview FILE ... [--base DIR]")
            sys.stdout.write(agent.preview(rest, base) + "\n")
            return 0
        if cmd == "validate":
            out = api.validate(_spec(rest), base, allow_unsandboxed=allow)
        elif cmd in ("options", "option"):
            out = api.echarts_options(_spec(rest), base, full=True, allow_unsandboxed=allow)
        else:
            out_dir = _opt(rest, "--out")
            if not out_dir:
                raise PlotkitError("render needs --out DIR")
            fmts = _opt(rest, "--format", "png").split(",")
            engine = _opt(rest, "--engine", "echarts")
            csv = bool(_opt(rest, "--summary-csv", flag=True))
            out = api.render(_spec(rest), out_dir, fmts, engine, base, summary_csv=csv, allow_unsandboxed=allow)
    except PlotkitError as e:
        out = {"ok": False, "error": e.message, "hint": e.hint}
    sys.stdout.write(json.dumps(out, ensure_ascii=False, indent=1, default=str) + "\n")
    return 0 if out.get("ok") else 2


if __name__ == "__main__":
    sys.exit(main())
