"""Run model-written Python on data in a sandbox (bubblewrap: no network, read-only system, private /tmp).

    out = run(code, {"df": df}, ["df"])            # plotkit.charts data_code
    out = run(code, {"x": x, "y1": y1, ...}, ["x", "y1", "y2", "marks"])   # plotkit data_code

The inputs are pickled into a temporary folder, the code runs in a fresh Python with numpy and pandas
(names np, pd), and the named outputs come back. Without bwrap (or with PLOTKIT_NO_SANDBOX=1) it runs in a
plain subprocess.
"""
import os
import pickle
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

from .core import PlotkitError

RUNNER = r'''
import pickle, sys
import numpy as np
try:
    import pandas as pd
except ImportError:
    pd = None
env = pickle.load(open(sys.argv[1], "rb"))
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
names = sys.argv[4].split(",")
code = open(sys.argv[2], encoding="utf-8").read()
try:
    exec(compile(code, "<data_code>", "exec"), env)
except Exception as e:
    print(f"{type(e).__name__}: {e}", file=sys.stderr)
    sys.exit(3)
out = {k: env.get(k) for k in names}
if pd is not None and isinstance(out.get("df"), pd.DataFrame):
    out["df"] = pd.DataFrame(out["df"])
pickle.dump(out, open(sys.argv[3], "wb"))
'''


def run(code, inputs, outputs, timeout=60, hint=""):
    with tempfile.TemporaryDirectory(prefix="plotkit_code_") as td:
        td = Path(td)
        (td / "runner.py").write_text(RUNNER, encoding="utf-8")
        (td / "code.py").write_text(code, encoding="utf-8")
        with open(td / "in.pkl", "wb") as fh:
            pickle.dump(inputs, fh)
        cmd = [sys.executable, "-I", str(td / "runner.py"), str(td / "in.pkl"), str(td / "code.py"),
               str(td / "out.pkl"), ",".join(outputs)]
        if shutil.which("bwrap") and not os.environ.get("PLOTKIT_NO_SANDBOX"):
            cmd = ["bwrap", "--ro-bind", "/", "/", "--dev", "/dev", "--proc", "/proc", "--tmpfs", "/tmp",
                   "--bind", str(td), str(td), "--unshare-net", "--die-with-parent", "--chdir", str(td), *cmd]
        try:
            p = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout,
                               env={"PATH": "/usr/bin:/bin", "HOME": str(td), "LANG": "C.UTF-8"})
        except subprocess.TimeoutExpired:
            raise PlotkitError(f"data_code took longer than {timeout} s", "simplify the code")
        if p.returncode != 0:
            err = (p.stderr or "").strip().splitlines()
            raise PlotkitError(f"data_code failed: {err[-1] if err else p.returncode}", hint)
        with open(td / "out.pkl", "rb") as fh:
            return pickle.load(fh)
