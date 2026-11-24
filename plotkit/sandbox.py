"""Run model-written Python on data in a sandbox (bubblewrap: no network, read-only system, private /tmp).

    out = run(code, {"df": df}, ["df"])            # plotkit.charts data_code
    out = run(code, {"x": x, "y1": y1, ...}, ["x", "y1", "y2", "marks"])   # plotkit.core data_code

The code runs in a fresh Python with numpy and pandas (names np, pd), and the named outputs come back.

Safety:
- The inputs go in as a pickle the host writes; the outputs come back as JSON and .npy files the host reads with
  allow_pickle=False. The host never unpickles anything the model's code wrote.
- Without bubblewrap (Windows, macOS, Linux without bwrap) the code would run as a plain subprocess with the
  user's rights. That is refused with an error + hint unless the host allows it: allow_unsandboxed(True), the
  `allow_unsandboxed=True` argument of the plotkit API, or PLOTKIT_ALLOW_UNSANDBOXED=1. PLOTKIT_NO_SANDBOX=1 (the
  host has its own sandbox) skips bubblewrap and counts as allowing it.
"""
import contextlib
import contextvars
import json
import os
import pickle
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

import numpy as np

from .core import PlotkitError

_ALLOW = contextvars.ContextVar("plotkit_allow_unsandboxed", default=None)


def allow_unsandboxed(on=True):
    """Host switch: let data_code run without bubblewrap (as a plain subprocess). Off by default."""
    _ALLOW.set(bool(on))


@contextlib.contextmanager
def policy(allow_unsandboxed=None):
    """with policy(allow_unsandboxed=True): ...   (None keeps the current setting)"""
    tok = _ALLOW.set(bool(allow_unsandboxed)) if allow_unsandboxed is not None else None
    try:
        yield
    finally:
        if tok is not None:
            _ALLOW.reset(tok)


def mode():
    """"bwrap" | "plain" (allowed without a sandbox) | "refused"."""
    if os.environ.get("PLOTKIT_NO_SANDBOX"):
        return "plain"
    if shutil.which("bwrap"):
        return "bwrap"
    allowed = _ALLOW.get()
    if allowed is None:
        allowed = os.environ.get("PLOTKIT_ALLOW_UNSANDBOXED", "").strip().lower() in ("1", "true", "yes")
    return "plain" if allowed else "refused"


