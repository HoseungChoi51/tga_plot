from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd
from scipy.signal import find_peaks

DATA_FILE = Path("/home/chs/Work/tga_plot/tests/inputs/TGA.xlsx")
OUT_DIR = Path("/home/chs/Work/tga_plot/eval/results/runs/luna/R-mpl-plain/03_r1/out")
SHEET_NAME = "1006R1-V acid"

OUT_DIR.mkdir(parents=True, exist_ok=True)

df = pd.read_excel(DATA_FILE, sheet_name=SHEET_NAME)
df.columns = [str(column).strip() for column in df.columns]

temperature = pd.to_numeric(df["Temperature"], errors="coerce")
weight = pd.to_numeric(df["Weight(%)"], errors="coerce")
derivative = pd.to_numeric(df["D.W(%/C)"], errors="coerce")

plot_data = pd.DataFrame({
    "Temperature": temperature,
    "Weight(%)": weight,
    "D.W(%/C)": derivative,
}).dropna()
plot_data = plot_data[
    plot_data["Temperature"].between(100, 800)
].sort_values("Temperature")

# D.W(%/C)는 질량 감소가 음의 방향으로 나타나므로, 감소 피크 두 개를 표시합니다.
x = plot_data["Temperature"].to_numpy()
y = plot_data["D.W(%/C)"].to_numpy()
peak_indices, _ = find_peaks(-y, distance=max(1, len(y) // 20), prominence=0.01)

if len(peak_indices) < 2:
    peak_indices = find_peaks(-y, distance=max(1, len(y) // 20))[0]

if len(peak_indices) >= 2:
    selected = sorted(peak_indices, key=lambda index: y[index])[:2]
else:
    selected = sorted(range(len(y)), key=lambda index: y[index])[:2]

fig, ax_weight = plt.subplots(figsize=(9, 6))
ax_derivative = ax_weight.twinx()

ax_weight.plot(
    plot_data["Temperature"],
    plot_data["Weight(%)"],
    color="tab:blue",
    linewidth=2,
    label="Weight (%)",
)
ax_derivative.plot(
    x,
    y,
    color="tab:red",
    linewidth=1.8,
    label="D.W (%/°C)",
)

for number, index in enumerate(selected, start=1):
    peak_temp = x[index]
    peak_value = y[index]
    ax_derivative.scatter(
        peak_temp, peak_value, color="black", s=45, zorder=5
    )
    ax_derivative.annotate(
        f"Peak {number}\n{peak_temp:.1f} °C",
        xy=(peak_temp, peak_value),
        xytext=(8, -24 if number == 1 else 12),
        textcoords="offset points",
        fontsize=9,
        arrowprops={"arrowstyle": "->", "color": "black", "lw": 0.8},
    )

ax_weight.set_xlim(100, 800)
ax_weight.set_xlabel("Temperature (°C)")
ax_weight.set_ylabel("Weight (%)", color="tab:blue")
ax_derivative.set_ylabel("D.W (%/°C)", color="tab:red")
ax_weight.set_title("1006R1-V acid")
ax_weight.grid(True, linestyle="--", alpha=0.35)
ax_weight.tick_params(axis="y", labelcolor="tab:blue")
ax_derivative.tick_params(axis="y", labelcolor="tab:red")

handles1, labels1 = ax_weight.get_legend_handles_labels()
handles2, labels2 = ax_derivative.get_legend_handles_labels()
ax_weight.legend(handles1 + handles2, labels1 + labels2, loc="best")

fig.tight_layout()
fig.savefig(OUT_DIR / "1006R1-V_acid.png", dpi=300, bbox_inches="tight")
plt.close(fig)
