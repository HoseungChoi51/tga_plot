from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

DATA_FILE = Path("/home/chs/Work/tga_plot/tests/inputs/korean_excel.csv")
OUT_DIR = Path("/home/chs/Work/tga_plot/eval/results/runs/luna/R-mpl-plain/14_r3/out")

plt.rcParams["font.family"] = "Noto Sans CJK KR"
plt.rcParams["axes.unicode_minus"] = False

# CSV 파일을 읽고 열 이름의 공백을 정리합니다.
try:
    data = pd.read_csv(DATA_FILE, encoding="utf-8-sig")
except UnicodeDecodeError:
    data = pd.read_csv(DATA_FILE, encoding="cp949")

data.columns = data.columns.astype(str).str.strip()

x_col = "온도(°C)"
weight_col = "무게(%)"
derivative_col = "미분무게(%/°C)"

# 필요한 열을 숫자로 변환하고 결측 행을 제외합니다.
for col in (x_col, weight_col, derivative_col):
    data[col] = pd.to_numeric(data[col], errors="coerce")
data = data.dropna(subset=[x_col, weight_col, derivative_col]).sort_values(x_col)

OUT_DIR.mkdir(parents=True, exist_ok=True)

fig, ax1 = plt.subplots(figsize=(9, 6))
ax1.plot(data[x_col], data[weight_col], color="tab:blue", linewidth=1.8, label="무게")
ax1.set_xlabel("온도 (°C)")
ax1.set_ylabel("무게 (%)", color="tab:blue")
ax1.tick_params(axis="y", labelcolor="tab:blue")
ax1.grid(True, linestyle="--", alpha=0.35)

ax2 = ax1.twinx()
ax2.plot(
    data[x_col],
    data[derivative_col],
    color="tab:red",
    linewidth=1.5,
    label="미분무게",
)
ax2.set_ylabel("미분무게 (%/°C)", color="tab:red")
ax2.tick_params(axis="y", labelcolor="tab:red")

lines = ax1.get_lines() + ax2.get_lines()
ax1.legend(lines, [line.get_label() for line in lines], loc="best")
ax1.set_title("열중량 분석 (TGA)")

fig.tight_layout()
fig.savefig(OUT_DIR / "korean_excel.png", dpi=300, bbox_inches="tight")
fig.savefig(OUT_DIR / "korean_excel.pdf", bbox_inches="tight")
plt.close(fig)
