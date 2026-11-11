"""Create TGA test files in many formats (tests/inputs/) plus expected.json.

Each file holds a synthetic CNT run in air with known DTG peak temperature and
residue, so run_tests.py can check that plotkit read the right columns.
"""
import json
from pathlib import Path

import numpy as np
import openpyxl

OUT = Path(__file__).parent / "inputs"
OUT.mkdir(exist_ok=True)
rng = np.random.default_rng(1)


def run(steps, residue, tmax=900.0, dT=1.0):
    T = np.arange(30.0, tmax + dT / 2, dT)
    time = (T - 30.0) / 10.0
    rate = np.zeros_like(T)
    for amount, center, width in steps:
        rate += amount * np.exp(-0.5 * ((T - center) / width) ** 2) / (width * np.sqrt(2 * np.pi))
    loss = np.cumsum(rate) * dT
    total = sum(a for a, _, _ in steps)
    W = 100 - loss * (100 - residue) / total
    D = np.gradient(W, T)                       # negative during mass loss
    W = W + rng.normal(0, 0.01, T.size)
    D = D + rng.normal(0, 0.001, T.size)
    main = max(steps, key=lambda s: s[0] / s[2])
    exp_res = float(W[np.argmin(abs(T - 800))]) if tmax >= 800 else None
    return dict(time=time, T=T, W=W, D=D, mg=W / 100 * 10.23, hf=-D * 3 + 0.1,
                peak=float(main[1]), residue=exp_res)


R1 = run([(2, 90, 20), (88, 600, 35)], residue=8)
R2 = run([(4, 95, 20), (12, 400, 30), (80, 560, 40)], residue=3)
R3 = run([(2, 90, 20), (60, 540, 30)], residue=30, tmax=750)     # stops before 800
expected = {}


def fmt(v):
    return float(f"{v:.5g}")


def save_xlsx(name, sheets):
    wb = openpyxl.Workbook()
    wb.remove(wb.active)
    for sname, rows in sheets.items():
        ws = wb.create_sheet(sname)
        for r in rows:
            ws.append(r)
    wb.save(OUT / name)


def std_rows(r, header=("Time", "Temperature", "Weight(%)", "D.W(%/C)")):
    rows = [list(header)] if header else []
    rows += [[fmt(a), fmt(b), fmt(c), fmt(d)] for a, b, c, d in zip(r["time"], r["T"], r["W"], r["D"])]
    return rows


# 1. the normal layout, 3 sheets (one stops at 750 °C)
save_xlsx("TGA.xlsx", {"1006R1-V normal": std_rows(R1), "1006R1-V acid": std_rows(R2),
                       "1006R1-V 750C": std_rows(R3)})
expected["TGA.xlsx"] = {"1006R1-V normal": dict(cols="B C D", **{k: R1[k] for k in ("peak", "residue")}),
                        "1006R1-V acid": dict(cols="B C D", **{k: R2[k] for k in ("peak", "residue")}),
                        "1006R1-V 750C": dict(cols="B C D", **{k: R3[k] for k in ("peak", "residue")})}

# 2. extra and reordered columns
rows = [["Index", "Temperature (°C)", "Time (min)", "Weight (mg)", "Weight (%)", "Heat Flow (W/g)",
         "Deriv. Weight (%/°C)"]]
rows += [[i + 1, fmt(b), fmt(a), fmt(m), fmt(c), fmt(h), fmt(d)] for i, (a, b, c, d, m, h) in
         enumerate(zip(R1["time"], R1["T"], R1["W"], R1["D"], R1["mg"], R1["hf"]))]
save_xlsx("extra_columns.xlsx", {"CNT-01": rows})
expected["extra_columns.xlsx"] = {"CNT-01": dict(cols="B E G", peak=R1["peak"], residue=R1["residue"])}

# 3. blank rows and metadata on top, table starts in column B
rows = [[], [], [], [None, "Sample: CNT-01"], [None, "Method: Ramp 10 °C/min to 900 °C, Air"],
        [None, "Mass (mg)", 10.23], [], [None] + std_rows(R2)[0]]
rows += [[None] + r for r in std_rows(R2)[1:]]
save_xlsx("blank_rows_on_top.xlsx", {"Sheet1": rows})
expected["blank_rows_on_top.xlsx"] = {"Sheet1": dict(cols="C D E", peak=R2["peak"], residue=R2["residue"])}

