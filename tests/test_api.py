"""validate, echarts_options, render, the command line and the serve sidecar (offline)."""
import io
import json
import subprocess
import sys
from pathlib import Path

import pytest

import plotkit
from plotkit import __main__ as cli

ROOT = Path(__file__).resolve().parent.parent
INPUTS = ROOT / "tests" / "inputs"
CURVE = {"file": "TGA.xlsx", "sheets": 1, "x": {"step": 200}}
CHART = {"file": "run_log.csv", "chart": "bar", "x": "반응기", "y": {"col": "수율", "agg": "mean"}, "values": "{:.2f}"}


def test_validate_both_kinds():
    c = plotkit.validate(CURVE, INPUTS)
    t = plotkit.validate(CHART, INPUTS)
    assert c["kind"] == "curve" and c["spec"]["x"]["step"] == 200 and c["spec"]["preset"] == "tga"
    assert t["kind"] == "chart" and t["spec"]["chart"] == "bar"
    json.dumps([c, t])                                      # JSON-safe: the sidecar sends it as it is
    assert not any(k.startswith("_") for k in c["spec"])


def test_validate_reads_the_data():
    with pytest.raises(plotkit.PlotkitError) as e:
        plotkit.validate({**CURVE, "sheets": "no such sheet"}, INPUTS)
    assert "1006R1-V" in e.value.hint or "1006R1-V" in e.value.message


