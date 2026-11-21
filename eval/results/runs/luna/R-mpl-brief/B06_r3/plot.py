from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

DATA_FILE = Path("/home/chs/Work/tga_plot/eval/inputs_b/isothermal.txt")
OUT_DIR = Path("/home/chs/Work/tga_plot/eval/results/runs/luna/R-mpl-brief/B06_r3/out")
OUT_DIR.mkdir(parents=True, exist_ok=True)

plt.rcParams["font.family"] = "Noto Sans CJK KR"
plt.rcParams["axes.unicode_minus"] = False

# Read the tabular text file, detecting its delimiter.
df = pd.read_csv(DATA_FILE, sep=None, engine="python", comment="#")
if df.shape[1] < 3:
    # Fallback for whitespace-delimited text.
    df = pd.read_csv(DATA_FILE, sep=r"\s+", engine="python", comment="#")

# Columns: time (min), temperature (°C), weight (%).
time = pd.to_numeric(df.iloc[:, 0], errors="coerce")
temperature = pd.to_numeric(df.iloc[:, 1], errors="coerce")
weight = pd.to_numeric(df.iloc[:, 2], errors="coerce")
valid = time.notna() & temperature.notna() & weight.notna()
time, temperature, weight = time[valid], temperature[valid], weight[valid]

fig, ax1 = plt.subplots(figsize=(8, 5))
weight_line, = ax1.plot(time, weight, color="#1f4e9c", linewidth=2, label="무게")
ax1.set_xlabel("시간 (분)")
ax1.set_ylabel("무게 (%)", color="#1f4e9c")
ax1.tick_params(axis="y", labelcolor="#1f4e9c")

ax2 = ax1.twinx()
temperature_line, = ax2.plot(
    time, temperature, color="#c0392b", linewidth=2, label="온도"
)
ax2.set_ylabel("온도 (°C)", color="#c0392b")
ax2.tick_params(axis="y", labelcolor="#c0392b")

# Mark the measured weight nearest 140 minutes.
target_time = 140.0
idx = (time - target_time).abs().idxmin()
x_mark = float(time.loc[idx])
weight_mark = float(weight.loc[idx])
ax1.scatter([x_mark], [weight_mark], color="#1f4e9c", edgecolor="white",
            linewidth=0.8, zorder=5)
ax1.annotate(
    f"{weight_mark:.2f}%",
    xy=(x_mark, weight_mark),
    xytext=(-10, 12),
    textcoords="offset points",
    ha="right",
    color="#1f4e9c",
    fontsize=10,
)

ax1.legend(
    [weight_line, temperature_line],
    ["무게", "온도"],
    loc="best",
)
ax1.grid(True, alpha=0.25)
ax1.set_title("Isothermal")
fig.tight_layout()

fig.savefig(OUT_DIR / "isothermal.png", dpi=300, bbox_inches="tight")
plt.close(fig)