# 4. Korean headers
save_xlsx("korean_headers.xlsx", {"시료A": std_rows(R1, ("시간(분)", "온도(°C)", "무게(%)", "미분무게(%/°C)"))})
expected["korean_headers.xlsx"] = {"시료A": dict(cols="B C D", peak=R1["peak"], residue=R1["residue"])}

# 5. names row + units row
rows = [["Time", "Temperature", "Weight", "Deriv. Weight"], ["min", "°C", "%", "%/°C"]] + std_rows(R1, None)
save_xlsx("units_row.xlsx", {"run1": rows})
expected["units_row.xlsx"] = {"run1": dict(cols="B C D", peak=R1["peak"], residue=R1["residue"])}

# 6. no header at all
save_xlsx("no_header.xlsx", {"data": std_rows(R2, None)})
expected["no_header.xlsx"] = {"data": dict(cols="B C D", peak=R2["peak"], residue=R2["residue"])}

# 7. different wording
save_xlsx("different_wording.xlsx",
          {"S1": std_rows(R1, ("t [min]", "Sample Temp.", "Mass %", "DTG"))})
expected["different_wording.xlsx"] = {"S1": dict(cols="B C D", peak=R1["peak"], residue=R1["residue"])}

# 8. instrument-style text export: UTF-16, tab separated, metadata, no column names
lines = ["Filename\tC:\\TA\\Data\\CNT01.001", "Instrument\tTGA Q500", "Sample\tCNT-01",
         "Size\t10.2300\tmg", "Method\tRamp 10 °C/min to 900 °C", "Sig1\tTime (min)",
         "Sig2\tTemperature (°C)", "Sig3\tWeight (%)", "Sig4\tDeriv. Weight (%/°C)", "StartOfData"]
lines += [f"{a:.4f}\t{b:.3f}\t{c:.4f}\t{d:.6f}" for a, b, c, d in zip(R2["time"], R2["T"], R2["W"], R2["D"])]
(OUT / "instrument_export.txt").write_bytes("\r\n".join(lines).encode("utf-16"))
expected["instrument_export.txt"] = {"instrument_export": dict(cols="B C D", peak=R2["peak"], residue=R2["residue"])}

# 9. CSV saved by Korean Excel (cp949) with Korean headers
lines = ["시간(분),온도(°C),무게(%),미분무게(%/°C)"]
lines += [f"{a:.4f},{b:.3f},{c:.4f},{d:.6f}" for a, b, c, d in zip(R1["time"], R1["T"], R1["W"], R1["D"])]
(OUT / "korean_excel.csv").write_bytes("\r\n".join(lines).encode("cp949"))
expected["korean_excel.csv"] = {"korean_excel": dict(cols="B C D", peak=R1["peak"], residue=R1["residue"])}

# 10. European CSV: semicolons and decimal commas
lines = ["Time;Temperature;Weight;Deriv. Weight", "min;°C;%;%/°C"]
lines += [f"{a:.4f};{b:.3f};{c:.4f};{d:.6f}".replace(".", ",") for a, b, c, d in
          zip(R2["time"], R2["T"], R2["W"], R2["D"])]
(OUT / "semicolon_decimal_comma.csv").write_text("\n".join(lines), encoding="utf-8")
expected["semicolon_decimal_comma.csv"] = {"semicolon_decimal_comma": dict(cols="B C D", peak=R2["peak"], residue=R2["residue"])}

# 11. plain text, columns separated by spaces
lines = ["Time   Temperature   Weight(%)   Deriv.Weight(%/C)"]
lines += [f"{a:8.3f} {b:9.2f} {c:9.4f} {d:11.6f}" for a, b, c, d in zip(R1["time"], R1["T"], R1["W"], R1["D"])]
(OUT / "space_separated.txt").write_text("\n".join(lines), encoding="utf-8")
expected["space_separated.txt"] = {"space_separated": dict(cols="B C D", peak=R1["peak"], residue=R1["residue"])}

# 12. old Excel 97-2003 .xls (needs xlwt to create, xlrd to read)
try:
    import xlwt
    wb = xlwt.Workbook()
    ws = wb.add_sheet("old run")
    for i, r in enumerate(std_rows(R1)):
        for j, v in enumerate(r):
            ws.write(i, j, v)
    wb.save(str(OUT / "old_format.xls"))
    expected["old_format.xls"] = {"old run": dict(cols="B C D", peak=R1["peak"], residue=R1["residue"])}
except ImportError:
    print("xlwt not installed: skipped old_format.xls")

(Path(__file__).parent / "expected.json").write_text(json.dumps(expected, ensure_ascii=False, indent=1))
print(f"wrote {len(expected)} test files to {OUT}")
