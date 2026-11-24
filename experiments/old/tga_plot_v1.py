#!/usr/bin/env python3
"""
tga_plot.py - make one TGA/DTG plot per sheet of an Excel workbook.

Each sheet is expected to hold four columns:
    Time (unused) | Temperature (°C) | Weight (%) | D.W (%/°C)
A header row is optional; extra header/unit rows are skipped automatically.

For each sheet the script draws
  * Weight (%) vs Temperature on the left y-axis,
  * Derivative weight (DTG) vs Temperature on the right y-axis,
  * the residue at 800 °C (interpolated) and the DTG peak temperature(s),
and uses the sheet name as the title. Axis ranges follow the data.

It also writes summary.csv with the residue and peak temperatures per sheet.

Usage:
    python tga_plot.py data.xlsx                    # PNGs into ./data_plots/
    python tga_plot.py data.xlsx -o out --pdf       # also save PDFs
    python tga_plot.py data.xlsx --max-peaks 1      # only the main DTG peak
    python tga_plot.py data.xlsx --dtg-sign auto    # plot DTG with the sign stored in the file

Requires: pandas, openpyxl, matplotlib, numpy, scipy
"""
import argparse
import re
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy.signal import find_peaks, savgol_filter

WEIGHT_COLOR = "#1f4e9c"   # blue  - weight curve, left axis
DTG_COLOR = "#c0392b"      # red   - DTG curve, right axis


# ---------------------------------------------------------------- reading
def _find_col(cols, patterns):
    for c in cols:
        name = str(c).strip().lower()
        if any(re.search(p, name) for p in patterns):
            return c
    return None


def read_sheet(df_raw):
    """Return a DataFrame with numeric columns T, W, DTG (sorted as recorded)."""
    df = df_raw.copy()
    cols = list(df.columns)
    t = _find_col(cols, [r"^temp", r"temperature", r"°c$", r"\(c\)"])
    w = _find_col(cols, [r"^weight", r"^wt", r"mass", r"^tg\b"])
    d = _find_col(cols, [r"d\.?\s*w", r"deriv", r"dtg", r"/\s*°?c"])
    if None in (t, w, d) or len({t, w, d}) < 3:
        # fall back to column positions: Time, Temperature, Weight, D.W
        if df.shape[1] < 4:
            raise ValueError(f"expected 4 columns, found {df.shape[1]}")
        t, w, d = cols[1], cols[2], cols[3]
    out = pd.DataFrame({
        "T": pd.to_numeric(df[t], errors="coerce"),
        "W": pd.to_numeric(df[w], errors="coerce"),
        "DTG": pd.to_numeric(df[d], errors="coerce"),
    }).dropna()
    if len(out) < 10:
        raise ValueError("fewer than 10 numeric rows")
    return out.reset_index(drop=True)


# ---------------------------------------------------------------- analysis
def residue_at(T, W, target):
    """Weight % at `target` °C (linear interpolation on the heating part)."""
    if T.max() < target:
        return None
    # use only rising temperatures so np.interp sees a monotonic x
    keep = np.r_[True, np.diff(np.maximum.accumulate(T)) > 0]
    return float(np.interp(target, T[keep], W[keep]))


