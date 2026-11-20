from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

DATA_FILE = Path("/home/chs/Work/tga_plot/tests/inputs/TGA.xlsx")
OUT_DIR = Path("/home/chs/Work/tga_plot/eval/results/runs/luna/R-mpl-brief/05_r3/out")
OUT_DIR.mkdir(parents=True, exist_ok=True)

plt.rcParams["font.family"] = "Noto Sans CJK KR"
plt.rcParams["axes.unicode_minus"] = False

sheets = pd.read_excel(DATA_FILE, sheet_name=None)

for sheet_name, df in sheets.items():
    # Identify TGA columns by their names.
    normalized = {str(col).strip().lower(): col for col in df.columns}

    def find_column(keywords):
        for col in df.columns:
            name = str(col).strip().lower()
            if any(keyword in name for keyword in keywords):
                return col
        return None

    x_col = find_column(["temperature", "temp"])
    weight_col = find_column(["weight", "mass"])
    dtg_col = find_column(["d.w", "dtg", "derivative"])

    if x_col is None or weight_col is None or dtg_col is None:
        raise ValueError(f"시트 '{sheet_name}'에서 온도, 무게, DTG 열을 찾을 수 없습니다.")

    x = pd.to_numeric(df[x_col], errors="coerce").to_numpy()
    weight = pd.to_numeric(df[weight_col], errors="coerce").to_numpy()
    dtg = pd.to_numeric(df[dtg_col], errors="coerce").to_numpy()

    valid = np.isfinite(x) & np.isfinite(weight) & np.isfinite(dtg)
    x, weight, dtg = x[valid], weight[valid], dtg[valid]
    if len(x) == 0:
        continue

    fig, ax1 = plt.subplots(figsize=(9, 6))
    ax2 = ax1.twinx()

    line1, = ax1.plot(
        x, weight, color="black", linewidth=2.5, label="Weight (%)"
    )
    line2, = ax2.plot(
        x, -dtg, color="#c0392b", linestyle="--", linewidth=1.5, label="DTG"
    )

    # Residue: measured weight at the point nearest 800 °C.
    residue_idx = int(np.argmin(np.abs(x - 800)))
    ax1.plot(x[residue_idx], weight[residue_idx], "o", color="black", markersize=5)
    ax1.annotate(
        f"Residue {weight[residue_idx]:.1f}%",
        (x[residue_idx], weight[residue_idx]),
        xytext=(8, 8),
        textcoords="offset points",
        color="black",
    )

    # Peak: highest upward-pointing DTG peak above 150 °C.
    above_150 = np.flatnonzero(x > 150)
    if len(above_150):
        peak_idx = int(above_150[np.argmax((-dtg)[above_150])])
        ax2.plot(x[peak_idx], -dtg[peak_idx], "o", color="#c0392b", markersize=5)
        ax2.annotate(
            f"{x[peak_idx]:.0f} °C",
            (x[peak_idx], -dtg[peak_idx]),
            xytext=(8, 8),
            textcoords="offset points",
            color="#c0392b",
        )

    ax1.set_title(str(sheet_name))
    ax1.set_xlabel("Temperature (°C)")
    ax1.set_ylabel("Weight (%)")
    ax2.set_ylabel("DTG (-%/°C)")
    ax1.legend([line1, line2], [line1.get_label(), line2.get_label()], loc="center left")
    ax1.grid(True, alpha=0.3)

    fig.tight_layout()
    safe_name = "".join(ch if ch not in '<>:"/\\|?*' else "_" for ch in str(sheet_name))
    fig.savefig(OUT_DIR / f"{safe_name}.png", dpi=300, bbox_inches="tight")
    plt.close(fig)
