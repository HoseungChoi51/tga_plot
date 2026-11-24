from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

DATA_FILE = Path("/home/chs/Work/tga_plot/eval/inputs_b/cnt_batches.xlsx")
OUT_DIR = Path("/home/chs/Work/tga_plot/eval/results/runs/luna/R-mpl-brief/B21_r1/out")
SHEET_NAME = "Raw"

OUT_DIR.mkdir(parents=True, exist_ok=True)

plt.rcParams["font.family"] = "Noto Sans CJK KR"
plt.rcParams["axes.unicode_minus"] = False

df = pd.read_excel(DATA_FILE, sheet_name=SHEET_NAME)
df.columns = [str(column).strip() for column in df.columns]

def find_column(keywords):
    for column in df.columns:
        if any(keyword in column.lower() for keyword in keywords):
            return column
    raise ValueError(f"필요한 열을 찾을 수 없습니다: {keywords}")

temperature_col = find_column(["temperature", "temp"])
weight_col = find_column(["weight"])
dtg_col = find_column(["deriv", "dtg"])

temperature = pd.to_numeric(df[temperature_col], errors="coerce")
weight = pd.to_numeric(df[weight_col], errors="coerce")
dtg = pd.to_numeric(df[dtg_col], errors="coerce")

valid = temperature.notna() & weight.notna() & dtg.notna()
temperature = temperature[valid].to_numpy()
weight = weight[valid].to_numpy()
dtg = dtg[valid].to_numpy()

fig, ax1 = plt.subplots(figsize=(9, 6))
ax2 = ax1.twinx()

weight_line, = ax1.plot(
    temperature, weight, color="#1f4e9c", linewidth=2, label="Weight (%)"
)
dtg_up = -dtg
dtg_line, = ax2.plot(
    temperature, dtg_up, color="#c0392b", linewidth=1.8, label="DTG"
)

# 잔류량: 800 °C에 가장 가까운 측정점
residue_idx = int(np.argmin(np.abs(temperature - 800)))
residue_temp = temperature[residue_idx]
residue_weight = weight[residue_idx]
ax1.plot(residue_temp, residue_weight, "o", color="#1f4e9c", markersize=6)
ax1.annotate(
    f"Residue {residue_weight:.1f}%",
    xy=(residue_temp, residue_weight),
    xytext=(8, 10),
    textcoords="offset points",
    color="#1f4e9c",
    fontsize=10,
)

# 피크: 150 °C 초과 구간에서 가장 높은 -DTG
above_150 = temperature > 150
if np.any(above_150):
    peak_candidates = np.flatnonzero(above_150)
    peak_idx = int(peak_candidates[np.argmax(dtg_up[above_150])])
    peak_temp = temperature[peak_idx]
    peak_value = dtg_up[peak_idx]
    ax2.plot(peak_temp, peak_value, "o", color="#c0392b", markersize=6)
    ax2.annotate(
        f"{peak_temp:.0f} °C",
        xy=(peak_temp, peak_value),
        xytext=(8, 10),
        textcoords="offset points",
        color="#c0392b",
        fontsize=10,
    )

ax1.set_title(SHEET_NAME)
ax1.set_xlabel("Temperature (°C)")
ax1.set_ylabel("Weight (%)", color="#1f4e9c")
ax2.set_ylabel("-DTG", color="#c0392b")
ax1.tick_params(axis="y", labelcolor="#1f4e9c")
ax2.tick_params(axis="y", labelcolor="#c0392b")

# 높은 온도가 왼쪽에 오도록 x축 방향을 뒤집습니다.
ax1.set_xlim(np.nanmax(temperature), np.nanmin(temperature))

ax1.legend([weight_line, dtg_line], ["Weight (%)", "DTG"], loc="center left")
fig.tight_layout()
fig.savefig(OUT_DIR / "Raw.png", dpi=300, bbox_inches="tight")
plt.close(fig)
