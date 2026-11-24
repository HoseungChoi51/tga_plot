from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

DATA_FILE = Path("/home/chs/Work/tga_plot/eval/inputs_b/cnt_batches.xlsx")
OUT_DIR = Path("/home/chs/Work/tga_plot/eval/results/runs/luna/R-mpl-plain/B22_r2/out")
OUT_DIR.mkdir(parents=True, exist_ok=True)

# Read the Raw worksheet and select temperature and weight columns by header.
df = pd.read_excel(DATA_FILE, sheet_name="Raw")
df.columns = [str(column).strip() for column in df.columns]

temperature = pd.to_numeric(df["Temperature (°C)"], errors="coerce")
weight = pd.to_numeric(df["Weight (%)"], errors="coerce")
valid = temperature.notna() & weight.notna()

data = pd.DataFrame({
    "temperature": temperature[valid],
    "weight": weight[valid],
}).sort_values("temperature")

# Normalize the weight so that the interpolated value at 150 °C is 100%.
reference_temperature = 150.0
reference_weight = np.interp(
    reference_temperature,
    data["temperature"].to_numpy(),
    data["weight"].to_numpy(),
)
if not np.isfinite(reference_weight) or reference_weight == 0:
    raise ValueError("150 °C에서의 기준 무게를 계산할 수 없습니다.")

normalized_weight = data["weight"] / reference_weight * 100.0

plt.rcParams["font.family"] = "Noto Sans CJK KR"
plt.rcParams["axes.unicode_minus"] = False

fig, ax = plt.subplots(figsize=(8, 5.2))
ax.plot(
    data["temperature"],
    normalized_weight,
    color="#2369a1",
    linewidth=2,
)
ax.axvline(
    reference_temperature,
    color="0.45",
    linestyle="--",
    linewidth=1,
    label=f"기준 온도: {reference_temperature:.0f} °C",
)
ax.axhline(100, color="0.7", linestyle=":", linewidth=1)

ax.set_xlabel("온도 (°C)")
ax.set_ylabel("건조 기준 무게 (%)")
ax.set_title("Raw 시트 — 150 °C 기준 무게 정규화")
ax.grid(True, alpha=0.25)
ax.legend(frameon=False)
fig.tight_layout()

output_file = OUT_DIR / "raw_weight_dry_basis.png"
fig.savefig(output_file, dpi=300, bbox_inches="tight")
plt.close(fig)
