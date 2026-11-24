"""Where the plotkit-ts checkout is (branch lib/plotkit-ts), for the dev tools that write into it.

    git worktree add .worktrees/plotkit-ts lib/plotkit-ts        (the default place), or set PLOTKIT_TS
"""
import os
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEFAULT = ROOT / ".worktrees" / "plotkit-ts"
# the data folders the goldens name files from -> where plotkit-ts's tests read them (test/golden.ts: BASES)
DATA = {ROOT / "tests" / "inputs": "inputs", ROOT / "experiments" / "eval" / "inputs_b": "inputs_b",
        ROOT / "experiments" / "eval" / "cnt" / "data": "cnt/data", ROOT / "experiments" / "gallery" / "data": "gallery/data"}


def ts_root():
    """PLOTKIT_TS, else .worktrees/plotkit-ts; exits with how to make one when there is none."""
    p = Path(os.environ.get("PLOTKIT_TS") or DEFAULT).resolve()
    if not (p / "package.json").is_file() or not (p / "src").is_dir():
        sys.exit(f"no plotkit-ts checkout at {p}: run  git worktree add .worktrees/plotkit-ts lib/plotkit-ts  "
                 "or set PLOTKIT_TS")
    return p


def sync_data(ts):
    """Copy the data folders to <ts>/test/data, replacing what is there (the goldens are written from these)."""
    for src, dst in DATA.items():
        d = ts / "test" / "data" / dst
        shutil.rmtree(d, ignore_errors=True)
        shutil.copytree(src, d, ignore=shutil.ignore_patterns("__pycache__", "*.pyc", ".~lock*"))
