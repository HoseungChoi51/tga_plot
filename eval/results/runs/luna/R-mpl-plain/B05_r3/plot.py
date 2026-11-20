from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd


DATA_FILES = [
    "/home/chs/Work/tga_plot/eval/inputs_b/cnt_lot_A.csv",
    "/home/chs/Work/tga_plot/eval/inputs_b/cnt_lot_B.txt",
]
OUT_DIR = "/home/chs/Work/tga_plot/eval/results/runs/luna/R-mpl-plain/B05_r3/out"

plt.rcParams["font.family"] = "Noto Sans CJK KR"
plt.rcParams["axes.unicode_minus"] = False


def read_data(path):
    path = Path(path)
    if path.suffix.lower() == ".csv":
        return pd.read_csv(path)

    # Try typical text-file delimiters, retaining the parse with the most columns.
    best = None
    for separator in ("\t", ",", r"\s+"):
        try:
            candidate = pd.read_csv(path, sep=separator, engine="python")
            if best is None or candidate.shape[1] > best.shape[1]:
                best = candidate
            if candidate.shape[1] >= 4:
                return candidate
        except Exception:
            continue
    if best is None:
        raise ValueError(f"Could not read data file: {path}")
    return best


def find_column(df, terms, fallback_index):
    normalized = {column: str(column).strip().lower() for column in df.columns}
    for column, name in normalized.items():
        if all(term in name for term in terms):
            return column
    if df.shape[1] > fallback_index:
        return df.columns[fallback_index]
    raise ValueError(f"Required data column not found: {terms}")


fig, ax = plt.subplots(figsize=(8, 5.5), constrained_layout=True)

for path, label in zip(DATA_FILES, ("Lot A", "Lot B")):
    data = read_data(path)
    data.columns = [str(column).strip() for column in data.columns]

    temperature_col = find_column(data, ("temperature",), 1)
    weight_col = find_column(data, ("weight",), 2)

    temperature = pd.to_numeric(data[temperature_col], errors="coerce")
    weight = pd.to_numeric(data[weight_col], errors="coerce")
    valid = temperature.notna() & weight.notna()

    ax.plot(temperature[valid], weight[valid], linewidth=1.8, label=label)

ax.set_xlabel("Temperature (°C)")
ax.set_ylabel("Weight (%)")
ax.set_title("TGA Comparison")
ax.grid(True, alpha=0.3)
ax.legend()

out_dir = Path(OUT_DIR)
out_dir.mkdir(parents=True, exist_ok=True)
fig.savefig(out_dir / "tga_lot_comparison.png", dpi=300, bbox_inches="tight")
plt.close(fig)
