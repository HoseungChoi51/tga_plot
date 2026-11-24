from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

DATA_FILE = Path("/home/chs/Work/tga_plot/tests/inputs/instrument_export.txt")
OUT_DIR = Path("/home/chs/Work/tga_plot/eval/results/runs/luna_think/R-mpl-brief/23_r1/out")
OUT_DIR.mkdir(parents=True, exist_ok=True)


def read_text_data(path):
    # Instrument exports are often UTF-16 (BOM starts with FF FE or FE FF);
    # try common encodings so the file can be read without assuming UTF-8.
    raw = path.read_bytes()
    for encoding in ("utf-16", "utf-8-sig", "cp1252", "latin1"):
        try:
            text = raw.decode(encoding)
            break
        except UnicodeDecodeError:
            continue
    else:
        raise UnicodeError(f"Could not decode {path}")

    # Skip the first 10 metadata lines indicated by the preview, then extract
    # numeric fields from each row. This also tolerates tab/comma/space exports.
    rows = []
    for line in text.splitlines()[10:]:
        line = line.strip()
        if not line or line.startswith(("#", ";")):
            continue
        fields = line.replace(",", " ").replace("\t", " ").split()
        values = []
        for field in fields:
            try:
                values.append(float(field))
            except ValueError:
                continue
        if len(values) >= 4:
            rows.append(values[:4])

    if not rows:
        raise ValueError(f"No numeric data rows found in {path}")
    return np.asarray(rows, dtype=float)


data = read_text_data(DATA_FILE)
temperature, weight, dtg = data[:, 1], data[:, 2], data[:, 3]
valid = np.isfinite(temperature) & np.isfinite(weight) & np.isfinite(dtg)
temperature, weight, dtg = temperature[valid], weight[valid], dtg[valid]

if temperature.size == 0:
    raise ValueError(f"No valid TGA data found in {DATA_FILE}")

plt.rcParams["font.family"] = "Noto Sans CJK KR"
plt.rcParams["axes.unicode_minus"] = False

fig, ax1 = plt.subplots(figsize=(9, 6))
line1, = ax1.plot(temperature, weight, color="#1f4e9c", label="Weight")
ax1.set_xlabel("Temperature (°C)")
ax1.set_ylabel("Weight (%)", color="#1f4e9c")
ax1.tick_params(axis="y", labelcolor="#1f4e9c")
ax1.grid(True, alpha=0.3)

ax2 = ax1.twinx()
line2, = ax2.plot(temperature, -dtg, color="#c0392b", label="DTG")
ax2.set_ylabel("DTG (%/°C)", color="#c0392b")
ax2.tick_params(axis="y", labelcolor="#c0392b")

residue_idx = int(np.argmin(np.abs(temperature - 800)))
ax1.scatter(temperature[residue_idx], weight[residue_idx], color="#1f4e9c", zorder=5)
ax1.annotate(
    f"Residue: {weight[residue_idx]:.1f}%",
    (temperature[residue_idx], weight[residue_idx]),
    xytext=(8, 8),
    textcoords="offset points",
    color="#1f4e9c",
)

eligible = np.flatnonzero(temperature > 150)
if eligible.size:
    upward_dtg = -dtg
    peak_idx = int(eligible[np.argmax(upward_dtg[eligible])])
    ax2.scatter(
        temperature[peak_idx], upward_dtg[peak_idx],
        color="#c0392b", zorder=5
    )
    ax2.annotate(
        f"{temperature[peak_idx]:.0f} °C",
        (temperature[peak_idx], upward_dtg[peak_idx]),
        xytext=(8, 8),
        textcoords="offset points",
        color="#c0392b",
    )

ax1.set_title("instrument_export")
ax1.legend([line1, line2], ["Weight", "DTG"], loc="center left")
fig.tight_layout()
fig.savefig(OUT_DIR / "instrument_export.png", dpi=300, bbox_inches="tight")
plt.close(fig)
