from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

DATA_FILE = "/home/chs/Work/tga_plot/eval/inputs_b/polymers.xlsx"
OUT_DIR = "/home/chs/Work/tga_plot/eval/results/runs/luna/R-mpl-brief/B07_r2/out"

plt.rcParams["font.family"] = "Noto Sans CJK KR"
plt.rcParams["axes.unicode_minus"] = False

out_dir = Path(OUT_DIR)
out_dir.mkdir(parents=True, exist_ok=True)

# 두 번째 시트만 읽습니다.
df = pd.read_excel(DATA_FILE, sheet_name=1)
df.columns = [str(col).strip() for col in df.columns]

temperature_col = next(
    col for col in df.columns if "temperature" in col.lower() or "온도" in col
)
weight_col = next(
    col for col in df.columns if "weight" in col.lower() or "무게" in col
)
dtg_col = next(
    (col for col in df.columns if "deriv" in col.lower() or "dtg" in col.lower()),
    None,
)

temperature = pd.to_numeric(df[temperature_col], errors="coerce")
weight = pd.to_numeric(df[weight_col], errors="coerce")
valid = temperature.notna() & weight.notna()
temperature = temperature[valid].to_numpy()
weight = weight[valid].to_numpy()

sheet_name = pd.ExcelFile(DATA_FILE).sheet_names[1]

fig, ax1 = plt.subplots(figsize=(9, 6))
ax1.plot(temperature, weight, color="#1f4e9c", linewidth=1.8, label="Weight")
ax1.set_xlabel("Temperature (°C)")
ax1.set_ylabel("Weight (%)", color="#1f4e9c")
ax1.tick_params(axis="y", labelcolor="#1f4e9c")
ax1.set_title(sheet_name)
ax1.grid(True, linestyle="--", alpha=0.35)

# 요청한 온도에 가장 가까운 측정값을 표시합니다.
for target in (300, 600):
    idx = int(np.argmin(np.abs(temperature - target)))
    measured_temp = temperature[idx]
    measured_weight = weight[idx]
    ax1.scatter(
        measured_temp,
        measured_weight,
        color="#1f4e9c",
        edgecolor="white",
        linewidth=0.8,
        zorder=5,
    )
    ax1.annotate(
        f"{target} °C: {measured_weight:.1f}%",
        xy=(measured_temp, measured_weight),
        xytext=(8, 12 if target == 300 else -20),
        textcoords="offset points",
        fontsize=9,
        color="#1f4e9c",
        bbox={"boxstyle": "round,pad=0.25", "fc": "white", "ec": "#1f4e9c", "alpha": 0.9},
        arrowprops={"arrowstyle": "-", "color": "#1f4e9c", "lw": 0.8},
    )

if dtg_col is not None:
    dtg_all = pd.to_numeric(df[dtg_col], errors="coerce")
    dtg = dtg_all[valid].to_numpy()
    valid_dtg = np.isfinite(dtg)
    if valid_dtg.any():
        ax2 = ax1.twinx()
        ax2.plot(
            temperature[valid_dtg],
            -dtg[valid_dtg],
            color="#c0392b",
            linewidth=1.5,
            label="DTG",
        )
        ax2.set_ylabel("DTG (%/°C)", color="#c0392b")
        ax2.tick_params(axis="y", labelcolor="#c0392b")
        lines1, labels1 = ax1.get_legend_handles_labels()
        lines2, labels2 = ax2.get_legend_handles_labels()
        ax1.legend(lines1 + lines2, labels1 + labels2, loc="center left")
else:
    ax1.legend(loc="center left")

fig.tight_layout()
fig.savefig(out_dir / f"{sheet_name}.png", dpi=300, bbox_inches="tight")
plt.close(fig)
