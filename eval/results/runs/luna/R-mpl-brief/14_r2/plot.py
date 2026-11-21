from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

DATA_FILE = Path("/home/chs/Work/tga_plot/tests/inputs/korean_excel.csv")
OUT_DIR = Path("/home/chs/Work/tga_plot/eval/results/runs/luna/R-mpl-brief/14_r2/out")
OUT_DIR.mkdir(parents=True, exist_ok=True)

plt.rcParams["font.family"] = "Noto Sans CJK KR"
plt.rcParams["axes.unicode_minus"] = False

# Read the CSV, trying common encodings used for Korean Excel exports.
df = None
for encoding in ("utf-8-sig", "cp949", "euc-kr"):
    try:
        df = pd.read_csv(DATA_FILE, encoding=encoding)
        break
    except UnicodeDecodeError:
        continue
if df is None:
    raise UnicodeError(f"Could not decode CSV file: {DATA_FILE}")

# Select columns from the supplied TGA preview.
temperature = pd.to_numeric(df["온도(°C)"], errors="coerce")
weight = pd.to_numeric(df["무게(%)"], errors="coerce")
dtg = pd.to_numeric(df["미분무게(%/°C)"], errors="coerce")
valid = temperature.notna() & weight.notna() & dtg.notna()
temperature = temperature[valid].to_numpy()
weight = weight[valid].to_numpy()
dtg = dtg[valid].to_numpy()

fig, ax1 = plt.subplots(figsize=(9, 6))
ax1.plot(temperature, weight, color="#1f4e9c", linewidth=1.8, label="무게(%)")
ax1.set_xlabel("온도 (°C)")
ax1.set_ylabel("무게 (%)", color="#1f4e9c")
ax1.tick_params(axis="y", labelcolor="#1f4e9c")
ax1.set_title("korean_excel")
ax1.grid(True, alpha=0.25)

ax2 = ax1.twinx()
dtg_up = -dtg
ax2.plot(temperature, dtg_up, color="#c0392b", linewidth=1.5, label="DTG")
ax2.set_ylabel("-미분무게 (%/°C)", color="#c0392b")
ax2.tick_params(axis="y", labelcolor="#c0392b")

# Residue at the measured point nearest 800 °C.
residue_idx = int(np.argmin(np.abs(temperature - 800)))
ax1.scatter(
    temperature[residue_idx], weight[residue_idx],
    color="#1f4e9c", edgecolor="white", linewidth=0.7, zorder=5
)
ax1.annotate(
    f"Residue {weight[residue_idx]:.1f}%",
    (temperature[residue_idx], weight[residue_idx]),
    xytext=(8, 10), textcoords="offset points",
    color="#1f4e9c", fontsize=9
)

# Highest upward DTG peak above 150 °C.
above_150 = np.flatnonzero(temperature > 150)
if above_150.size:
    peak_idx = int(above_150[np.argmax(dtg_up[above_150])])
    ax2.scatter(
        temperature[peak_idx], dtg_up[peak_idx],
        color="#c0392b", edgecolor="white", linewidth=0.7, zorder=5
    )
    ax2.annotate(
        f"{temperature[peak_idx]:.0f} °C",
        (temperature[peak_idx], dtg_up[peak_idx]),
        xytext=(8, 10), textcoords="offset points",
        color="#c0392b", fontsize=9
    )

lines = ax1.get_lines() + ax2.get_lines()
ax1.legend(lines, [line.get_label() for line in lines], loc="center left")
fig.tight_layout()

stem = OUT_DIR / "korean_excel"
fig.savefig(stem.with_suffix(".png"), dpi=300, bbox_inches="tight")
fig.savefig(stem.with_suffix(".pdf"), bbox_inches="tight")
plt.close(fig)
