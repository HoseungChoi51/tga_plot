"""Check that plotkit reads every test file correctly with the default TGA spec.

    python tests/run_tests.py            (run make_test_inputs.py once first)
Plots go to tests/out/. Exit code 0 = all passed.
"""
import json
import sys
from pathlib import Path

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE.parent))
import plotkit  # noqa: E402

expected = json.loads((HERE / "expected.json").read_text(encoding="utf-8"))
fails = 0
for fname, sheets in expected.items():
    try:
        res = plotkit.plot({"file": str(HERE / "inputs" / fname),
                            "output": {"dir": str(HERE / "out" / Path(fname).stem)}})
    except plotkit.PlotkitError as e:
        print(f"FAIL {fname}: {e.message} | {e.hint}")
        fails += len(sheets)
        continue
    got = {p["sheet"]: p for p in res["plots"]}
    for sheet, exp in sheets.items():
        p = got.get(sheet)
        if p is None:
            print(f"FAIL {fname} / {sheet}: not plotted. warnings: {res['warnings']}")
            fails += 1
            continue
        used = p["columns_used"][sheet]
        letters = " ".join(used[r].split()[0] for r in ("x", "y1", "y2"))
        ann = {a["name"]: a for a in p["annotations"]}
        res_v = ann["residue"].get("value")
        peak = ann["peak"]["peaks"][0]["x"] if ann["peak"].get("peaks") else None
        problems = []
        if letters != exp["cols"]:
            problems.append(f"columns {letters} (expected {exp['cols']})")
        if exp["residue"] is None:
            if res_v is not None:
                problems.append(f"residue {res_v} but the run stops before 800 °C")
        elif res_v is None or abs(res_v - exp["residue"]) > 0.05:
            problems.append(f"residue {res_v} (expected {exp['residue']:.2f})")
        if peak is None or abs(peak - exp["peak"]) > 5:
            problems.append(f"peak {peak} (expected {exp['peak']:.0f})")
        status = "FAIL" if problems else "ok  "
        fails += bool(problems)
        print(f"{status} {fname:30s} {sheet:18s} cols={letters} ({p['column_guess']}), "
              f"residue={res_v}, peak={peak}" + (" <- " + "; ".join(problems) if problems else ""))
print("\nALL PASSED" if not fails else f"\n{fails} FAILED")
sys.exit(1 if fails else 0)
