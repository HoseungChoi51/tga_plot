from pathlib import Path

import pandas as pd
import matplotlib.pyplot as plt

DATA_FILE = Path("/home/chs/Work/tga_plot/tests/inputs/TGA.xlsx")
OUT_DIR = Path("/home/chs/Work/tga_plot/eval/results/runs/luna/R-mpl-brief/07_r3/out")

plt.rcParams["font.family"] = "Noto Sans CJK KR"
plt.rcParams["axes.unicode_minus"] = False

OUT_DIR.mkdir(parents=True, exist_ok=True)
sheets = pd.read_excel(DATA_FILE, sheet_name=None)

for sheet_name, df in sheets.items():
    df = df.apply(pd.to_numeric, errors="coerce")
    df = df.dropna(subset=["Temperature", "Weight(%)", "D.W(%/C)"])

    temperature = df["Temperature"]
    weight = df["Weight(%)"]
    dtg_up = -df["D.W(%/C)"]

    fig, ax1 = plt.subplots(figsize=(8, 5))
    ax2 = ax1.twinx()

    line1, = ax1.plot(
        temperature, weight, color="#1f4e9c", label="Weight (%)"
    )
    line2, = ax2.plot(
        temperature, dtg_up, color="#c0392b", label="DTG (%/°C)"
    )

    residue_idx = (temperature - 800).abs().idxmin()
    residue_temp = temperature.loc[residue_idx]
    residue_weight = weight.loc[residue_idx]
    ax1.plot(residue_temp, residue_weight, "o", color="#1f4e9c")
    ax1.annotate(
        f"Residue {residue_weight:.1f}%",
        (residue_temp, residue_weight),
        xytext=(7, 8),
        textcoords="offset points",
        color="#1f4e9c",
    )

    peak_candidates = df.loc[temperature > 150]
    if not peak_candidates.empty:
        peak_idx = (-peak_candidates["D.W(%/C)"]).idxmax()
        peak_temp = temperature.loc[peak_idx]
        peak_value = dtg_up.loc[peak_idx]
        ax2.plot(peak_temp, peak_value, "o", color="#c0392b")
        ax2.annotate(
            f"{peak_temp:.0f} °C",
            (peak_temp, peak_value),
            xytext=(7, 8),
            textcoords="offset points",
            color="#c0392b",
        )

    ax1.set_title(sheet_name)
    ax1.set_xlabel("Temperature (°C)")
    ax1.set_ylabel("Weight (%)", color="#1f4e9c")
    ax2.set_ylabel("DTG (%/°C)", color="#c0392b")
    ax1.tick_params(axis="y", labelcolor="#1f4e9c")
    ax2.tick_params(axis="y", labelcolor="#c0392b")

    ax1.legend(
        [line1, line2],
        [line1.get_label(), line2.get_label()],
        loc="upper right",
        fontsize=9,
    )

    fig.tight_layout()
    safe_name = "".join(
        char if char.isalnum() or char in "-_ " else "_" for char in sheet_name
    ).strip()
    fig.savefig(OUT_DIR / f"{safe_name}.png", dpi=300, bbox_inches="tight")
    plt.close(fig)
