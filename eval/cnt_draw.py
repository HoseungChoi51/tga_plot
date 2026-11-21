"""Draw one spec (curve or chart) in a fresh process and record what was drawn.

    python -I eval/cnt_draw.py <spec.json> <engine> <result.json>

Writes {"result": plotkit's reply or {"ok": false, "error", "hint"}, "facts": [chart facts per figure],
"draw_s": seconds}. Run with the run folder as the working directory.
"""
import json
import os
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
sys.path.insert(0, str(HERE))

spec_path, engine, out_path = sys.argv[1], sys.argv[2], sys.argv[3]
spec = json.loads(Path(spec_path).read_text(encoding="utf-8"))
dump = str(Path(out_path).with_suffix(".echarts.json"))
os.environ["PLOTKIT_DUMP_OPTION"] = dump
t0 = time.time()
import chart_facts  # noqa: E402
import plotkit  # noqa: E402
from plotkit import PlotkitError  # noqa: E402
chart_facts.install_hook()
try:
    if any(k in spec for k in ("chart", "kind", "chart_type")):
        import chartkit
        result = chartkit.plot(spec, engine=engine, dump_path=dump)
    else:
        result = plotkit.plot(spec, engine=engine)
except PlotkitError as e:
    result = {"ok": False, "error": e.message, "hint": e.hint}
except Exception as e:  # noqa: BLE001 - a crash is a failed run, not a crashed harness
    result = {"ok": False, "error": f"{type(e).__name__}: {e}", "hint": "", "crash": True}
draw_s = time.time() - t0
facts = []
if result.get("ok"):
    if engine == "echarts":
        if Path(dump).exists():
            facts = chart_facts.echarts_dump_chart_facts(dump)
    else:
        facts = chart_facts.take()
Path(out_path).write_text(json.dumps({"result": result, "facts": facts, "draw_s": draw_s}, ensure_ascii=False, default=str),
                          encoding="utf-8")
