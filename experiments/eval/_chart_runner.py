"""Runs a model-written matplotlib script and records the chart facts of every saved figure.

    python -I experiments/eval/_chart_runner.py <script.py> <facts.json>
(started inside the bubblewrap sandbox by eval/cnt_runs.py)
"""
import runpy
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import chart_facts  # noqa: E402

script, out = sys.argv[1], sys.argv[2]
chart_facts.install_hook(out)
sys.argv = [script]
runpy.run_path(script, run_name="__main__")