RUNNER = r'''
import json, pickle, sys
import numpy as np
try:
    import pandas as pd
except ImportError:
    pd = None
td = sys.argv[1]
env = pickle.load(open(td + "/in.pkl", "rb"))
env.update({"np": np, "pd": pd})
if pd is not None and isinstance(env.get("df"), pd.DataFrame):
    import re as _re

    def _norm(s):
        return _re.sub(r"[\s._\-:·,]+", "", str(s).lower())

    def _base(s):
        return _norm(_re.sub(r"[\(\[\{].*?[\)\]\}]", "", str(s)))

    class DF(pd.DataFrame):
        """df['등급'] also finds the column '등급 (A/B/C)': names may be given without their unit."""
        @property
        def _constructor(self):
            return DF

        def _match(self, key):
            if not isinstance(key, str) or key in self.columns:
                return key
            hits = [c for c in self.columns if _base(c) == _base(key) or _norm(c) == _norm(key)]
            return hits[0] if len(hits) == 1 else key

        def __getitem__(self, key):
            return super().__getitem__(self._match(key))

        def __setitem__(self, key, value):
            return super().__setitem__(self._match(key) if isinstance(key, str) and self._match(key) in self.columns else key, value)

    env["df"] = DF(env["df"])
names = sys.argv[2].split(",")
code = open(td + "/code.py", encoding="utf-8").read()
try:
    exec(compile(code, "<data_code>", "exec"), env)
except Exception as e:
    print(f"{type(e).__name__}: {e}", file=sys.stderr)
    sys.exit(3)


def plain(v):
    """JSON for marks and other small values: numbers, text, lists, dicts; missing values and NaN -> null."""
    if isinstance(v, dict):
        return {str(k): plain(x) for k, x in v.items()}
    if isinstance(v, (list, tuple)):
        return [plain(x) for x in v]
    if isinstance(v, np.ndarray):
        return plain(v.tolist())
    if pd is not None and (v is pd.NA or v is pd.NaT):
        return None
    if isinstance(v, np.generic):
        v = v.item()
    if isinstance(v, float) and (v != v or v in (float("inf"), float("-inf"))):
        return None
    if v is None or isinstance(v, (bool, int, float, str)):
        return v
    if hasattr(v, "isoformat"):
        return v.isoformat()
    return str(v)


def column(name, s):
    """One column (or the index) as JSON, with what the host needs to rebuild the same dtype."""
    d = {"name": name if name is None or (isinstance(name, (str, int, float)) and not isinstance(name, bool)) else
         plain(name.item()) if isinstance(name, np.generic) else " ".join(map(str, name)) if isinstance(name, tuple)
         else str(name), "dtype": str(s.dtype)}
    k = s.dtype.kind
    if isinstance(s.dtype, pd.CategoricalDtype):
        d.update(kind="category", categories=plain(list(s.cat.categories)), ordered=bool(s.cat.ordered),
                 values=[None if pd.isna(x) else plain(x) for x in s.astype(object)])
    elif k == "M":
        tz = str(s.dt.tz) if getattr(s.dt, "tz", None) is not None else None
        v = s.dt.tz_convert("UTC").dt.tz_localize(None) if tz else s
        d.update(kind="datetime", tz=tz, values=[None if pd.isna(x) else x.isoformat() for x in v])
    elif k == "m":
        d.update(kind="timedelta", values=[None if pd.isna(x) else x.total_seconds() for x in s])
    elif k in "biuf":
        d.update(kind="number", values=[None if pd.isna(x) or (k == "f" and not np.isfinite(x)) else plain(x) for x in s])
    else:
        d.update(kind="object", values=[None if x is None or (isinstance(x, float) and x != x) or x is pd.NA else plain(x)
                                        for x in s])
    return d


def frame(df):
    """A DataFrame as JSON: its columns and index, each with its dtype, so the host rebuilds the same frame."""
    if isinstance(df.index, pd.MultiIndex) or isinstance(df.columns, pd.MultiIndex):
        df = df.reset_index() if isinstance(df.index, pd.MultiIndex) else df
    cols = []
    for i in range(df.shape[1]):
        cols.append(column(df.columns[i], df.iloc[:, i]))
    idx = None if isinstance(df.index, pd.RangeIndex) and df.index.start == 0 and df.index.step == 1 and \
        df.index.name is None else column(df.index.name, df.index.to_series())
    return {"frame": cols, "index": idx, "rows": len(df)}


out, arrays = {}, {}
for k in names:
    v = env.get(k)
    if pd is not None and isinstance(v, pd.DataFrame):
        out[k] = frame(v)
    elif isinstance(v, np.ndarray) or (k in ("x", "y1", "y2") and v is not None):
        try:
            arrays[k] = np.asarray(v, dtype=float).ravel()
            out[k] = {"array": k + ".npy"}
        except (TypeError, ValueError):
            out[k] = {"bad": f"{type(v).__name__} that is not numbers"}
    else:
        out[k] = {"value": plain(v)}
for k, a in arrays.items():
    np.save(td + "/" + k + ".npy", a, allow_pickle=False)
with open(td + "/out.json", "w", encoding="utf-8") as fh:
    json.dump(out, fh, ensure_ascii=False, allow_nan=False)
'''


