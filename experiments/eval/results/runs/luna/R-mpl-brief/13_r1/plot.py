from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

DATA_FILE = Path("/home/chs/Work/tga_plot/tests/inputs/extra_columns.xlsx")
OUT_DIR = Path("/home/chs/Work/tga_plot/eval/results/runs/luna/R-mpl-brief/13_r1/out")
OUT_DIR.mkdir(parents=True, exist_ok=True)

plt.rcParams["font.family"] = "Noto Sans CJK KR"
plt.rcParams["axes.unicode_minus"] = False

excel = pd.ExcelFile(DATA_FILE)

for sheet_name in excel.sheet_names:
    df = pd.read_excel(DATA_FILE, sheet_name=sheet_name)
    df.columns = [str(c).strip() for c in df.columns]

    x_col = next((c for c in df.columns if "Temperature" in c), None)
    weight_col = next((c for c in df.columns if "Weight (mg)" in c), None)
    dtg_col = next((c for c in df.columns if "Deriv. Weight" in c), None)

    if not all((x_col, weight_col, dtg_col)):
        continue

    data = df[[x_col, weight_col, dtg_col]].apply(pd.to_numeric, errors="coerce").dropna()
    if data.empty:
        continue

    x = data[x_col].to_numpy()
    weight = data[weight_col].to_numpy()
    dtg_up = -data[dtg_col].to_numpy()

    fig, ax1 = plt.subplots(figsize=(8, 5))
    ax1.plot(x, weight, color="#1f4e9c", label="Weight (mg)")
    ax1.set_xlabel("Temperature (°C)")
    ax1.set_ylabel("Weight (mg)", color="#1f4e9c")
    ax1.tick_params(axis="y", labelcolor="#1f4e9c")
    ax1.set_title(sheet_name)

    ax2 = ax1.twinx()
    ax2.plot(x, dtg_up, color="#c0392b", label="DTG")
    ax2.set_ylabel("DTG (%/°C)", color="#c0392b")
    ax2.tick_params(axis="y", labelcolor="#c0392b")

    residue_idx = int(np.argmin(np.abs(x - 800)))
    ax1.plot(x[residue_idx], weight[residue_idx], "o", color="#1f4e9c")
    ax1.annotate(
        f"Residue {weight[residue_idx]:.1f}%",
        (x[residue_idx], weight[residue_idx]),
        xytext=(8, 8),
        textcoords="offset points",
        color="#1f4e9c",
    )

    peak_candidates = np.flatnonzero(x > 150)
    if len(peak_candidates):
        peak_idx = peak_candidates[np.argmax(dtg_up[peak_candidates])]
        ax2.plot(x[peak_idx], dtg_up[peak_idx], "o", color="#c0392b")
        ax2.annotate(
            f"{x[peak_idx]:.0f} °C",
            (x[peak_idx], dtg_up[peak_idx]),
            xytext=(8, 8),
            textcoords="offset points",
            color="#c0392b",
        )

    handles1, labels1 = ax1.get_legend_handles_labels()
    handles2, labels2 = ax2.get_legend_handles_labels()
    ax1.legend(handles1 + handles2, labels1 + labels2, loc="center left")
    ax1.grid(True, alpha=0.3)
    fig.tight_layout()

    output_path = OUT_DIR / f"{sheet_name}.png"
    fig.savefig(output_path, dpi=300, bbox_inches="tight")
    plt.close(fig)
