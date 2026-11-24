from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

DATA_FILE = "/home/chs/Work/tga_plot/tests/inputs/blank_rows_on_top.xlsx"
OUT_DIR = "/home/chs/Work/tga_plot/eval/results/runs/luna/R-mpl-brief/21_r3/out"

# 한글 폰트 설정
plt.rcParams["font.family"] = "Noto Sans CJK KR"
plt.rcParams["axes.unicode_minus"] = False

out_dir = Path(OUT_DIR)
out_dir.mkdir(parents=True, exist_ok=True)

# 헤더가 8행에 있으므로(엑셀 기준), 앞의 빈 행을 건너뜁니다.
df = pd.read_excel(DATA_FILE, sheet_name="Sheet1", header=7)

# 요청한 엑셀 열: C=X, D=Y1, E=Y2
x = pd.to_numeric(df.iloc[:, 2], errors="coerce")
y1 = pd.to_numeric(df.iloc[:, 3], errors="coerce")
y2 = pd.to_numeric(df.iloc[:, 4], errors="coerce")

valid = x.notna() & y1.notna() & y2.notna()
x = x[valid].to_numpy()
y1 = y1[valid].to_numpy()
y2 = y2[valid].to_numpy()

fig, ax1 = plt.subplots(figsize=(9, 6))
ax1.plot(x, y1, color="#1f4e9c", label=str(df.columns[3]))
ax1.set_xlabel(str(df.columns[2]))
ax1.set_ylabel(str(df.columns[3]), color="#1f4e9c")
ax1.tick_params(axis="y", labelcolor="#1f4e9c")
ax1.grid(True, alpha=0.3)

ax2 = ax1.twinx()
# TGA의 DTG는 질량 감소 시 음수이므로 위쪽 피크가 되도록 부호를 반전합니다.
ax2.plot(x, -y2, color="#c0392b", label=f"-{df.columns[4]}")
ax2.set_ylabel(f"-{df.columns[4]}", color="#c0392b")
ax2.tick_params(axis="y", labelcolor="#c0392b")

# 잔류량: 800 °C에 가장 가까운 측정점
residue_idx = int(np.argmin(np.abs(x - 800)))
ax1.plot(x[residue_idx], y1[residue_idx], "o", color="#1f4e9c")
ax1.annotate(
    f"Residue {y1[residue_idx]:.1f}%",
    (x[residue_idx], y1[residue_idx]),
    xytext=(8, 10),
    textcoords="offset points",
    color="#1f4e9c",
)

# 피크: 150 °C 초과 구간에서 부호 반전한 DTG의 최대값
peak_candidates = np.flatnonzero(x > 150)
if peak_candidates.size:
    peak_idx = peak_candidates[np.argmax(-y2[peak_candidates])]
    ax2.plot(x[peak_idx], -y2[peak_idx], "o", color="#c0392b")
    ax2.annotate(
        f"{x[peak_idx]:.0f} °C",
        (x[peak_idx], -y2[peak_idx]),
        xytext=(8, 10),
        textcoords="offset points",
        color="#c0392b",
    )

lines1, labels1 = ax1.get_legend_handles_labels()
lines2, labels2 = ax2.get_legend_handles_labels()
ax1.legend(lines1 + lines2, labels1 + labels2, loc="center left")

ax1.set_title("Sheet1")
fig.tight_layout()
fig.savefig(out_dir / "Sheet1.png", dpi=300, bbox_inches="tight")
plt.close(fig)