def _series(c):
    """One column the sandbox wrote, back as a Series of the same dtype (as far as JSON allows)."""
    import pandas as pd
    v, k, dt = c["values"], c["kind"], c["dtype"]
    if k == "datetime":
        s = pd.to_datetime(pd.Series(v, dtype=object))
        if c.get("tz"):
            return s.dt.tz_localize("UTC").dt.tz_convert(c["tz"])
        try:
            return s.astype(dt)
        except (TypeError, ValueError):
            return s
    if k == "timedelta":
        return pd.to_timedelta(pd.Series(v, dtype=float), unit="s")
    if k == "category":
        return pd.Series(pd.Categorical(v, categories=c["categories"], ordered=c["ordered"]))
    try:
        return pd.Series(v, dtype=dt if k == "number" or dt in ("object", "string", "str") else object)
    except (TypeError, ValueError):                 # e.g. missing values in a numpy int column
        return pd.Series(v, dtype=float if k == "number" else object)


def _frame(d):
    """The DataFrame the sandbox wrote (see RUNNER frame())."""
    import pandas as pd
    cols = [_series(c) for c in d["frame"]]
    df = pd.concat(cols, axis=1, ignore_index=True) if cols else pd.DataFrame(index=range(d.get("rows", 0)))
    df.columns = [c["name"] for c in d["frame"]] if cols else df.columns
    if d.get("index"):
        df.index = pd.Index(_series(d["index"]), name=d["index"]["name"])
    return df


def _read(td, names):
    raw = json.loads((td / "out.json").read_text(encoding="utf-8"))
    out = {}
    for k in names:
        d = raw.get(k) or {"value": None}
        if "array" in d:
            out[k] = np.load(td / d["array"], allow_pickle=False)
        elif "frame" in d:
            out[k] = _frame(d)
        elif "bad" in d:
            out[k] = _Bad(d["bad"])
        else:
            out[k] = d.get("value")
    return out


class _Bad(str):
    """An output the code left as something that is not numbers (the caller reports it)."""


def _python_binds():
    """bwrap arguments that keep this Python visible when it lives under /tmp (a venv there, a PyInstaller one-file
    build), which the sandbox otherwise covers with an empty tmpfs. Read-only."""
    out = []
    paths = (sys.prefix, sys.base_prefix, str(Path(sys.executable).parent))
    for p in dict.fromkeys([*paths, *(str(Path(x).resolve()) for x in paths)]):
        if p == "/tmp" or p.startswith("/tmp/"):
            out += ["--ro-bind", p, p]
    return out


def run(code, inputs, outputs, timeout=60, hint=""):
    m = mode()
    if m == "refused":
        raise PlotkitError("data_code needs a sandbox (bubblewrap), and none is available here",
                           "draw it with keys only (no data_code), or say in asks that it cannot be done; "
                           "the host can allow unsandboxed data_code with allow_unsandboxed=True")
    with tempfile.TemporaryDirectory(prefix="plotkit_code_") as td:
        td = Path(td)
        (td / "runner.py").write_text(RUNNER, encoding="utf-8")
        (td / "code.py").write_text(code, encoding="utf-8")
        with open(td / "in.pkl", "wb") as fh:
            pickle.dump(inputs, fh)
        cmd = [sys.executable, "-I", str(td / "runner.py"), str(td), ",".join(outputs)]
        if m == "bwrap":
            cmd = ["bwrap", "--ro-bind", "/", "/", "--dev", "/dev", "--proc", "/proc", "--tmpfs", "/tmp", *_python_binds(),
                   "--bind", str(td), str(td), "--unshare-net", "--die-with-parent", "--chdir", str(td), *cmd]
        try:
            p = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout,
                               env={"PATH": os.environ.get("PATH", "/usr/bin:/bin") if m == "plain" else "/usr/bin:/bin",
                                    "HOME": str(td), "LANG": "C.UTF-8", **({"SYSTEMROOT": os.environ["SYSTEMROOT"]}
                                                                       if "SYSTEMROOT" in os.environ else {})})
        except subprocess.TimeoutExpired:
            raise PlotkitError(f"data_code took longer than {timeout} s", "simplify the code")
        if p.returncode != 0:
            err = (p.stderr or "").strip().splitlines()
            raise PlotkitError(f"data_code failed: {err[-1] if err else p.returncode}", hint)
        try:
            return _read(td, outputs)
        except (OSError, ValueError, KeyError) as e:
            raise PlotkitError(f"data_code left something that cannot be read back: {e}", hint)
