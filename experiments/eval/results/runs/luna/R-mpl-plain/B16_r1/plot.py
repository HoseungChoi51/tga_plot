from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

DATA_FILE = Path("/home/chs/Work/tga_plot/eval/inputs_b/caox.csv")
OUT_DIR = Path("/home/chs/Work/tga_plot/eval/results/runs/luna/R-mpl-plain/B16_r1/out")

# Read the CSV and use its temperature, weight, and derivative-weight columns.
df = pd.read_csv(DATA_FILE)
df.columns = [str(column).strip() for column in df.columns]

temperature_col = next(
    column for column in df.columns
    if "temperature" in column.lower() or "온도" in column
)
weight_col = next(
    column for column in df.columns
    if "weight" in column.lower()
    and "deriv" not in column.lower()
    and "derivative" not in column.lower()
)
dtg_col = next(
    column for column in df.columns
    if "deriv" in column.lower() or "dtg" in column.lower()
)

temperature = pd.to_numeric(df[temperature_col], errors="coerce")
weight = pd.to_numeric(df[weight_col], errors="coerce")
dtg = pd.to_numeric(df[dtg_col], errors="coerce")
valid = temperature.notna() & weight.notna() & dtg.notna()
temperature, weight, dtg = temperature[valid], weight[valid], dtg[valid]

OUT_DIR.mkdir(parents=True, exist_ok=True)
plt.rcParams["font.family"] = "Noto Sans CJK KR"
plt.rcParams["axes.unicode_minus"] = False

fig, (ax_weight, ax_dtg) = plt.subplots(
    2, 1, figsize=(8, 7), sharex=True,
    gridspec_kw={"height_ratios": [1, 1], "hspace": 0.08}
)

ax_weight.plot(temperature, weight, color="black", linewidth=1.5)
ax_weight.set_ylabel("Weight (%)")
ax_weight.grid(True, linestyle="--", alpha=0.35)

ax_dtg.plot(temperature, dtg, color="tab:blue", linewidth=1.3)
ax_dtg.set_xlabel("Temperature (°C)")
ax_dtg.set_ylabel("DTG (%/°C)")
ax_dtg.grid(True, linestyle="--", alpha=0.35)

ax_dtg.set_xlim(temperature.min(), temperature.max())
fig.tight_layout()
fig.savefig(OUT_DIR / "caox_weight_dtg.png", dpi=300, bbox_inches="tight")
plt.close(fig)
