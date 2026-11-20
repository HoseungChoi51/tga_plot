from pathlib import Path

import pandas as pd
import matplotlib.pyplot as plt

DATA_FILE = Path("/home/chs/Work/tga_plot/eval/inputs_b/rheology.csv")
OUT_DIR = Path("/home/chs/Work/tga_plot/eval/results/runs/luna/R-mpl-plain/B03_r1/out")

# Read the CSV and select the frequency, storage-modulus, and loss-modulus columns.
data = pd.read_csv(DATA_FILE)
frequency = pd.to_numeric(data["Angular frequency (rad/s)"], errors="coerce")
storage_modulus = pd.to_numeric(data["Storage modulus G' (Pa)"], errors="coerce")
loss_modulus = pd.to_numeric(data["Loss modulus G'' (Pa)"], errors="coerce")

valid = (
    frequency.notna()
    & storage_modulus.notna()
    & loss_modulus.notna()
    & (frequency > 0)
    & (storage_modulus > 0)
    & (loss_modulus > 0)
)
frequency = frequency[valid]
storage_modulus = storage_modulus[valid]
loss_modulus = loss_modulus[valid]

plt.rcParams["font.family"] = "Noto Sans CJK KR"
plt.rcParams["axes.unicode_minus"] = False

fig, ax_left = plt.subplots(figsize=(8, 5))
ax_right = ax_left.twinx()

line_storage, = ax_left.plot(
    frequency, storage_modulus, marker="o", linewidth=2,
    color="tab:blue", label="G' (저장 탄성률)"
)
line_loss, = ax_right.plot(
    frequency, loss_modulus, marker="s", linewidth=2,
    color="tab:red", label="G'' (손실 탄성률)"
)

ax_left.set_xscale("log")
ax_left.set_yscale("log")
ax_right.set_yscale("log")

ax_left.set_xlabel("각주파수 (rad/s)")
ax_left.set_ylabel("저장 탄성률 G' (Pa)", color="tab:blue")
ax_right.set_ylabel("손실 탄성률 G'' (Pa)", color="tab:red")
ax_left.tick_params(axis="y", labelcolor="tab:blue")
ax_right.tick_params(axis="y", labelcolor="tab:red")
ax_left.grid(True, which="both", linestyle=":", alpha=0.5)

ax_left.legend(
    [line_storage, line_loss],
    [line_storage.get_label(), line_loss.get_label()],
    loc="best",
)
ax_left.set_title("주파수에 따른 저장 및 손실 탄성률")
fig.tight_layout()

OUT_DIR.mkdir(parents=True, exist_ok=True)
fig.savefig(OUT_DIR / "rheology_moduli_vs_frequency.png", dpi=300, bbox_inches="tight")
plt.close(fig)
