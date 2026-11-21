from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

DATA_FILE = Path("/home/chs/Work/tga_plot/tests/inputs/korean_excel.csv")
OUT_DIR = Path("/home/chs/Work/tga_plot/eval/results/runs/luna/R-mpl-plain/14_r2/out")

# Read the CSV, trying common encodings in case it was saved from Excel.
for encoding in ("utf-8-sig", "cp949", "euc-kr"):
    try:
        data = pd.read_csv(DATA_FILE, encoding=encoding)
        break
    except UnicodeDecodeError:
        continue
else:
    raise UnicodeError(f"Could not decode {DATA_FILE}")

data.columns = data.columns.astype(str).str.strip()
required = ["온도(°C)", "무게(%)", "미분무게(%/°C)"]
missing = [column for column in required if column not in data.columns]
if missing:
    raise ValueError(f"Missing required column(s): {missing}. Found: {list(data.columns)}")

for column in required:
    data[column] = pd.to_numeric(data[column], errors="coerce")
data = data.dropna(subset=required).sort_values("온도(°C)")

OUT_DIR.mkdir(parents=True, exist_ok=True)
plt.rcParams["font.family"] = "Noto Sans CJK KR"
plt.rcParams["axes.unicode_minus"] = False

fig, ax_mass = plt.subplots(figsize=(9, 6))
ax_dtg = ax_mass.twinx()

mass_line, = ax_mass.plot(
    data["온도(°C)"],
    data["무게(%)"],
    color="tab:blue",
    linewidth=1.8,
    label="무게",
)
dtg_line, = ax_dtg.plot(
    data["온도(°C)"],
    data["미분무게(%/°C)"],
    color="tab:red",
    linewidth=1.5,
    label="미분무게",
)

ax_mass.set_xlabel("온도 (°C)")
ax_mass.set_ylabel("무게 (%)", color="tab:blue")
ax_dtg.set_ylabel("미분무게 (%/°C)", color="tab:red")
ax_mass.tick_params(axis="y", labelcolor="tab:blue")
ax_dtg.tick_params(axis="y", labelcolor="tab:red")
ax_mass.set_title("열중량 분석 (TGA)")
ax_mass.grid(True, linestyle="--", alpha=0.35)
ax_mass.legend([mass_line, dtg_line], ["무게", "미분무게"], loc="best")
fig.tight_layout()

fig.savefig(OUT_DIR / "korean_excel.png", dpi=300, bbox_inches="tight")
fig.savefig(OUT_DIR / "korean_excel.pdf", bbox_inches="tight")
plt.close(fig)