def test_options_without_files(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    for spec, kind in ((CURVE, "curve"), (CHART, "chart")):
        r = plotkit.echarts_options(spec, INPUTS, full=True)
        assert r["ok"] and r["kind"] == kind and r["saved"] == [] and r["options"]
        assert plotkit.echarts_options(spec, INPUTS) == r["options"]
    assert list(tmp_path.iterdir()) == [] and not list(INPUTS.glob("*_plots"))     # nothing written anywhere
    curve = plotkit.echarts_options(CURVE, INPUTS, full=True)
    sheet = next(iter(curve["values"]))
    assert {"residue", "peak"} <= set(curve["values"][sheet])
    chart = plotkit.echarts_options(CHART, INPUTS)[0]
    assert "__fmt__" in json.dumps(chart, ensure_ascii=False)       # the renderer revives it


def test_options_refuse_matplotlib_code():
    with pytest.raises(plotkit.PlotkitError, match='"code"'):
        plotkit.echarts_options({**CHART, "code": "ax.set_title('x')"}, INPUTS)
    with pytest.raises(plotkit.PlotkitError, match='"code"'):
        plotkit.echarts_options({**CURVE, "code": "ax1.set_title('x')"}, INPUTS)


@pytest.mark.parametrize("engine", ["echarts", "matplotlib"])
def test_render(engine, tmp_path):
    r = plotkit.render(CHART, tmp_path, formats=("png", "svg"), engine=engine, base=INPUTS)
    assert r["kind"] == "chart" and r["engine"] == engine
    assert sorted(Path(p).suffix for p in r["saved"]) == [".png", ".svg"]
    r = plotkit.render(CURVE, tmp_path / "c", engine=engine, base=INPUTS)
    assert [Path(p).suffix for p in r["saved"]] == [".png"] and not (tmp_path / "c" / "summary.csv").exists()


def test_base_only_joins_relative_names():
    a = plotkit.api.with_base({"files": ["a.csv", "/abs/b.csv"], "x": "a.csv"}, "/data")
    assert a == {"files": ["/data/a.csv", "/abs/b.csv"], "x": "a.csv"}


def test_revive_handles_the_markers():
    js = ("import { revive } from './plotkit/js/revive.mjs';"
          "const o = revive({series: [{label: {formatter: '__fmt__{:.2f}'}}]});"
          "console.log(o.series[0].label.formatter({value: 4.256}));")
    out = subprocess.run(["node", "--input-type=module", "-e", js], cwd=ROOT, capture_output=True, text=True, check=True)
    assert out.stdout.strip() == "4.26"


# =================================================================== command line and sidecar
def run_cli(*args):
    p = subprocess.run([sys.executable, "-m", "plotkit", *args], cwd=ROOT, capture_output=True, text=True)
    return p.returncode, p.stdout


def test_cli(tmp_path):
    rc, out = run_cli("prompt")
    assert rc == 0 and out == plotkit.system_prompt()
    rc, out = run_cli("preview", "run_log.csv", "--base", str(INPUTS))
    assert rc == 0 and out.startswith("데이터 미리보기:\n파일 run_log.csv")
    spec = json.dumps(CHART, ensure_ascii=False)
    rc, out = run_cli("validate", "--base", str(INPUTS), "--json", spec)
    assert rc == 0 and json.loads(out)["kind"] == "chart"
    rc, out = run_cli("options", "--base", str(INPUTS), "--json", spec)
    assert rc == 0 and json.loads(out)["options"]
    rc, out = run_cli("render", "--base", str(INPUTS), "--out", str(tmp_path), "--format", "svg", "--json", spec)
    assert rc == 0 and json.loads(out)["saved"][0].endswith(".svg")
    rc, out = run_cli("validate", "--base", str(INPUTS), "--json", json.dumps({**CHART, "colour_by": 1}))
    assert rc == 2 and json.loads(out)["hint"]
    rc, out = run_cli("inspect", str(INPUTS / "TGA.xlsx"))          # the older command line still works
    assert rc == 0 and json.loads(out)["ok"]


def test_serve_round_trip():
    lines = [{"id": 1, "method": "options", "params": {"spec": CHART, "base": str(INPUTS)}},
             {"id": 2, "method": "validate", "params": {"spec": {**CHART, "colour_by": 1}, "base": str(INPUTS)}},
             {"id": 3, "method": "nope"},
             "not json",
             {"id": 4, "method": "retry_message", "params": {"error": "e", "hint": "h"}},
             {"id": 5, "method": "request_options", "params": {"reasoning": True}}]
    out = io.StringIO()
    cli.serve(io.StringIO("\n".join(json.dumps(x) if isinstance(x, dict) else x for x in lines) + "\n"), out)
    got = [json.loads(x) for x in out.getvalue().splitlines()]
    assert [g["id"] for g in got] == [1, 2, 3, None, 4, 5]
    assert got[0]["ok"] and got[0]["result"]["options"]
    assert not got[1]["ok"] and got[1]["error"].startswith('unknown key "colour_by"') and got[1]["hint"]
    assert not got[2]["ok"] and "methods:" in got[2]["hint"]
    assert not got[3]["ok"]
    assert got[4]["result"] == "plotkit error: e\nhint: h\n\n고쳐서 다시 보내 주세요."
    assert got[5]["result"] == {"chat_template_kwargs": {"enable_thinking": True}}


def test_serve_from_node():
    """As Electron would call it: spawn the sidecar, write a request line, read the answer line."""
    js = r"""
import { spawn } from "node:child_process";
import readline from "node:readline";
const py = spawn(process.argv[1], ["-m", "plotkit", "serve"]);
const rl = readline.createInterface({ input: py.stdout });
rl.on("line", line => { const m = JSON.parse(line); console.log(JSON.stringify({ id: m.id, ok: m.ok, n: m.result.options.length })); py.stdin.end(); });
py.stdin.write(JSON.stringify({ id: 7, method: "options", params: { spec: JSON.parse(process.argv[2]), base: process.argv[3] } }) + "\n");
"""
    p = subprocess.run(["node", "--input-type=module", "-e", js, sys.executable, json.dumps(CHART, ensure_ascii=False),
                        str(INPUTS)], cwd=ROOT, capture_output=True, text=True, timeout=120)
    assert json.loads(p.stdout.strip().splitlines()[-1]) == {"id": 7, "ok": True, "n": 1}, p.stderr
