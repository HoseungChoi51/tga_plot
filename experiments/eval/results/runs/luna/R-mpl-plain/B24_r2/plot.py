from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

DATA_FILE = Path("/home/chs/Work/tga_plot/eval/inputs_b/polymers.xlsx")
OUT_DIR = Path("/home/chs/Work/tga_plot/eval/results/runs/luna/R-mpl-plain/B24_r2/out")
OUT_DIR.mkdir(parents=True, exist_ok=True)

# Korean font support
plt.rcParams["font.family"] = "Noto Sans CJK KR"
plt.rcParams["axes.unicode_minus"] = False

df = pd.read_excel(DATA_FILE, sheet_name="PE")
df.columns = [str(column).strip() for column in df.columns]

temperature_c = pd.to_numeric(df["Temperature (°C)"], errors="coerce")
temperature_k = temperature_c + 273.15
weight = pd.to_numeric(df["Weight (%)"], errors="coerce")
derivative = pd.to_numeric(df["Deriv. Weight (%/°C)"], errors="coerce")

fig, ax1 = plt.subplots(figsize=(9, 5.5))
ax1.plot(temperature_k, weight, color="tab:blue", linewidth=1.8, label="Weight")
ax1.set_xlabel("온도 (K)")
ax1.set_ylabel("무게 (%)", color="tab:blue")
ax1.tick_params(axis="y", labelcolor="tab:blue")
ax1.set_xlim(left=temperature_k.min(), right=temperature_k.max())
ax1.grid(True, linestyle="--", alpha=0.35)

ax2 = ax1.twinx()
ax2.plot(
    temperature_k,
    derivative,
    color="tab:red",
    linewidth=1.4,
    label="Deriv. Weight",
)
ax2.set_ylabel("미분 무게 (%/K)", color="tab:red")
ax2.tick_params(axis="y", labelcolor="tab:red")

lines1, labels1 = ax1.get_legend_handles_labels()
lines2, labels2 = ax2.get_legend_handles_labels()
ax1.legend(lines1 + lines2, labels1 + labels2, loc="best", frameon=True)

ax1.set_title("PE 열중량 분석 (온도: K)")
fig.tight_layout()
fig.savefig(OUT_DIR / "PE_TGA_temperature_K.png", dpi=300, bbox_inches="tight")
plt.close(fig)
