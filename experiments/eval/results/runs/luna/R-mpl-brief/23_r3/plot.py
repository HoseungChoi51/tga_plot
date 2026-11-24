from pathlib import Path
import re

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

DATA_FILE = Path("/home/chs/Work/tga_plot/tests/inputs/instrument_export.txt")
OUT_DIR = Path("/home/chs/Work/tga_plot/eval/results/runs/luna/R-mpl-brief/23_r3/out")
OUT_DIR.mkdir(parents=True, exist_ok=True)

plt.rcParams["font.family"] = "Noto Sans CJK KR"
plt.rcParams["axes.unicode_minus"] = False


def load_numeric_columns(path):
    """Extract numeric fields from instrument text, ignoring metadata/header rows."""
    raw = path.read_bytes()
    text = None
    for encoding in ("utf-8-sig", "utf-16", "cp949", "latin-1"):
        try:
            text = raw.decode(encoding)
            break
        except UnicodeDecodeError:
            continue
    if text is None:
        text = raw.decode("utf-8", errors="replace")

    rows = []
    for line in text.splitlines():
        # Split on common instrument-export delimiters.
        tokens = re.split(r"[\t,; ]+", line.strip())
        if len(tokens) < 4:
            continue

        numbers = []
        for token in tokens:
            token = token.strip().strip('"').strip("'")
            if not token:
                continue
            # Accept decimal/scientific notation and decimal commas.
            token = token.replace(",", ".") if re.fullmatch(
                r"[+-]?\d+,\d+(?:[eE][+-]?\d+)?", token
            ) else token
            try:
                numbers.append(float(token))
            except ValueError:
                continue

        if len(numbers) >= 4:
            rows.append(numbers[:4])

    if not rows:
        # Some exports contain unusual separators or formatting. Extract numeric
        # values from each line as a final fallback.
        number_pattern = re.compile(
            r"[-+]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][-+]?\d+)?"
        )
        for line in text.splitlines():
            values = [float(value) for value in number_pattern.findall(line)]
            if len(values) >= 4:
                rows.append(values[:4])

    if not rows:
        raise ValueError(f"Could not find numeric data rows in {path}")

    return np.asarray(rows, dtype=float)


data = load_numeric_columns(DATA_FILE)
temperature = data[:, 1]
weight = data[:, 2]
dtg = data[:, 3]

valid = np.isfinite(temperature) & np.isfinite(weight) & np.isfinite(dtg)
temperature, weight, dtg = temperature[valid], weight[valid], dtg[valid]
if temperature.size == 0:
    raise ValueError("No valid data points to plot.")

residue_idx = int(np.argmin(np.abs(temperature - 800)))
residue_temp = temperature[residue_idx]
residue_weight = weight[residue_idx]

above_150 = np.flatnonzero(temperature > 150)
if above_150.size:
    peak_idx = int(above_150[np.argmax(-dtg[above_150])])
else:
    peak_idx = int(np.argmax(-dtg))
peak_temp = temperature[peak_idx]

fig, ax1 = plt.subplots(figsize=(8, 5))
ax2 = ax1.twinx()

weight_line, = ax1.plot(
    temperature, weight, color="#1f4e9c", linewidth=1.8, label="Weight"
)
dtg_line, = ax2.plot(
    temperature, -dtg, color="#c0392b", linewidth=1.5, label="DTG"
)

ax1.scatter(
    residue_temp, residue_weight, color="#1f4e9c",
    edgecolor="white", linewidth=0.6, zorder=5
)
ax1.annotate(
    f"Residue: {residue_weight:.1f}%",
    xy=(residue_temp, residue_weight),
    xytext=(8, 10),
    textcoords="offset points",
    color="#1f4e9c",
    fontsize=9,
)

ax2.scatter(
    peak_temp, -dtg[peak_idx], color="#c0392b",
    edgecolor="white", linewidth=0.6, zorder=5
)
ax2.annotate(
    f"{peak_temp:.0f} °C",
    xy=(peak_temp, -dtg[peak_idx]),
    xytext=(8, 10),
    textcoords="offset points",
    color="#c0392b",
    fontsize=9,
)

ax1.set_title("instrument_export")
ax1.set_xlabel("Temperature (°C)")
ax1.set_ylabel("Weight (%)", color="#1f4e9c")
ax2.set_ylabel("DTG", color="#c0392b")
ax1.tick_params(axis="y", labelcolor="#1f4e9c")
ax2.tick_params(axis="y", labelcolor="#c0392b")
ax1.grid(True, alpha=0.25)
ax1.legend([weight_line, dtg_line], ["Weight", "DTG"], loc="center left")

fig.tight_layout()
fig.savefig(OUT_DIR / "instrument_export.png", dpi=300, bbox_inches="tight")
plt.close(fig)
