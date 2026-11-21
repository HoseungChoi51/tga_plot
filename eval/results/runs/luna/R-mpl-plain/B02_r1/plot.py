from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from scipy.signal import find_peaks

DATA_FILE = Path("/home/chs/Work/tga_plot/eval/inputs_b/caox.csv")
OUT_DIR = Path("/home/chs/Work/tga_plot/eval/results/runs/luna/R-mpl-plain/B02_r1/out")
OUT_DIR.mkdir(parents=True, exist_ok=True)

plt.rcParams["font.family"] = "Noto Sans CJK KR"
plt.rcParams["axes.unicode_minus"] = False

df = pd.read_csv(DATA_FILE)
df.columns = [str(column).strip() for column in df.columns]


def find_column(fragment):
    matches = [column for column in df.columns if fragment.lower() in column.lower()]
    if not matches:
        raise ValueError(f"'{fragment}' 열을 찾지 못했습니다. 열 이름: {list(df.columns)}")
    return matches[0]


temperature = pd.to_numeric(df[find_column("Temperature")], errors="coerce").to_numpy()
weight = pd.to_numeric(df[find_column("Weight (%)")], errors="coerce").to_numpy()
heat_flow = pd.to_numeric(df[find_column("Heat Flow")], errors="coerce").to_numpy()

valid = np.isfinite(temperature) & np.isfinite(weight) & np.isfinite(heat_flow)
temperature, weight, heat_flow = temperature[valid], weight[valid], heat_flow[valid]

order = np.argsort(temperature)
temperature, weight, heat_flow = temperature[order], weight[order], heat_flow[order]

# Smooth the signal for peak detection while plotting the original data.
heat_flow_smooth = (
    pd.Series(heat_flow)
    .rolling(window=9, center=True, min_periods=1)
    .mean()
    .to_numpy()
)

positive_count = np.count_nonzero(heat_flow_smooth > 0)
negative_count = np.count_nonzero(heat_flow_smooth < 0)
endothermic_sign = 1 if positive_count <= negative_count else -1

prominence = max(float(np.nanstd(heat_flow_smooth)) * 0.15, 1e-6)
minimum_distance = max(1, len(temperature) // 50)

endothermic_indices, _ = find_peaks(
    endothermic_sign * heat_flow_smooth,
    prominence=prominence,
    distance=minimum_distance,
)
exothermic_indices, _ = find_peaks(
    -endothermic_sign * heat_flow_smooth,
    prominence=prominence,
    distance=minimum_distance,
)

if len(endothermic_indices) < 2:
    endothermic_indices = np.argsort(endothermic_sign * heat_flow_smooth)[-2:]
endothermic_indices = sorted(
    endothermic_indices,
    key=lambda index: endothermic_sign * heat_flow_smooth[index],
    reverse=True,
)[:2]

if len(exothermic_indices) == 0:
    exothermic_indices = np.array(
        [np.argmin(endothermic_sign * heat_flow_smooth)]
    )
exothermic_index = max(
    exothermic_indices,
    key=lambda index: -endothermic_sign * heat_flow_smooth[index],
)

fig, ax_weight = plt.subplots(figsize=(10, 6))
ax_heat = ax_weight.twinx()

weight_line, = ax_weight.plot(
    temperature, weight, color="#2457A6", linewidth=2.0, label="Weight"
)
heat_line, = ax_heat.plot(
    temperature, heat_flow, color="#C44E52", linewidth=1.7, label="Heat Flow"
)

ax_weight.set_xlabel("Temperature (°C)")
ax_weight.set_ylabel("Weight (%)", color="#2457A6")
ax_heat.set_ylabel("Heat Flow (W/g)", color="#C44E52")
ax_weight.tick_params(axis="y", colors="#2457A6")
ax_heat.tick_params(axis="y", colors="#C44E52")
ax_weight.grid(True, which="major", linestyle="--", alpha=0.35)

for index, label in zip(endothermic_indices, ("흡열 피크 1", "흡열 피크 2")):
    ax_heat.scatter(
        temperature[index], heat_flow[index], color="#C44E52", s=45, zorder=5
    )
    ax_heat.annotate(
        f"{label}\n{temperature[index]:.1f} °C",
        xy=(temperature[index], heat_flow[index]),
        xytext=(8, 12),
        textcoords="offset points",
        fontsize=9,
        color="#8E3034",
        arrowprops=dict(arrowstyle="->", color="#8E3034", lw=0.9),
    )

ax_heat.scatter(
    temperature[exothermic_index],
    heat_flow[exothermic_index],
    color="#4C8C57",
    s=45,
    zorder=5,
)
ax_heat.annotate(
    f"발열 피크\n{temperature[exothermic_index]:.1f} °C",
    xy=(temperature[exothermic_index], heat_flow[exothermic_index]),
    xytext=(8, -30),
    textcoords="offset points",
    fontsize=9,
    color="#35653D",
    arrowprops=dict(arrowstyle="->", color="#35653D", lw=0.9),
)

ax_weight.set_title("TGA 및 Heat Flow")
ax_weight.legend(
    [weight_line, heat_line],
    ["Weight (%)", "Heat Flow (W/g)"],
    loc="best",
    frameon=False,
)

fig.tight_layout()
fig.savefig(OUT_DIR / "caox_tga_heat_flow.png", dpi=300, bbox_inches="tight")
plt.close(fig)
