from pathlib import Path

import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

DATA_FILE = Path("/home/chs/Work/tga_plot/eval/inputs_b/polymers.xlsx")
OUT_DIR = Path("/home/chs/Work/tga_plot/eval/results/runs/luna/R-mpl-brief/B15_r3/out")

plt.rcParams["font.family"] = "Noto Sans CJK KR"
plt.rcParams["axes.unicode_minus"] = False

OUT_DIR.mkdir(parents=True, exist_ok=True)

sheets = pd.read_excel(DATA_FILE, sheet_name=None)
fig, ax1 = plt.subplots(figsize=(10, 6))
ax2 = ax1.twinx()

colors = {"PE": "#1f4e9c", "PVC": "#2e8b57", "PET": "#c0392b"}

for name, df in sheets.items():
    # 열 이름에 따라 온도, 무게, DTG 데이터를 가져옵니다.
    temperature = pd.to_numeric(df["Temperature (°C)"], errors="coerce")
    weight = pd.to_numeric(df["Weight (%)"], errors="coerce")
    dtg = pd.to_numeric(df["Deriv. Weight (%/°C)"], errors="coerce")
    valid = temperature.notna() & weight.notna() & dtg.notna()
    temperature, weight, dtg = temperature[valid], weight[valid], dtg[valid]

    color = colors.get(name, None)
    ax1.plot(temperature, weight, color=color, linewidth=1.8, label=f"{name} Weight")
    ax2.plot(temperature, -dtg, color=color, linewidth=1.5, linestyle="--", label=f"{name} DTG")

    # 800 °C에 가장 가까운 측정점의 잔류량 표시
    residue_idx = (temperature - 800).abs().idxmin()
    residue_x = temperature.loc[residue_idx]
    residue_y = weight.loc[residue_idx]
    ax1.scatter(residue_x, residue_y, color=color, s=30, zorder=4)
    ax1.annotate(
        f"{name} Residue {residue_y:.1f}%",
        xy=(residue_x, residue_y),
        xytext=(5, 8),
        textcoords="offset points",
        color=color,
        fontsize=8,
    )

    # 150 °C 초과 영역에서 위쪽으로 표시한 DTG의 최고점
    peak_region = temperature > 150
    if peak_region.any():
        peak_idx = (-dtg[peak_region]).idxmax()
        peak_x = temperature.loc[peak_idx]
        peak_y = -dtg.loc[peak_idx]
        ax2.scatter(peak_x, peak_y, color=color, marker="^", s=35, zorder=4)
        ax2.annotate(
            f"{name} {peak_x:.0f} °C",
            xy=(peak_x, peak_y),
            xytext=(5, 6),
            textcoords="offset points",
            color=color,
            fontsize=8,
        )

ax1.set_xlabel("Temperature (°C)")
ax1.set_ylabel("Weight (%)")
ax2.set_ylabel("DTG (-%/°C)")
ax1.set_title("PE, PVC, PET")
ax1.grid(True, alpha=0.25)

# 두 축의 선을 하나의 범례로 합쳐 그래프 오른쪽 바깥에 배치
handles1, labels1 = ax1.get_legend_handles_labels()
handles2, labels2 = ax2.get_legend_handles_labels()
ax1.legend(
    handles1 + handles2,
    labels1 + labels2,
    loc="center left",
    bbox_to_anchor=(1.12, 0.5),
    frameon=False,
)

fig.tight_layout()
fig.savefig(OUT_DIR / "polymers_overlay.png", dpi=300, bbox_inches="tight")
plt.close(fig)
