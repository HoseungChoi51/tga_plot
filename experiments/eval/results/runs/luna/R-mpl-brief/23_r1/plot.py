from pathlib import Path
import csv
import re

import numpy as np
import matplotlib.pyplot as plt

DATA_FILE = Path("/home/chs/Work/tga_plot/tests/inputs/instrument_export.txt")
OUT_DIR = Path("/home/chs/Work/tga_plot/eval/results/runs/luna/R-mpl-brief/23_r1/out")
OUT_DIR.mkdir(parents=True, exist_ok=True)

plt.rcParams["font.family"] = "Noto Sans CJK KR"
plt.rcParams["axes.unicode_minus"] = False


def parse_number(value):
    """Parse plain numbers, including decimal comma and optional surrounding quotes."""
    if value is None:
        return np.nan
    text = str(value).strip().strip('"').strip("'").replace("\ufeff", "")
    if not text:
        return np.nan
    text = text.replace(",", ".")
    try:
        return float(text)
    except ValueError:
        return np.nan


def read_numeric_rows(path):
    # Decode flexibly because instrument exports often have a UTF-16/locale encoding.
    raw = path.read_bytes()
    text = None
    for encoding in ("utf-8-sig", "utf-16", "cp1252", "latin1"):
        try:
            text = raw.decode(encoding)
            break
        except UnicodeDecodeError:
            continue
    if text is None:
        text = raw.decode("latin1", errors="replace")

    rows = []
    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue
        # Instrument files may use tabs, semicolons, commas, or whitespace.
        if "\t" in line:
            fields = next(csv.reader([line], delimiter="\t"))
        elif ";" in line:
            fields = next(csv.reader([line], delimiter=";"))
        elif "," in line:
            fields = next(csv.reader([line], delimiter=","))
        else:
            fields = re.split(r"\s+", line)

        values = [parse_number(field) for field in fields]
        # The numeric data rows contain the four expected numeric columns.
        if len(values) >= 4 and np.isfinite(values[1:4]).sum() >= 3:
            rows.append(values[:4])

    if not rows:
        raise ValueError(f"No numeric TGA data rows could be parsed from {path}")
    return np.asarray(rows, dtype=float)


data = read_numeric_rows(DATA_FILE)
temperature = data[:, 1]
weight = data[:, 2]
dtg = data[:, 3]

valid = np.isfinite(temperature) & np.isfinite(weight) & np.isfinite(dtg)
temperature, weight, dtg = temperature[valid], weight[valid], dtg[valid]
if temperature.size == 0:
    raise ValueError("No valid temperature, weight, and DTG values were found.")

fig, ax1 = plt.subplots(figsize=(8, 5))
ax2 = ax1.twinx()

weight_line, = ax1.plot(
    temperature, weight, color="#1f4e9c", linewidth=1.8, label="Weight"
)
dtg_line, = ax2.plot(
    temperature, -dtg, color="#c0392b", linewidth=1.5, label="DTG"
)

ax1.set_title(DATA_FILE.stem)
ax1.set_xlabel("Temperature (°C)")
ax1.set_ylabel("Weight (%)", color="#1f4e9c")
ax2.set_ylabel("DTG (%/°C)", color="#c0392b")
ax1.tick_params(axis="y", labelcolor="#1f4e9c")
ax2.tick_params(axis="y", labelcolor="#c0392b")
ax1.grid(True, alpha=0.25)
ax1.legend([weight_line, dtg_line], ["Weight", "DTG"], loc="center left")

# Residue at the measured point nearest 800 °C.
residue_idx = int(np.nanargmin(np.abs(temperature - 800)))
residue_temp = temperature[residue_idx]
residue_weight = weight[residue_idx]
ax1.plot(residue_temp, residue_weight, marker="o", color="#1f4e9c", markersize=5)
ax1.annotate(
    f"Residue: {residue_weight:.1f}%",
    xy=(residue_temp, residue_weight),
    xytext=(8, 10),
    textcoords="offset points",
    color="#1f4e9c",
    fontsize=9,
)

# Highest upward DTG peak above 150 °C.
peak_mask = temperature > 150
if np.any(peak_mask):
    candidate_indices = np.flatnonzero(peak_mask)
    peak_idx = candidate_indices[np.argmax((-dtg)[peak_mask])]
    peak_temp = temperature[peak_idx]
    peak_value = -dtg[peak_idx]
    ax2.plot(peak_temp, peak_value, marker="o", color="#c0392b", markersize=5)
    ax2.annotate(
        f"{peak_temp:.0f} °C",
        xy=(peak_temp, peak_value),
        xytext=(8, 10),
        textcoords="offset points",
        color="#c0392b",
        fontsize=9,
    )

fig.tight_layout()
fig.savefig(OUT_DIR / f"{DATA_FILE.stem}.png", dpi=300, bbox_inches="tight")
plt.close(fig)
