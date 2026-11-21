from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

DATA_FILE = Path("/home/chs/Work/tga_plot/tests/inputs/TGA.xlsx")
OUT_DIR = Path("/home/chs/Work/tga_plot/eval/results/runs/luna/R-mpl-brief/08_r1/out")

plt.rcParams["font.family"] = "Noto Sans CJK KR"
plt.rcParams["axes.unicode_minus"] = False

OUT_DIR.mkdir(parents=True, exist_ok=True)

sheets = pd.read_excel(DATA_FILE, sheet_name=None)

for sheet_name, df in sheets.items():
    df.columns = [str(col).strip() for col in df.columns]

    def find_column(key):
        matches = [col for col in df.columns if key.lower() in col.lower()]
        if not matches:
            raise ValueError(f"'{sheet_name}' 시트에서 '{key}' 열을 찾을 수 없습니다.")
        return matches[0]

    x_col = find_column("temperature")
    weight_col = find_column("weight")
    dtg_col = next(
        (col for col in df.columns if "d.w" in col.lower() or "dtg" in col.lower()),
        None,
    )
    if dtg_col is None:
        raise ValueError(f"'{sheet_name}' 시트에서 DTG 열을 찾을 수 없습니다.")

    x = pd.to_numeric(df[x_col], errors="coerce").to_numpy()
    weight = pd.to_numeric(df[weight_col], errors="coerce").to_numpy()
    dtg = pd.to_numeric(df[dtg_col], errors="coerce").to_numpy()

    valid = np.isfinite(x) & np.isfinite(weight) & np.isfinite(dtg)
    x, weight, dtg = x[valid], weight[valid], dtg[valid]
    if not len(x):
        continue

    fig, ax1 = plt.subplots(figsize=(9, 6))
    ax2 = ax1.twinx()

    weight_line, = ax1.plot(x, weight, color="#1f4e9c", label="Weight")
    dtg_line, = ax2.plot(x, -dtg, color="#c0392b", label="DTG")

    ax1.set_xlabel("온도 (°C)")
    ax1.set_ylabel("무게 (%)", color="#1f4e9c")
    ax2.set_ylabel("미분 무게 (%/°C)", color="#c0392b")
    ax1.tick_params(axis="y", labelcolor="#1f4e9c")
    ax2.tick_params(axis="y", labelcolor="#c0392b")
    ax1.set_title(sheet_name)

    residue_idx = int(np.argmin(np.abs(x - 800)))
    ax1.scatter(x[residue_idx], weight[residue_idx], color="#1f4e9c", zorder=5)
    ax1.annotate(
        f"Residue {weight[residue_idx]:.1f}%",
        (x[residue_idx], weight[residue_idx]),
        xytext=(8, 8),
        textcoords="offset points",
        color="#1f4e9c",
    )

    peak_candidates = np.flatnonzero(x > 150)
    if len(peak_candidates):
        peak_idx = peak_candidates[np.argmax((-dtg)[peak_candidates])]
        ax2.scatter(x[peak_idx], -dtg[peak_idx], color="#c0392b", zorder=5)
        ax2.annotate(
            f"{x[peak_idx]:.0f} °C",
            (x[peak_idx], -dtg[peak_idx]),
            xytext=(8, 8),
            textcoords="offset points",
            color="#c0392b",
        )

    ax1.legend([weight_line, dtg_line], ["Weight", "DTG"], loc="center left")
    ax1.grid(True, alpha=0.3)
    fig.tight_layout()

    safe_name = "".join(c if c.isalnum() or c in "-_ ." else "_" for c in sheet_name).strip()
    fig.savefig(OUT_DIR / f"{safe_name}.png", dpi=300, bbox_inches="tight")
    plt.close(fig)
