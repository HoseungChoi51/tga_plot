from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

DATA_FILE = Path("/home/chs/Work/tga_plot/tests/inputs/TGA.xlsx")
OUT_DIR = Path("/home/chs/Work/tga_plot/eval/results/runs/luna/R-mpl-brief/15_r3/out")

plt.rcParams["font.family"] = "Noto Sans CJK KR"
plt.rcParams["axes.unicode_minus"] = False

OUT_DIR.mkdir(parents=True, exist_ok=True)

sheets = pd.read_excel(DATA_FILE, sheet_name=None)
fig, ax1 = plt.subplots(figsize=(10, 6))
ax2 = ax1.twinx()

colors = plt.get_cmap("tab10").colors
for i, (sheet_name, df) in enumerate(sheets.items()):
    df = df.copy()
    df.columns = [str(c).strip() for c in df.columns]

    def find_column(tokens):
        for col in df.columns:
            name = col.lower().replace(" ", "")
            if any(token in name for token in tokens):
                return col
        return None

    x_col = find_column(["temperature", "temp"])
    weight_col = find_column(["weight"])
    dtg_col = find_column(["d.w", "dtg", "derivative"])

    if x_col is None or weight_col is None or dtg_col is None:
        numeric = df.select_dtypes(include="number").columns.tolist()
        if len(numeric) < 3:
            continue
        x_col, weight_col, dtg_col = numeric[:3]

    x = pd.to_numeric(df[x_col], errors="coerce")
    weight = pd.to_numeric(df[weight_col], errors="coerce")
    dtg = pd.to_numeric(df[dtg_col], errors="coerce")
    valid = x.notna() & weight.notna() & dtg.notna()
    x, weight, dtg = x[valid], weight[valid], dtg[valid]
    if x.empty:
        continue

    color = colors[i % len(colors)]
    ax1.plot(x, weight, color=color, linewidth=1.7, label=f"{sheet_name} Weight")
    ax2.plot(x, -dtg, color=color, linewidth=1.2, linestyle="--",
             alpha=0.75, label=f"{sheet_name} DTG")

    residue_idx = (x - 800).abs().idxmin()
    ax1.scatter(x.loc[residue_idx], weight.loc[residue_idx], color=color,
                edgecolor="white", linewidth=0.7, s=35, zorder=5)
    ax1.annotate(
        f"{sheet_name}: Residue {weight.loc[residue_idx]:.1f}%",
        (x.loc[residue_idx], weight.loc[residue_idx]),
        xytext=(5, 5), textcoords="offset points", fontsize=8, color=color,
    )

    peak_mask = x > 150
    if peak_mask.any():
        peak_idx = (-dtg[peak_mask]).idxmax()
        ax2.scatter(x.loc[peak_idx], -dtg.loc[peak_idx], color=color,
                    edgecolor="white", linewidth=0.7, s=35, zorder=5)
        ax2.annotate(
            f"{sheet_name}: {x.loc[peak_idx]:.0f} °C",
            (x.loc[peak_idx], -dtg.loc[peak_idx]),
            xytext=(5, -12), textcoords="offset points", fontsize=8, color=color,
        )

ax1.set_title("TGA — 모든 시트 겹쳐 그리기")
ax1.set_xlabel("Temperature (°C)")
ax1.set_ylabel("Weight (%)", color="#1f4e9c")
ax2.set_ylabel("-DTG (%/°C)", color="#c0392b")
ax1.tick_params(axis="y", labelcolor="#1f4e9c")
ax2.tick_params(axis="y", labelcolor="#c0392b")
ax1.grid(True, alpha=0.25)

handles1, labels1 = ax1.get_legend_handles_labels()
handles2, labels2 = ax2.get_legend_handles_labels()
ax1.legend(handles1 + handles2, labels1 + labels2, loc="center left",
           bbox_to_anchor=(1.08, 0.5), fontsize=8, frameon=True)

fig.tight_layout()
fig.savefig(OUT_DIR / "TGA_all_sheets_overlay.png", dpi=300, bbox_inches="tight")
plt.close(fig)
