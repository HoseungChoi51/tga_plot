from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

DATA_FILE = Path("/home/chs/Work/tga_plot/tests/inputs/TGA.xlsx")
OUT_DIR = Path("/home/chs/Work/tga_plot/eval/results/runs/luna/R-mpl-plain/10_r3/out")
OUT_DIR.mkdir(parents=True, exist_ok=True)

plt.rcParams["font.family"] = "Noto Sans CJK KR"
plt.rcParams["axes.unicode_minus"] = False

sheets = pd.read_excel(DATA_FILE, sheet_name=None)
fig, ax = plt.subplots(figsize=(10, 6))
colors = ["#2878B5", "#E07A26", "#3A923A"]

for (sheet_name, data), color in zip(sheets.items(), colors):
    data.columns = [str(col).strip() for col in data.columns]
    temperature = pd.to_numeric(data["Temperature"], errors="coerce")
    weight = pd.to_numeric(data["Weight(%)"], errors="coerce")
    valid = temperature.notna() & weight.notna()
    temperature = temperature[valid].to_numpy(dtype=float)
    weight = weight[valid].to_numpy(dtype=float)

    order = np.argsort(temperature)
    temperature = temperature[order]
    weight = weight[order]
    ax.plot(temperature, weight, label=sheet_name, color=color, linewidth=1.8)

    # 700 °C 측정값을 선형 보간하고 소수점 둘째 자리까지 표시합니다.
    if len(temperature) and temperature.min() <= 700 <= temperature.max():
        unique_temperature, unique_indices = np.unique(temperature, return_index=True)
        unique_weight = weight[unique_indices]
        residual = float(np.interp(700, unique_temperature, unique_weight))

        ax.scatter([700], [residual], color=color, s=34, zorder=4)
        ax.annotate(
            f"{residual:.2f}%",
            xy=(700, residual),
            xytext=(7, 7),
            textcoords="offset points",
            color=color,
            fontsize=9,
        )

ax.axvline(700, color="0.55", linestyle="--", linewidth=1, alpha=0.7)
ax.set_xlabel("Temperature (°C)")
ax.set_ylabel("Weight (%)")
ax.set_title("TGA")
ax.set_xlim(left=30)
ax.set_ylim(bottom=0)
ax.grid(True, alpha=0.25)
ax.legend(frameon=False)
fig.tight_layout()
fig.savefig(OUT_DIR / "TGA_residual_at_700C.png", dpi=300, bbox_inches="tight")
plt.close(fig)
