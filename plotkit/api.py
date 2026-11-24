"""What an app calls: check a spec, get the live ECharts options, export files.

    plotkit.validate(spec)              -> {"ok", "kind", "spec" (normalized), "warnings", "not_done"}
    plotkit.echarts_options(spec)       -> [option, ...]   (full=True: the shared result with "options")
    plotkit.render(spec, out_dir)       -> the shared result with "saved"

Every function raises plotkit.PlotkitError(message, hint) when the spec cannot be drawn; send it back to the model
with plotkit.retry_message(e). base: the folder the spec's file names are relative to (default: the current one).
allow_unsandboxed: let data_code run without bubblewrap for this call (see plotkit.sandbox); None keeps the
process setting (off unless PLOTKIT_ALLOW_UNSANDBOXED=1).
"""
from pathlib import Path

from . import charts, core, sandbox
from .core import PlotkitError

FILE_KEYS = frozenset({"file"} | {k for k, v in core.TOP_ALIASES.items() if v == "file"}
                      | {k for k, v in charts.TOP_ALIASES.items() if v == "file"})


def with_base(spec, base):
    """A copy of the spec whose relative file names are joined to base (other keys untouched)."""
    if base is None or not isinstance(spec, dict):
        return spec
    out = dict(spec)
    for k, v in spec.items():
        if str(k).lower() in FILE_KEYS:
            join = (lambda f: str(Path(base) / f) if isinstance(f, str) and not Path(f).is_absolute() else f)
            out[k] = [join(f) for f in v] if isinstance(v, list) else join(v)
    return out


def _clean(obj):
    """JSON-safe copy of a normalized spec: no private keys, numpy values as plain numbers."""
    if isinstance(obj, dict):
        return {str(k): _clean(v) for k, v in obj.items() if not str(k).startswith("_")}
    if isinstance(obj, (list, tuple)):
        return [_clean(v) for v in obj]
    if hasattr(obj, "item") and not isinstance(obj, (str, bytes)):
        try:
            return obj.item()
        except (TypeError, ValueError):
            pass
    return obj if obj is None or isinstance(obj, (bool, int, float, str)) else str(obj)


def validate(spec, base=None, *, allow_unsandboxed=None):
    """Check a spec against the data without drawing (files, sheets and columns are read; data_code runs).
    Returns {"ok": True, "kind", "spec": the normalized spec, "warnings", "not_done"}; raises PlotkitError."""
    with sandbox.policy(allow_unsandboxed):
        kind, s = core.route(with_base(spec, base))
        if kind == "chart":
            norm = charts.normalize(s)
            model = charts.layout(norm, charts.build_model(norm, charts.load_frame(norm)))
            warnings = list(model["notes"])
        else:
            norm = core.normalize_spec(s)
            _, warnings = core.build_jobs(norm)
    return {"ok": True, "kind": kind, "spec": _clean(norm), "warnings": warnings, "not_done": core.not_done(norm)}


def echarts_options(spec, base=None, *, full=False, allow_unsandboxed=None):
    """The live ECharts options of a spec, one per figure, without writing files. Labels are tied to the data, with
    tooltip and zoom. Chart options may hold "__fmt__..." / "__histbar__" / "__errorbar__" markers: the page turns
    them into functions with revive() from plotkit/js/revive.mjs before setOption. Curves need Node (plotkit/js/live.mjs).
    full=True returns the shared result {"ok", "kind", "engine", "options", "saved": [], "warnings", "not_done", "values"}."""
    with sandbox.policy(allow_unsandboxed):
        kind, s = core.route(with_base(spec, base))
        if kind == "chart":
            res = charts.live_result(s)
        else:
            from . import echarts
            res = echarts.live_result(s)
    return res if full else res["options"]


def render(spec, out_dir, formats=("png",), engine="echarts", base=None, *, summary_csv=False, allow_unsandboxed=None):
    """Draw a spec to files in out_dir (created). formats: png, svg, pdf, jpg, tif (PDF on ECharts needs Chromium).
    Returns the shared result {"ok", "kind", "engine", "saved", "warnings", "not_done", "values", ...}."""
    with sandbox.policy(allow_unsandboxed):
        return core.plot(with_base(spec, base), engine=engine, out_dir=out_dir, formats=list(formats),
                         summary_csv=summary_csv)
