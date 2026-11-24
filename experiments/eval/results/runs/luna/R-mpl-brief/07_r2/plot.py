from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

DATA_FILE = Path("/home/chs/Work/tga_plot/tests/inputs/TGA.xlsx")
OUT_DIR = Path("/home/chs/Work/tga_plot/eval/results/runs/luna/R-mpl-brief/07_r2/out")
OUT_DIR.mkdir(parents=True, exist_ok=True)

plt.rcParams["font.family"] = "Noto Sans CJK KR"
plt.rcParams["axes.unicode_minus"] = False

sheets = pd.read_excel(DATA_FILE, sheet_name=None)

for sheet_name, df in sheets.items():
    df.columns = [str(c).strip() for c in df.columns]

    def find_column(keywords):
        for col in df.columns:
            if any(word in col.lower() for word in keywords):
                return col
        return None

    temp_col = find_column(["temperature", "temp", "온도"])
    weight_col = find_column(["weight", "mass", "중량", "무게"])
    dtg_col = find_column(["d.w", "dtg", "derivative", "미분"])

    if temp_col is None or weight_col is None or dtg_col is None:
        if len(df.columns) < 4:
            continue
        temp_col, weight_col, dtg_col = df.columns[1], df.columns[2], df.columns[3]

    data = df[[temp_col, weight_col, dtg_col]].apply(pd.to_numeric, errors="coerce").dropna()
    if data.empty:
        continue

    temperature = data[temp_col].to_numpy()
    weight = data[weight_col].to_numpy()
    dtg = data[dtg_col].to_numpy()

    fig, ax1 = plt.subplots(figsize=(9, 6))
    ax2 = ax1.twinx()

    ax1.plot(temperature, weight, color="#1f4e9c", label="Weight (%)")
    ax2.plot(temperature, -dtg, color="#c0392b", label="DTG")

    ax1.set_title(sheet_name)
    ax1.set_xlabel("Temperature (°C)")
    ax1.set_ylabel("Weight (%)")
    ax2.set_ylabel("DTG (%/°C)")
    ax1.grid(True, alpha=0.3)

    # 잔류량: 800 °C에 가장 가까운 측정점
    residue_idx = int(np.argmin(np.abs(temperature - 800)))
    ax1.scatter(
        temperature[residue_idx], weight[residue_idx],
        color="#1f4e9c", edgecolor="white", zorder=5
    )
    ax1.annotate(
        f"Residue {weight[residue_idx]:.1f}%",
        (temperature[residue_idx], weight[residue_idx]),
        xytext=(8, 10), textcoords="offset points",
        color="#1f4e9c"
    )

    # 150 °C 초과 구간에서 가장 높은 -DTG 피크
    eligible = np.flatnonzero(temperature > 150)
    if eligible.size:
        peak_idx = eligible[np.argmax(-dtg[eligible])]
        ax2.scatter(
            temperature[peak_idx], -dtg[peak_idx],
            color="#c0392b", edgecolor="white", zorder=5
        )
        ax2.annotate(
            f"{temperature[peak_idx]:.0f} °C",
            (temperature[peak_idx], -dtg[peak_idx]),
            xytext=(8, 10), textcoords="offset points",
            color="#c0392b"
        )

    lines1, labels1 = ax1.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    ax1.legend(lines1 + lines2, labels1 + labels2, loc="upper right", fontsize=9)

    fig.tight_layout()
    safe_name = "".join(c if c.isalnum() or c in "-_ ." else "_" for c in sheet_name).strip()
    fig.savefig(OUT_DIR / f"{safe_name or 'sheet'}.png", dpi=300, bbox_inches="tight")
    plt.close(fig)
