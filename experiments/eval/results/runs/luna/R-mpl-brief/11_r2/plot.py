from pathlib import Path
import re

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

DATA_FILE = Path("/home/chs/Work/tga_plot/tests/inputs/TGA.xlsx")
OUT_DIR = Path("/home/chs/Work/tga_plot/eval/results/runs/luna/R-mpl-brief/11_r2/out")

plt.rcParams["font.family"] = "Noto Sans CJK KR"
plt.rcParams["axes.unicode_minus"] = False

OUT_DIR.mkdir(parents=True, exist_ok=True)


def find_column(columns, terms):
    """Find a column by matching any of the supplied terms (case-insensitive)."""
    lowered = [str(col).strip().lower() for col in columns]
    for term in terms:
        for index, col in enumerate(lowered):
            if term in col:
                return columns[index]
    return None


def safe_filename(name):
    name = re.sub(r'[\\/:*?"<>|]+', "_", str(name)).strip()
    return name or "sheet"


excel = pd.ExcelFile(DATA_FILE)

for sheet_name in excel.sheet_names:
    df = pd.read_excel(DATA_FILE, sheet_name=sheet_name)
    df.columns = [str(col).strip() for col in df.columns]

    x_col = find_column(df.columns, ["temperature", "temp"])
    weight_col = find_column(df.columns, ["weight", "mass"])
    dtg_col = find_column(df.columns, ["d.w", "dtg", "derivative"])

    if x_col is None or weight_col is None or dtg_col is None:
        # Fall back to the expected TGA column order: Temperature, Weight, DTG.
        if len(df.columns) < 4:
            continue
        x_col, weight_col, dtg_col = df.columns[1], df.columns[2], df.columns[3]

    x = pd.to_numeric(df[x_col], errors="coerce")
    weight = pd.to_numeric(df[weight_col], errors="coerce")
    dtg = pd.to_numeric(df[dtg_col], errors="coerce")
    valid = x.notna() & weight.notna() & dtg.notna()
    x, weight, dtg = x[valid], weight[valid], dtg[valid]

    if x.empty:
        continue

    fig, ax1 = plt.subplots(figsize=(10, 6))
    ax2 = ax1.twinx()

    ax1.plot(x, weight, color="#1f4e9c", linewidth=1.8, label="Weight (%)")
    ax2.plot(x, -dtg, color="#c0392b", linewidth=1.5, label="DTG")

    ax1.set_title(sheet_name)
    ax1.set_xlabel("Temperature (°C)")
    ax1.set_ylabel("Weight (%)", color="#1f4e9c")
    ax2.set_ylabel("-DTG (%/°C)", color="#c0392b")
    ax1.tick_params(axis="y", labelcolor="#1f4e9c")
    ax2.tick_params(axis="y", labelcolor="#c0392b")
    ax1.grid(True, alpha=0.25)

    # 잔류량: 800 °C에 가장 가까운 측정점의 무게를 표시합니다.
    residue_idx = (x - 800).abs().idxmin()
    residue_x = float(x.loc[residue_idx])
    residue_y = float(weight.loc[residue_idx])
    ax1.plot(residue_x, residue_y, marker="o", color="#1f4e9c", markersize=5)
    ax1.annotate(
        f"Residue {residue_y:.1f}%",
        xy=(residue_x, residue_y),
        xytext=(8, 10),
        textcoords="offset points",
        color="#1f4e9c",
        fontsize=9,
    )

    # 두 축의 선을 하나의 범례로 표시합니다.
    lines = ax1.get_lines()[:1] + ax2.get_lines()[:1]
    ax1.legend(lines, [line.get_label() for line in lines], loc="center left")

    fig.tight_layout()
    fig.savefig(OUT_DIR / f"{safe_filename(sheet_name)}.png", dpi=300, bbox_inches="tight")
    plt.close(fig)
