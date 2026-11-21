from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

DATA_FILE = Path("/home/chs/Work/tga_plot/eval/inputs_b/caox.csv")
OUT_DIR = Path("/home/chs/Work/tga_plot/eval/results/runs/luna/R-mpl-brief/B02_r3/out")

# Heat Flow의 극값을 흡열/발열 피크로 해석할 때 장비 데이터의 부호 관례가
# 반대일 수 있으므로, 기본값은 양의 피크 2개를 흡열, 음의 피크 1개를 발열로 둡니다.
# 통상적인 반대 부호 관례의 데이터라면 이 값을 True로 바꾸세요.
INVERT_HEAT_FLOW_SIGN = False

plt.rcParams["font.family"] = "Noto Sans CJK KR"
plt.rcParams["axes.unicode_minus"] = False

OUT_DIR.mkdir(parents=True, exist_ok=True)

data = pd.read_csv(DATA_FILE)
data.columns = [str(c).strip() for c in data.columns]

def find_column(columns, candidates):
    lowered = {c.lower(): c for c in columns}
    for candidate in candidates:
        for key, original in lowered.items():
            if candidate in key:
                return original
    raise ValueError(f"필요한 열을 찾지 못했습니다: {candidates}")

temperature_col = find_column(data.columns, ["temperature", "temp"])
weight_col = find_column(data.columns, ["weight"])
heat_flow_col = find_column(data.columns, ["heat flow", "heatflow"])

temperature = pd.to_numeric(data[temperature_col], errors="coerce")
weight = pd.to_numeric(data[weight_col], errors="coerce")
heat_flow = pd.to_numeric(data[heat_flow_col], errors="coerce")

valid = temperature.notna() & weight.notna() & heat_flow.notna()
plot_data = pd.DataFrame({
    "temperature": temperature[valid],
    "weight": weight[valid],
    "heat_flow": heat_flow[valid],
}).sort_values("temperature")

if INVERT_HEAT_FLOW_SIGN:
    plot_data["heat_flow"] = -plot_data["heat_flow"]

x = plot_data["temperature"].to_numpy()
w = plot_data["weight"].to_numpy()
hf = plot_data["heat_flow"].to_numpy()

fig, ax1 = plt.subplots(figsize=(9, 6))
ax2 = ax1.twinx()

weight_line, = ax1.plot(x, w, color="#1f4e9c", linewidth=1.8, label="Weight (%)")
heat_line, = ax2.plot(x, hf, color="#c0392b", linewidth=1.5, label="Heat Flow (W/g)")

ax1.set_xlabel("Temperature (°C)")
ax1.set_ylabel("Weight (%)", color="#1f4e9c")
ax2.set_ylabel("Heat Flow (W/g)", color="#c0392b")
ax1.tick_params(axis="y", labelcolor="#1f4e9c")
ax2.tick_params(axis="y", labelcolor="#c0392b")
ax1.grid(True, linestyle="--", alpha=0.35)

# 요청한 피크 온도를 표시하기 위해 Heat Flow를 평활화한 뒤 국소 극값을 찾습니다.
# 두드러진 양의 피크 2개와 음의 피크 1개를 선택합니다.
smooth_window = max(5, int(round(len(hf) * 0.01)))
if smooth_window % 2 == 0:
    smooth_window += 1
if smooth_window >= len(hf):
    smooth_window = max(3, len(hf) // 2 * 2 - 1)
smoothed_hf = (
    pd.Series(hf)
    .rolling(window=smooth_window, center=True, min_periods=1)
    .mean()
    .to_numpy()
)

try:
    from scipy.signal import find_peaks

    prominence = max(float(np.nanstd(smoothed_hf)) * 0.08, 1e-12)
    positive_candidates, _ = find_peaks(smoothed_hf, prominence=prominence)
    negative_candidates, _ = find_peaks(-smoothed_hf, prominence=prominence)
except Exception:
    positive_candidates = np.array([
        i for i in range(1, len(hf) - 1)
        if smoothed_hf[i] > smoothed_hf[i - 1]
        and smoothed_hf[i] >= smoothed_hf[i + 1]
    ])
    negative_candidates = np.array([
        i for i in range(1, len(hf) - 1)
        if smoothed_hf[i] < smoothed_hf[i - 1]
        and smoothed_hf[i] <= smoothed_hf[i + 1]
    ])

def select_extreme_peaks(candidates, values, count, largest=True):
    candidates = np.asarray(candidates, dtype=int)
    if candidates.size == 0:
        return []
    order = np.argsort(values[candidates])
    if largest:
        order = order[::-1]
    chosen = []
    for idx in candidates[order]:
        if all(abs(int(idx) - prev) >= max(3, smooth_window // 2) for prev in chosen):
            chosen.append(int(idx))
        if len(chosen) == count:
            break
    return chosen

endothermic_peaks = select_extreme_peaks(
    positive_candidates, smoothed_hf, 2, largest=True
)
exothermic_peaks = select_extreme_peaks(
    negative_candidates, smoothed_hf, 1, largest=False
)

# 검출된 국소 피크가 부족한 경우에도 표시할 수 있도록 전역 극값으로 보충합니다.
for idx in np.argsort(smoothed_hf)[::-1]:
    idx = int(idx)
    if len(endothermic_peaks) >= 2:
        break
    if all(abs(idx - prev) >= max(3, smooth_window // 2) for prev in endothermic_peaks):
        endothermic_peaks.append(idx)

for idx in np.argsort(smoothed_hf):
    idx = int(idx)
    if exothermic_peaks:
        break
    exothermic_peaks.append(idx)

for idx in endothermic_peaks[:2]:
    ax2.scatter(x[idx], hf[idx], color="#c0392b", marker="^", s=55, zorder=5)
    ax2.annotate(
        f"흡열 {x[idx]:.0f} °C",
        (x[idx], hf[idx]),
        xytext=(7, 10),
        textcoords="offset points",
        color="#922b21",
        fontsize=9,
        ha="left",
    )

for idx in exothermic_peaks[:1]:
    ax2.scatter(x[idx], hf[idx], color="#1f77b4", marker="v", s=55, zorder=5)
    ax2.annotate(
        f"발열 {x[idx]:.0f} °C",
        (x[idx], hf[idx]),
        xytext=(7, -16),
        textcoords="offset points",
        color="#1f4e79",
        fontsize=9,
        ha="left",
    )

# 기본 TGA 잔류량 표시: 측정 데이터 중 800 °C에 가장 가까운 지점
residue_idx = int(np.nanargmin(np.abs(x - 800)))
ax1.scatter(
    x[residue_idx], w[residue_idx],
    color="#1f4e9c", edgecolor="white", linewidth=0.7, s=45, zorder=5
)
ax1.annotate(
    f"Residue {w[residue_idx]:.1f}%",
    (x[residue_idx], w[residue_idx]),
    xytext=(8, -18),
    textcoords="offset points",
    color="#1f4e9c",
    fontsize=9,
)

ax1.legend([weight_line, heat_line], ["Weight (%)", "Heat Flow (W/g)"], loc="center left")
ax1.set_title(DATA_FILE.stem)
fig.tight_layout()

output_file = OUT_DIR / f"{DATA_FILE.stem}_heat_flow.png"
fig.savefig(output_file, dpi=300, bbox_inches="tight")
plt.close(fig)
