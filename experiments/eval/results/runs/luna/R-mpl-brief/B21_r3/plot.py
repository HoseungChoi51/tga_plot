from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

DATA_FILE = Path("/home/chs/Work/tga_plot/eval/inputs_b/cnt_batches.xlsx")
OUT_DIR = Path("/home/chs/Work/tga_plot/eval/results/runs/luna/R-mpl-brief/B21_r3/out")
SHEET_NAME = "Raw"

OUT_DIR.mkdir(parents=True, exist_ok=True)
plt.rcParams["font.family"] = "Noto Sans CJK KR"
plt.rcParams["axes.unicode_minus"] = False

df = pd.read_excel(DATA_FILE, sheet_name=SHEET_NAME)

def find_column(columns, terms):
    for col in columns:
        name = str(col).lower()
        if all(term in name for term in terms):
            return col
    raise ValueError(f"필요한 열을 찾을 수 없습니다: {terms}")

temperature_col = find_column(df.columns, ["temperature"])
weight_col = find_column(df.columns, ["weight"])
dtg_col = find_column(df.columns, ["deriv"])

temperature = pd.to_numeric(df[temperature_col], errors="coerce").to_numpy()
weight = pd.to_numeric(df[weight_col], errors="coerce").to_numpy()
dtg = pd.to_numeric(df[dtg_col], errors="coerce").to_numpy()

valid = np.isfinite(temperature) & np.isfinite(weight) & np.isfinite(dtg)
temperature, weight, dtg = temperature[valid], weight[valid], dtg[valid]
if temperature.size == 0:
    raise ValueError("유효한 수치 데이터가 없습니다.")

# DTG는 질량 감소 피크가 위로 향하도록 부호를 반전합니다.
dtg_up = -dtg

residue_idx = int(np.argmin(np.abs(temperature - 800)))
peak_candidates = np.flatnonzero(temperature > 150)
if peak_candidates.size == 0:
    raise ValueError("150 °C보다 높은 온도의 DTG 데이터가 없습니다.")
peak_idx = int(peak_candidates[np.argmax(dtg_up[peak_candidates])])

fig, ax1 = plt.subplots(figsize=(9, 6))
line1, = ax1.plot(
    temperature, weight, color="#1f4e9c", linewidth=1.8, label="Weight (%)"
)
ax1.set_xlabel("Temperature (°C)")
ax1.set_ylabel("Weight (%)", color="#1f4e9c")
ax1.tick_params(axis="y", labelcolor="#1f4e9c")
ax1.set_title(SHEET_NAME)

ax2 = ax1.twinx()
line2, = ax2.plot(
    temperature, dtg_up, color="#c0392b", linewidth=1.5, label="DTG (-%/°C)"
)
ax2.set_ylabel("-Derivative Weight (%/°C)", color="#c0392b")
ax2.tick_params(axis="y", labelcolor="#c0392b")

ax1.plot(
    temperature[residue_idx], weight[residue_idx],
    marker="o", color="#1f4e9c", markersize=6, linestyle="none"
)
ax1.annotate(
    f"Residue {weight[residue_idx]:.1f}%",
    (temperature[residue_idx], weight[residue_idx]),
    xytext=(8, 10), textcoords="offset points",
    color="#1f4e9c", fontsize=9
)

ax2.plot(
    temperature[peak_idx], dtg_up[peak_idx],
    marker="o", color="#c0392b", markersize=6, linestyle="none"
)
ax2.annotate(
    f"{temperature[peak_idx]:.0f} °C",
    (temperature[peak_idx], dtg_up[peak_idx]),
    xytext=(8, 10), textcoords="offset points",
    color="#c0392b", fontsize=9
)

ax1.legend([line1, line2], [line1.get_label(), line2.get_label()], loc="center left")
ax1.grid(True, alpha=0.25)
ax1.invert_xaxis()
fig.tight_layout()
fig.savefig(OUT_DIR / "Raw.png", dpi=300, bbox_inches="tight")
plt.close(fig)
