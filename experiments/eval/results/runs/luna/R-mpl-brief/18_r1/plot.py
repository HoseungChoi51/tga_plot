from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.ticker import MultipleLocator

DATA_FILE = Path("/home/chs/Work/tga_plot/tests/inputs/TGA.xlsx")
OUT_DIR = Path("/home/chs/Work/tga_plot/eval/results/runs/luna/R-mpl-brief/18_r1/out")

OUT_DIR.mkdir(parents=True, exist_ok=True)
plt.rcParams["font.family"] = "Noto Sans CJK KR"
plt.rcParams["axes.unicode_minus"] = False


def find_column(columns, keyword):
    for col in columns:
        if keyword.lower() in str(col).lower():
            return col
    raise ValueError(f"열을 찾을 수 없습니다: {keyword}")


def safe_filename(name):
    cleaned = "".join(c if c.isalnum() or c in "-_ ." else "_" for c in str(name))
    return cleaned.strip().replace(" ", "_") or "sheet"


sheets = pd.read_excel(DATA_FILE, sheet_name=None)

for sheet_name, df in sheets.items():
    if df.empty:
        continue

    x_col = find_column(df.columns, "temperature")
    weight_col = find_column(df.columns, "weight")
    dtg_col = find_column(df.columns, "d.w")

    x = pd.to_numeric(df[x_col], errors="coerce")
    weight = pd.to_numeric(df[weight_col], errors="coerce")
    dtg = pd.to_numeric(df[dtg_col], errors="coerce")
    valid = x.notna() & weight.notna() & dtg.notna()
    x = x[valid].to_numpy()
    weight = weight[valid].to_numpy()
    dtg = dtg[valid].to_numpy()

    if not len(x):
        continue

    fig, ax1 = plt.subplots(figsize=(10, 6))
    ax2 = ax1.twinx()

    ax1.plot(x, weight, color="#1f4e9c", label="Weight (%)")
    # TGA의 질량 감소 DTG는 음수이므로 부호를 반전해 피크가 위를 향하도록 표시
    dtg_plot = -dtg
    ax2.plot(x, dtg_plot, color="#c0392b", label="DTG")

    ax1.set_title(str(sheet_name))
    ax1.set_xlabel("Temperature (°C)")
    ax1.set_ylabel("Weight (%)")
    ax2.set_ylabel("DTG (-%/°C)")
    ax1.xaxis.set_major_locator(MultipleLocator(100))
    ax2.set_ylim(-0.05, 1.2)

    # 잔류량: 800 °C에 가장 가까운 측정점
    residue_idx = int(np.argmin(np.abs(x - 800)))
    ax1.plot(x[residue_idx], weight[residue_idx], "o", color="#1f4e9c")
    ax1.annotate(
        f"Residue {weight[residue_idx]:.1f}%",
        (x[residue_idx], weight[residue_idx]),
        xytext=(8, 8),
        textcoords="offset points",
        color="#1f4e9c",
    )

    # 피크: 150 °C 초과 영역에서 가장 높은 부호 반전 DTG 값
    peak_candidates = np.flatnonzero(x > 150)
    if len(peak_candidates):
        peak_idx = peak_candidates[np.argmax(dtg_plot[peak_candidates])]
        ax2.plot(x[peak_idx], dtg_plot[peak_idx], "o", color="#c0392b")
        ax2.annotate(
            f"{x[peak_idx]:.0f} °C",
            (x[peak_idx], dtg_plot[peak_idx]),
            xytext=(8, 8),
            textcoords="offset points",
            color="#c0392b",
        )

    ax1.grid(True, alpha=0.3)
    handles1, labels1 = ax1.get_legend_handles_labels()
    handles2, labels2 = ax2.get_legend_handles_labels()
    ax1.legend(handles1 + handles2, labels1 + labels2, loc="center left")

    fig.tight_layout()
    fig.savefig(OUT_DIR / f"{safe_filename(sheet_name)}.png", dpi=300, bbox_inches="tight")
    plt.close(fig)
