from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

DATA_FILE = Path("/home/chs/Work/tga_plot/eval/inputs_b/cnt_batches.xlsx")
OUT_DIR = Path("/home/chs/Work/tga_plot/eval/results/runs/luna/R-mpl-brief/B22_r3/out")
SHEET_NAME = "Raw"

OUT_DIR.mkdir(parents=True, exist_ok=True)

plt.rcParams["font.family"] = "Noto Sans CJK KR"
plt.rcParams["axes.unicode_minus"] = False

df = pd.read_excel(DATA_FILE, sheet_name=SHEET_NAME)
df.columns = [str(col).strip() for col in df.columns]

temperature_col = next(
    col for col in df.columns
    if "temperature" in col.lower() or "온도" in col
)
weight_col = next(
    col for col in df.columns
    if "weight" in col.lower() or "무게" in col
)
dtg_col = next(
    col for col in df.columns
    if "deriv" in col.lower() or "dtg" in col.lower()
)

temperature = pd.to_numeric(df[temperature_col], errors="coerce").to_numpy()
weight = pd.to_numeric(df[weight_col], errors="coerce").to_numpy()
dtg = pd.to_numeric(df[dtg_col], errors="coerce").to_numpy()

valid = np.isfinite(temperature) & np.isfinite(weight)
temperature, weight = temperature[valid], weight[valid]
dtg = dtg[valid]

idx_150 = int(np.nanargmin(np.abs(temperature - 150.0)))
weight_at_150 = weight[idx_150]
if not np.isfinite(weight_at_150) or weight_at_150 == 0:
    raise ValueError("150 °C 기준 무게가 유효하지 않아 건조 기준 환산을 할 수 없습니다.")

dry_weight = weight / weight_at_150 * 100.0

# DTG는 원본의 %/°C 값을 건조 기준으로 환산하고, 표준 표시 방식에 따라 부호를 반전합니다.
dtg_dry = -dtg / weight_at_150 * 100.0

fig, ax1 = plt.subplots(figsize=(9, 6))
ax2 = ax1.twinx()

line1, = ax1.plot(
    temperature, dry_weight, color="#1f4e9c", linewidth=1.8,
    label="무게 (건조 기준, %)"
)
line2, = ax2.plot(
    temperature, dtg_dry, color="#c0392b", linewidth=1.5,
    label="DTG (건조 기준, %/°C)"
)

# 잔류량: 측정점 중 800 °C에 가장 가까운 무게
idx_800 = int(np.nanargmin(np.abs(temperature - 800.0)))
residue = dry_weight[idx_800]
ax1.scatter(
    temperature[idx_800], residue, color="#1f4e9c", edgecolor="white",
    linewidth=0.7, zorder=5
)
ax1.annotate(
    f"Residue {residue:.1f}%",
    (temperature[idx_800], residue),
    xytext=(8, 10), textcoords="offset points",
    color="#1f4e9c", fontsize=10
)

# 피크: 150 °C 초과 영역에서 가장 높은 양의 DTG 피크
peak_region = (temperature > 150.0) & np.isfinite(dtg_dry)
if peak_region.any():
    indices = np.flatnonzero(peak_region)
    peak_idx = indices[int(np.nanargmax(dtg_dry[peak_region]))]
    peak_temp = temperature[peak_idx]
    peak_value = dtg_dry[peak_idx]
    ax2.scatter(
        peak_temp, peak_value, color="#c0392b", edgecolor="white",
        linewidth=0.7, zorder=5
    )
    ax2.annotate(
        f"{peak_temp:.0f} °C",
        (peak_temp, peak_value),
        xytext=(8, 10), textcoords="offset points",
        color="#c0392b", fontsize=10
    )

ax1.set_title(SHEET_NAME)
ax1.set_xlabel("Temperature (°C)")
ax1.set_ylabel("Weight (dry basis, %)", color="#1f4e9c")
ax2.set_ylabel("DTG (dry basis, %/°C)", color="#c0392b")
ax1.tick_params(axis="y", labelcolor="#1f4e9c")
ax2.tick_params(axis="y", labelcolor="#c0392b")
ax1.grid(True, linestyle="--", alpha=0.35)
ax1.legend([line1, line2], [line1.get_label(), line2.get_label()], loc="center left")
fig.tight_layout()

output_file = OUT_DIR / "Raw_dry_basis.png"
fig.savefig(output_file, dpi=300, bbox_inches="tight")
plt.close(fig)
