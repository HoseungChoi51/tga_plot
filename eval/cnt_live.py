"""E4b driver: live ECharts options for every dev reference spec (curves and charts), plus the static options of
the curve plots as a control (their labels are placed in pixels, so they should NOT stay on their data), checked
in a browser by eval/live_check.mjs. Writes eval/results/cnt_live.json.

    python eval/cnt_live.py
"""
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
sys.path.insert(0, str(HERE))
import chartkit  # noqa: E402
import plotkit  # noqa: E402
import plotkit_echarts  # noqa: E402
from cnt_dev_refs import REFS  # noqa: E402

cases = []
work = Path(tempfile.mkdtemp(prefix="cnt_live_"))
(work / "data").symlink_to(HERE / "cnt" / "data", target_is_directory=True)
os.chdir(work)
for k, spec in REFS.items():
    curve = not any(x in spec for x in ("chart", "kind"))
    opts = plotkit_echarts.live_options(spec) if curve else chartkit.live_options(spec)
    cases.append({"id": k, "kind": "live", "option": opts[0]})
    if curve:                                  # the static render's own option, labels in pixels
        dump = work / f"{k}.json"
        os.environ["PLOTKIT_DUMP_OPTION"] = str(dump)
        plotkit.plot({**spec, "output": {"dir": str(work / "out"), "name": k}}, engine="echarts")
        os.environ.pop("PLOTKIT_DUMP_OPTION")
        cases.append({"id": k, "kind": "static", "option": json.loads(dump.read_text())["figures"][0]["option"]})
(work / "cases.json").write_text(json.dumps(cases, ensure_ascii=False, default=str))
out = HERE / "results" / "cnt_live.json"
subprocess.run(["node", str(HERE / "live_check.mjs"), str(work / "cases.json"), str(out)], check=True)
res = json.loads(out.read_text())
for kind in ("live", "static"):
    rr = [r for r in res if r["kind"] == kind]
    print(kind, "charts", len(rr), "labels in view", sum(r["in_view"] for r in rr), "attached", sum(r["attached"] for r in rr),
          "charts with a detached label", sum(1 for r in rr if r["attached"] < r["in_view"]))