def dtg_peaks(T, dtg_loss, max_peaks, min_rel, t_min):
    """Find peaks of the mass-loss rate. `dtg_loss` is positive for mass loss.

    Returns a list of (index, T, value) sorted by temperature.
    min_rel: a secondary peak must be at least this fraction of the main peak.
    """
    y = dtg_loss.copy()
    n = len(y)
    win = max(5, (n // 100) | 1)          # light smoothing, odd window
    if win < n:
        y = savgol_filter(y, win, 2)
    valid = T >= t_min
    if not valid.any():
        return []
    top = y[valid].max()
    if top <= 0:
        return []
    idx, props = find_peaks(y, height=min_rel * top, prominence=0.5 * min_rel * top)
    idx = [i for i in idx if valid[i]]
    if not idx:                              # fall back to the global maximum
        idx = [int(np.argmax(np.where(valid, y, -np.inf)))]
    idx = sorted(idx, key=lambda i: y[i], reverse=True)[:max_peaks]
    # report the raw (unsmoothed) value at the peak position
    return sorted([(i, float(T[i]), float(dtg_loss[i])) for i in idx], key=lambda p: p[1])


# ---------------------------------------------------------------- plotting
def plot_sheet(name, df, args):
    T = df["T"].to_numpy(float)
    W = df["W"].to_numpy(float)
    D = df["DTG"].to_numpy(float)

    # Sign convention: many instruments export DTG as negative during mass loss.
    # "auto" keeps the data as recorded; "up"/"down" force the peak direction.
    loss_is_negative = abs(D.min()) > abs(D.max())
    loss = -D if loss_is_negative else D            # positive = losing mass
    if args.dtg_sign == "auto":
        D_plot = D
    elif args.dtg_sign == "up":
        D_plot = loss
    else:  # "down"
        D_plot = -loss
    plot_sign = 1.0 if np.allclose(D_plot, loss) else -1.0

    res = residue_at(T, W, args.residue_temp)
    peaks = dtg_peaks(T, loss, args.max_peaks, args.min_peak, args.peak_tmin)

    fig, ax1 = plt.subplots(figsize=(6.4, 4.6), dpi=args.dpi)
    ax2 = ax1.twinx()

    ax1.plot(T, W, color=WEIGHT_COLOR, lw=1.8, label="Weight")
    ax2.plot(T, D_plot, color=DTG_COLOR, lw=1.4, label="Deriv. weight")

    ax1.set_xlabel("Temperature (°C)")
    ax1.set_ylabel("Weight (%)", color=WEIGHT_COLOR)
    ax2.set_ylabel("Deriv. weight (%/°C)", color=DTG_COLOR)
    ax1.tick_params(axis="y", colors=WEIGHT_COLOR)
    ax2.tick_params(axis="y", colors=DTG_COLOR)
    ax2.spines["left"].set_color(WEIGHT_COLOR)
    ax2.spines["right"].set_color(DTG_COLOR)

    # automatic ranges with a little head-room for the labels
    ax1.set_xlim(T.min(), T.max())
    wr = W.max() - W.min() or 1.0
    ax1.set_ylim(W.min() - 0.08 * wr, W.max() + 0.12 * wr)
    dr = D_plot.max() - D_plot.min() or 1.0
    ax2.set_ylim(D_plot.min() - 0.12 * dr, D_plot.max() + 0.18 * dr)

    # residue annotation
    if res is not None:
        ax1.plot([args.residue_temp], [res], "o", ms=6, mfc="white",
                 mec=WEIGHT_COLOR, mew=1.6, zorder=5)
        ax1.annotate(f"Residue at {args.residue_temp:g} °C\n{res:.1f} %",
                     xy=(args.residue_temp, res), xytext=(0, 45),
                     textcoords="offset points", ha="center", va="bottom",
                     fontsize=9, color=WEIGHT_COLOR, zorder=6,
                     bbox=dict(boxstyle="round,pad=0.25", fc="white", ec="none", alpha=0.85),
                     arrowprops=dict(arrowstyle="-", color=WEIGHT_COLOR, lw=0.8))
    else:
        ax1.text(0.98, 0.04, f"T max = {T.max():.0f} °C (< {args.residue_temp:g} °C):\n"
                 f"no residue value", transform=ax1.transAxes, ha="right",
                 va="bottom", fontsize=8, color="gray")

    # DTG peak annotations
    for i, tp, _ in peaks:
        yp = D_plot[i]
        ax2.plot([tp], [yp], "v" if plot_sign < 0 else "^", ms=6,
                 color=DTG_COLOR, zorder=5)
        ax2.annotate(f"{tp:.0f} °C", xy=(tp, yp),
                     xytext=(0, 10 if plot_sign > 0 else -12),
                     textcoords="offset points", ha="center",
                     va="bottom" if plot_sign > 0 else "top",
                     fontsize=9, color=DTG_COLOR, fontweight="bold")

    h1, l1 = ax1.get_legend_handles_labels()
    h2, l2 = ax2.get_legend_handles_labels()
    ax1.legend(h1 + h2, l1 + l2, loc="center left", frameon=False, fontsize=9)
    ax1.set_title(name)
    for a in (ax1, ax2):
        a.tick_params(direction="in")
    fig.tight_layout()

    stem = re.sub(r"[^\w.-]+", "_", name).strip("_") or "sheet"
    out = Path(args.outdir) / f"{stem}.png"
    fig.savefig(out)
    if args.pdf:
        fig.savefig(out.with_suffix(".pdf"))
    plt.close(fig)

    return {
        "sheet": name,
        f"residue_{args.residue_temp:g}C_pct": None if res is None else round(res, 2),
        "Tmax_measured_C": round(float(T.max()), 1),
        "dtg_peak_T_C": "; ".join(f"{p[1]:.1f}" for p in peaks),
        "dtg_peak_rate_pct_per_C": "; ".join(f"{abs(p[2]):.3f}" for p in peaks),
        "dtg_sign_in_file": "negative" if loss_is_negative else "positive",
        "plot": out.name,
    }


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("xlsx", help="Excel workbook, one sample per sheet")
    ap.add_argument("-o", "--outdir", help="output folder (default: <file>_plots)")
    ap.add_argument("--sheets", nargs="*", help="only these sheet names")
    ap.add_argument("--residue-temp", type=float, default=800.0,
                    help="temperature for the residue label (default 800)")
    ap.add_argument("--max-peaks", type=int, default=2,
                    help="max DTG peaks to label (default 2)")
    ap.add_argument("--min-peak", type=float, default=0.1,
                    help="a secondary peak must be >= this fraction of the "
                         "main peak (default 0.1)")
    ap.add_argument("--peak-tmin", type=float, default=150.0,
                    help="ignore DTG peaks below this temperature, e.g. "
                         "moisture loss (default 150)")
    ap.add_argument("--dtg-sign", choices=["auto", "up", "down"], default="up",
                    help="up (default) = mass-loss peaks point up; down = they point down; auto = as in the file")
    ap.add_argument("--pdf", action="store_true", help="also save PDF")
    ap.add_argument("--dpi", type=int, default=300)
    args = ap.parse_args()

    src = Path(args.xlsx)
    args.outdir = args.outdir or str(src.with_suffix("")) + "_plots"
    Path(args.outdir).mkdir(parents=True, exist_ok=True)

    sheets = pd.read_excel(src, sheet_name=args.sheets or None)
    rows = []
    for name, raw in sheets.items():
        try:
            df = read_sheet(raw)
        except ValueError as e:
            print(f"[skip] {name}: {e}")
            continue
        r = plot_sheet(str(name), df, args)
        rows.append(r)
        res = r[f"residue_{args.residue_temp:g}C_pct"]
        print(f"[ok]   {name}: residue={res} %, DTG peaks={r['dtg_peak_T_C']} °C")

    if rows:
        pd.DataFrame(rows).to_csv(Path(args.outdir) / "summary.csv", index=False)
        print(f"\n{len(rows)} plot(s) and summary.csv written to {args.outdir}/")


if __name__ == "__main__":
    main()
