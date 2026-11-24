from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

DATA_FILE = Path("/home/chs/Work/tga_plot/tests/inputs/TGA.xlsx")
OUT_DIR = Path("/home/chs/Work/tga_plot/eval/results/runs/luna/R-mpl-brief/04_r2/out")
SHEET_NAME = "1006R1-V normal"

OUT_DIR.mkdir(parents=True, exist_ok=True)
plt.rcParams["font.family"] = "Noto Sans CJK KR"
plt.rcParams["axes.unicode_minus"] = False

df = pd.read_excel(DATA_FILE, sheet_name=SHEET_NAME)
df.columns = [str(col).strip() for col in df.columns]

def find_column(candidates):
    for candidate in candidates:
        for col in df.columns:
            if candidate.lower() in col.lower():
                return col
    raise KeyError(f"필요한 열을 찾을 수 없습니다: {candidates}")

x_col = find_column(["Temperature", "온도"])
weight_col = find_column(["Weight", "무게", "중량"])
dtg_col = find_column(["D.W", "DTG", "Derivative"])

data = df[[x_col, weight_col, dtg_col]].apply(pd.to_numeric, errors="coerce").dropna()
temperature = data[x_col].to_numpy()
weight = data[weight_col].to_numpy()
dtg = data[dtg_col].to_numpy()

fig, ax1 = plt.subplots(figsize=(9, 6))
ax2 = ax1.twinx()

weight_line, = ax1.plot(temperature, weight, color="#1f4e9c", label="Weight (%)")
dtg_line, = ax2.plot(temperature, -dtg, color="#c0392b", label="DTG")

ax1.set_title("CNT 산화 거동", fontsize=18, color="navy")
ax1.set_xlabel("Temperature (°C)")
ax1.set_ylabel("Weight (%)")
ax2.set_ylabel("DTG (-%/°C)")

# Residue at the measured point nearest 800 °C
residue_idx = int(np.nanargmin(np.abs(temperature - 800)))
ax1.plot(temperature[residue_idx], weight[residue_idx], "o", color="#1f4e9c")
ax1.annotate(
    f"Residue {weight[residue_idx]:.1f}%",
    (temperature[residue_idx], weight[residue_idx]),
    xytext=(8, 8),
    textcoords="offset points",
    color="#1f4e9c",
)

# Highest positive DTG peak above 150 °C
eligible = np.flatnonzero(temperature > 150)
if eligible.size:
    peak_idx = int(eligible[np.nanargmax((-dtg)[eligible])])
    ax2.plot(temperature[peak_idx], (-dtg)[peak_idx], "o", color="#c0392b")
    ax2.annotate(
        f"{temperature[peak_idx]:.0f} °C",
        (temperature[peak_idx], (-dtg)[peak_idx]),
        xytext=(8, 8),
        textcoords="offset points",
        color="#c0392b",
    )

ax1.legend([weight_line, dtg_line], ["Weight (%)", "DTG"], loc="center left")
fig.tight_layout()
fig.savefig(OUT_DIR / "1006R1-V normal.png", dpi=300, bbox_inches="tight")
plt.close(fig)
