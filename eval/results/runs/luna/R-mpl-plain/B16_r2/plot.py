from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd

DATA_FILE = Path("/home/chs/Work/tga_plot/eval/inputs_b/caox.csv")
OUT_DIR = Path("/home/chs/Work/tga_plot/eval/results/runs/luna/R-mpl-plain/B16_r2/out")

OUT_DIR.mkdir(parents=True, exist_ok=True)

# Read the CSV and identify the requested columns by their headers.
df = pd.read_csv(DATA_FILE)
df.columns = df.columns.astype(str).str.strip()

temperature_col = next(c for c in df.columns if "Temperature" in c)
weight_col = next(c for c in df.columns if "Weight (%)" in c)
dtg_col = next(c for c in df.columns if "Deriv. Weight" in c)

temperature = pd.to_numeric(df[temperature_col], errors="coerce")
weight = pd.to_numeric(df[weight_col], errors="coerce")
dtg = pd.to_numeric(df[dtg_col], errors="coerce")

valid = temperature.notna() & weight.notna() & dtg.notna()
temperature, weight, dtg = temperature[valid], weight[valid], dtg[valid]

plt.rcParams["font.family"] = "Noto Sans CJK KR"
plt.rcParams["axes.unicode_minus"] = False

fig, (ax_weight, ax_dtg) = plt.subplots(
    2, 1, sharex=True, figsize=(8, 7), constrained_layout=True
)

ax_weight.plot(temperature, weight, color="tab:blue", linewidth=1.5)
ax_weight.set_ylabel("무게 (%)")
ax_weight.set_title("TGA / DTG")
ax_weight.grid(True, alpha=0.3)

ax_dtg.plot(temperature, dtg, color="tab:red", linewidth=1.5)
ax_dtg.set_xlabel("온도 (°C)")
ax_dtg.set_ylabel("DTG (%/°C)")
ax_dtg.grid(True, alpha=0.3)

fig.savefig(OUT_DIR / "caox_tga_dtg.png", dpi=300, bbox_inches="tight")
plt.close(fig)
