from pathlib import Path

import pandas as pd
import matplotlib.pyplot as plt

DATA_FILE = Path("/home/chs/Work/tga_plot/eval/inputs_b/caox.csv")
OUT_DIR = Path("/home/chs/Work/tga_plot/eval/results/runs/luna/R-mpl-plain/B16_r3/out")
OUT_DIR.mkdir(parents=True, exist_ok=True)

# CSV 파일 읽기
data = pd.read_csv(DATA_FILE)

# 미리보기의 열 이름 사용: Temperature (°C), Weight (%), Deriv. Weight (%/°C)
temperature = pd.to_numeric(data["Temperature (°C)"], errors="coerce")
weight = pd.to_numeric(data["Weight (%)"], errors="coerce")
dtg = pd.to_numeric(data["Deriv. Weight (%/°C)"], errors="coerce")

valid = temperature.notna() & weight.notna() & dtg.notna()
temperature = temperature[valid]
weight = weight[valid]
dtg = dtg[valid]

plt.rcParams["font.family"] = "Noto Sans CJK KR"
plt.rcParams["axes.unicode_minus"] = False

fig, (ax_weight, ax_dtg) = plt.subplots(
    2, 1,
    sharex=True,
    figsize=(9, 7),
    gridspec_kw={"height_ratios": [1, 1], "hspace": 0.08},
)

ax_weight.plot(temperature, weight, color="tab:blue", linewidth=1.6)
ax_weight.set_ylabel("무게 (%)")
ax_weight.set_title("TGA / DTG")
ax_weight.grid(True, alpha=0.3)

ax_dtg.plot(temperature, dtg, color="tab:red", linewidth=1.4)
ax_dtg.set_xlabel("온도 (°C)")
ax_dtg.set_ylabel("DTG (%/°C)")
ax_dtg.grid(True, alpha=0.3)

ax_weight.tick_params(axis="x", labelbottom=False)
fig.align_ylabels((ax_weight, ax_dtg))

fig.savefig(OUT_DIR / "caox_tga_dtg.png", dpi=300, bbox_inches="tight")
plt.close(fig)
