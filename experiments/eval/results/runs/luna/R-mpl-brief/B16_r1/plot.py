from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

DATA_FILE = "/home/chs/Work/tga_plot/eval/inputs_b/caox.csv"
OUT_DIR = "/home/chs/Work/tga_plot/eval/results/runs/luna/R-mpl-brief/B16_r1/out"

plt.rcParams["font.family"] = "Noto Sans CJK KR"
plt.rcParams["axes.unicode_minus"] = False

out_dir = Path(OUT_DIR)
out_dir.mkdir(parents=True, exist_ok=True)

df = pd.read_csv(DATA_FILE)
df.columns = [str(c).strip() for c in df.columns]

def find_column(keywords):
    for col in df.columns:
        if any(word.lower() in col.lower() for word in keywords):
            return col
    return None

temperature_col = find_column(["temperature", "temp", "온도"])
weight_col = find_column(["weight", "mass", "무게", "중량"])
dtg_col = find_column(["deriv", "dtg"])

# Fall back to the expected TGA column order if headers are not recognizable.
if temperature_col is None and len(df.columns) > 1:
    temperature_col = df.columns[1]
if weight_col is None and len(df.columns) > 2:
    weight_col = df.columns[2]
if dtg_col is None and len(df.columns) > 3:
    dtg_col = df.columns[3]

if temperature_col is None or weight_col is None or dtg_col is None:
    raise ValueError("온도, 무게, DTG 열을 찾을 수 없습니다.")

x = pd.to_numeric(df[temperature_col], errors="coerce").to_numpy()
weight = pd.to_numeric(df[weight_col], errors="coerce").to_numpy()
dtg = pd.to_numeric(df[dtg_col], errors="coerce").to_numpy()

valid = np.isfinite(x) & np.isfinite(weight) & np.isfinite(dtg)
x, weight, dtg = x[valid], weight[valid], dtg[valid]
if x.size == 0:
    raise ValueError("그릴 수 있는 유효한 데이터가 없습니다.")

order = np.argsort(x)
x, weight, dtg = x[order], weight[order], dtg[order]

fig, (ax_weight, ax_dtg) = plt.subplots(
    2, 1, figsize=(9, 8), sharex=True,
    gridspec_kw={"height_ratios": [1, 1], "hspace": 0.08}
)

ax_weight.plot(x, weight, color="#1f4e9c", linewidth=1.8, label="Weight")
ax_weight.set_ylabel("Weight (%)")
ax_weight.set_title(Path(DATA_FILE).stem)
ax_weight.grid(True, alpha=0.25)

# Residue: measured weight nearest 800 °C.
residue_idx = int(np.argmin(np.abs(x - 800)))
ax_weight.scatter(x[residue_idx], weight[residue_idx], color="#1f4e9c", zorder=3)
ax_weight.annotate(
    f"Residue {weight[residue_idx]:.1f}%",
    xy=(x[residue_idx], weight[residue_idx]),
    xytext=(8, 10),
    textcoords="offset points",
    color="#1f4e9c",
    fontsize=10,
)

# Plot -DTG so mass-loss peaks point upward; label the highest peak above 150 °C.
dtg_plot = -dtg
peak_candidates = np.flatnonzero((x > 150) & np.isfinite(dtg_plot))
ax_dtg.plot(x, dtg_plot, color="#c0392b", linewidth=1.8, label="-DTG")
ax_dtg.set_xlabel("Temperature (°C)")
ax_dtg.set_ylabel("-DTG (%/°C)")
ax_dtg.grid(True, alpha=0.25)

if peak_candidates.size:
    peak_idx = peak_candidates[np.argmax(dtg_plot[peak_candidates])]
    ax_dtg.scatter(x[peak_idx], dtg_plot[peak_idx], color="#c0392b", zorder=3)
    ax_dtg.annotate(
        f"{x[peak_idx]:.0f} °C",
        xy=(x[peak_idx], dtg_plot[peak_idx]),
        xytext=(8, 10),
        textcoords="offset points",
        color="#c0392b",
        fontsize=10,
    )

fig.align_ylabels()
fig.savefig(out_dir / "caox_separate_weight_dtg.png", dpi=300, bbox_inches="tight")
plt.close(fig)
