from pathlib import Path

import pandas as pd
import matplotlib.pyplot as plt

DATA_FILE = Path("/home/chs/Work/tga_plot/eval/inputs_b/polymers.xlsx")
OUT_DIR = Path("/home/chs/Work/tga_plot/eval/results/runs/luna/R-mpl-plain/B24_r3/out")
OUT_DIR.mkdir(parents=True, exist_ok=True)

# Read the PE worksheet and use the column headers from the workbook.
df = pd.read_excel(DATA_FILE, sheet_name="PE")
df.columns = [str(col).strip() for col in df.columns]

temperature_c = pd.to_numeric(df["Temperature (°C)"], errors="coerce")
weight = pd.to_numeric(df["Weight (%)"], errors="coerce")
derivative = pd.to_numeric(df["Deriv. Weight (%/°C)"], errors="coerce")

temperature_k = temperature_c + 273.15
valid = temperature_k.notna() & weight.notna() & derivative.notna()
temperature_k = temperature_k[valid]
weight = weight[valid]
derivative = derivative[valid]

plt.rcParams["font.family"] = "Noto Sans CJK KR"
plt.rcParams["axes.unicode_minus"] = False

fig, ax1 = plt.subplots(figsize=(9, 6))
ax1.plot(temperature_k, weight, color="tab:blue", linewidth=1.8, label="Weight")
ax1.set_xlabel("온도 (K)")
ax1.set_ylabel("Weight (%)", color="tab:blue")
ax1.tick_params(axis="y", labelcolor="tab:blue")
ax1.grid(True, linestyle="--", alpha=0.35)

ax2 = ax1.twinx()
ax2.plot(
    temperature_k,
    derivative,
    color="tab:red",
    linewidth=1.5,
    label="Derivative weight",
)
ax2.set_ylabel("Deriv. Weight (%/K)", color="tab:red")
ax2.tick_params(axis="y", labelcolor="tab:red")

ax1.set_title("PE TGA — Temperature in Kelvin")
fig.tight_layout()
fig.savefig(OUT_DIR / "PE_TGA_temperature_K.png", dpi=300, bbox_inches="tight")
plt.close(fig)
