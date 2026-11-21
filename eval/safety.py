"""Escape hatches, safety: what a spec's "code" and "echarts" keys let a model (or a pasted spec) do.

    python eval/safety.py      -> eval/results/safety.json
Harmless probes only: read a file outside the data folder, list the home folder, start a process;
and the ECharts patch with a function, a URL and an unknown path.
"""
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(ROOT))
import plotkit  # noqa: E402

T = str(ROOT / "tests" / "inputs" / "TGA.xlsx")
OUT = str(HERE / "results" / "safety")
PROBES = {
    "code_reads_file_outside": {"engine": "matplotlib", "spec": {"file": T, "sheets": 1, "output": {"dir": OUT},
        "code": "ax1.set_title(open('/etc/hostname').read().strip()[:3] + '…')"}},
    "code_lists_home": {"engine": "matplotlib", "spec": {"file": T, "sheets": 1, "output": {"dir": OUT},
        "code": "import os; ax1.set_xlabel(str(len(os.listdir(os.path.expanduser('~')))) + ' entries in ~')"}},
    "code_starts_process": {"engine": "matplotlib", "spec": {"file": T, "sheets": 1, "output": {"dir": OUT},
        "code": "import subprocess; ax1.set_ylabel(subprocess.run(['echo', 'ran'], capture_output=True, text=True).stdout.strip())"}},
    "echarts_function": {"engine": "echarts", "spec": {"file": T, "sheets": 1, "output": {"dir": OUT},
        "echarts": {"xAxis": {"axisLabel": {"formatter": "function (v) { return v + 273 }"}}}}},
    "echarts_url": {"engine": "echarts", "spec": {"file": T, "sheets": 1, "output": {"dir": OUT},
        "echarts": {"graphic": [{"type": "text", "style": {"text": "https://example.com/x.png"}}]}}},
    "echarts_unknown_path": {"engine": "echarts", "spec": {"file": T, "sheets": 1, "output": {"dir": OUT},
        "echarts": {"series": [{"data": [[1, 2]]}]}}},
}
res = {}
for name, p in PROBES.items():
    try:
        plotkit.plot(p["spec"], engine=p["engine"])
        res[name] = {"engine": p["engine"], "result": "ran"}
    except plotkit.PlotkitError as e:
        res[name] = {"engine": p["engine"], "result": "refused", "error": e.message, "hint": e.hint[:200]}
(HERE / "results" / "safety.json").write_text(json.dumps(res, ensure_ascii=False, indent=1), encoding="utf-8")
print(json.dumps(res, ensure_ascii=False, indent=1))
