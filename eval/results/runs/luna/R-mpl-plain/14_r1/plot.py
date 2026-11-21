from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

DATA_FILE = Path("/home/chs/Work/tga_plot/tests/inputs/korean_excel.csv")
OUT_DIR = Path("/home/chs/Work/tga_plot/eval/results/runs/luna/R-mpl-plain/14_r1/out")

plt.rcParams["font.family"] = "Noto Sans CJK KR"
plt.rcParams["axes.unicode_minus"] = False

OUT_DIR.mkdir(parents=True, exist_ok=True)

# Load the CSV and use the temperature, mass, and derivative-mass columns.
try:
    data = pd.read_csv(DATA_FILE, encoding="utf-8-sig")
except UnicodeDecodeError:
    data = pd.read_csv(DATA_FILE, encoding="cp949")

temperature = pd.to_numeric(data["온도(°C)"], errors="coerce")
mass = pd.to_numeric(data["무게(%)"], errors="coerce")
derivative = pd.to_numeric(data["미분무게(%/°C)"], errors="coerce")

valid = temperature.notna() & mass.notna() & derivative.notna()
temperature = temperature[valid]
mass = mass[valid]
derivative = derivative[valid]

fig, ax_mass = plt.subplots(figsize=(9, 6))
ax_derivative = ax_mass.twinx()

mass_line, = ax_mass.plot(
    temperature, mass, color="#1f77b4", linewidth=1.8, label="무게"
)
derivative_line, = ax_derivative.plot(
    temperature, derivative, color="#d62728", linewidth=1.5, label="미분무게"
)

ax_mass.set_xlabel("온도 (°C)")
ax_mass.set_ylabel("무게 (%)", color="#1f77b4")
ax_derivative.set_ylabel("미분무게 (%/°C)", color="#d62728")
ax_mass.tick_params(axis="y", labelcolor="#1f77b4")
ax_derivative.tick_params(axis="y", labelcolor="#d62728")
ax_mass.set_title("온도에 따른 무게 및 미분무게")
ax_mass.grid(True, linestyle="--", linewidth=0.6, alpha=0.5)
ax_mass.legend(
    [mass_line, derivative_line],
    [mass_line.get_label(), derivative_line.get_label()],
    loc="best",
)
fig.tight_layout()

fig.savefig(OUT_DIR / "korean_excel_tga.png", dpi=300, bbox_inches="tight")
fig.savefig(OUT_DIR / "korean_excel_tga.pdf", bbox_inches="tight")
plt.close(fig)
