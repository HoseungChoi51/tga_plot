from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

DATA_FILES = [
    "/home/chs/Work/tga_plot/eval/inputs_b/cnt_lot_A.csv",
    "/home/chs/Work/tga_plot/eval/inputs_b/cnt_lot_B.txt",
]
OUT_DIR = "/home/chs/Work/tga_plot/eval/results/runs/luna/R-mpl-plain/B05_r2/out"

plt.rcParams["font.family"] = "Noto Sans CJK KR"
plt.rcParams["axes.unicode_minus"] = False


def read_data(path):
    """Read delimited files, handling comma-separated text even with a .txt suffix."""
    suffix = Path(path).suffix.lower()
    if suffix == ".csv":
        return pd.read_csv(path)

    # The provided text file may be semicolon-delimited despite its extension.
    for sep in (";", "\t", r"\s+", ","):
        try:
            df = pd.read_csv(path, sep=sep, engine="python")
            if df.shape[1] >= 4:
                return df
        except Exception:
            continue

    return pd.read_csv(path, sep=None, engine="python")


def load_tga(path):
    df = read_data(path)

    # If a semicolon-delimited file was initially parsed with the wrong separator,
    # re-read it explicitly so headers and values align with the expected columns.
    if len(df.columns) < 4:
        df = pd.read_csv(path, sep=";", engine="python")

    if len(df.columns) < 4:
        raise ValueError(f"Could not identify four TGA columns in {path}: {list(df.columns)}")

    # Data preview establishes column order as Time, Temperature, Weight, Derivative.
    temperature = pd.to_numeric(df.iloc[:, 1], errors="coerce")
    weight = pd.to_numeric(df.iloc[:, 2], errors="coerce")
    valid = temperature.notna() & weight.notna()
    return temperature[valid], weight[valid]


def main():
    out_dir = Path(OUT_DIR)
    out_dir.mkdir(parents=True, exist_ok=True)

    fig, ax = plt.subplots(figsize=(9, 6), constrained_layout=True)

    for file_path, label, color in (
        (DATA_FILES[0], "Lot A", "#1f77b4"),
        (DATA_FILES[1], "Lot B", "#d62728"),
    ):
        temperature, weight = load_tga(file_path)
        ax.plot(temperature, weight, label=label, color=color, linewidth=1.8)

    ax.set_xlabel("Temperature (°C)")
    ax.set_ylabel("Weight (%)")
    ax.set_title("TGA Comparison")
    ax.grid(True, linestyle="--", alpha=0.35)
    ax.legend(frameon=False)
    ax.margins(x=0.02)

    fig.savefig(out_dir / "tga_lot_comparison.png", dpi=300, bbox_inches="tight")
    plt.close(fig)


if __name__ == "__main__":
    main()
