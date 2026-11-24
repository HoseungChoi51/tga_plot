import os
import re
import pandas as pd
import matplotlib.pyplot as plt

DATA_FILE = "/home/chs/Work/tga_plot/eval/inputs_b/polymers.xlsx"
OUT_DIR = "/home/chs/Work/tga_plot/eval/results/runs/sx_think/R-mpl-brief/B15_r1/out"


def normalized(name):
    return re.sub(r"[^a-z0-9]+", " ", str(name).lower())


def find_column(df, patterns, exclude=None):
    exclude = set(exclude or [])
    for pattern in patterns:
        for col in df.columns:
            if col in exclude:
                continue
            if pattern in normalized(col):
                return col
    return None


def load_sheets(path):
    ext = os.path.splitext(path)[1].lower()
    sheets = []

    if ext in (".xlsx", ".xls"):
        xls = pd.ExcelFile(path)
        for sheet_name in xls.sheet_names:
            df = pd.read_excel(xls, sheet_name=sheet_name)
            sheets.append((str(sheet_name), df))
    else:
        df = pd.read_csv(path, sep=None, engine="python")
        sheets.append(("Sheet1", df))

    return sheets


def prepare_sheet(df):
    df = df.copy()
    df.columns = [str(c).strip() for c in df.columns]

    df_num = df.apply(pd.to_numeric, errors="coerce")
    numeric_cols = [c for c in df_num.columns if df_num[c].notna().any()]

    x_col = find_column(df, ["temperature", "temp"])
    y2_col = find_column(df, ["deriv", "dtg", "derivative"])
    y1_col = find_column(df, ["weight", "wt"], exclude=[y2_col])

    if y1_col == y2_col:
        y1_col = None

    if x_col is None:
        x_col = numeric_cols[0] if numeric_cols else df.columns[0]

    if y1_col is None:
        candidates = [c for c in numeric_cols if c not in (x_col, y2_col)]
        if candidates:
            y1_col = min(
                candidates,
                key=lambda c: abs(float(df_num[c].median()) - 100.0)
            )

    if y2_col is None:
        candidates = [c for c in numeric_cols if c not in (x_col, y1_col)]
        if candidates:
            y2_col = min(candidates, key=lambda c: float(df_num[c].min()))

    if x_col is None or y1_col is None:
        return None

    cols = [x_col, y1_col]
    if y2_col is not None:
        cols.append(y2_col)

    out = df_num[cols].dropna(subset=[x_col, y1_col])
    if y2_col is not None:
        out = out.dropna(subset=[y2_col])

    out = out.sort_values(x_col).reset_index(drop=True)
    return out, x_col, y1_col, y2_col


def main():
    plt.rcParams.update({
        "font.family": "sans-serif",
        "font.sans-serif": [
            "Noto Sans CJK KR",
            "Noto Sans KR",
            "Malgun Gothic",
            "DejaVu Sans",
        ],
        "axes.unicode_minus": False,
    })

    os.makedirs(OUT_DIR, exist_ok=True)

    sheets = load_sheets(DATA_FILE)

    prepared = []
    for sheet_name, df in sheets:
        result = prepare_sheet(df)
        if result is not None:
            prepared.append((sheet_name, *result))

    if not prepared:
        fig, ax = plt.subplots(figsize=(8, 5))
        ax.set_title("No valid TGA data")
        fig.savefig(
            os.path.join(OUT_DIR, "TGA_overlay.png"),
            dpi=300,
            bbox_inches="tight",
        )
        plt.close(fig)
        return

    fig, ax1 = plt.subplots(figsize=(12, 7))
    ax2 = ax1.twinx()

    palette = plt.cm.tab20.colors

    for i, (sheet_name, df, x_col, y1_col, y2_col) in enumerate(prepared):
        color = palette[i % len(palette)]

        ax1.plot(
            df[x_col],
            df[y1_col],
            color=color,
            linestyle="-",
            linewidth=1.6,
            label=f"{sheet_name} Weight (%)",
            zorder=2,
        )

        if y2_col is not None:
            ax2.plot(
                df[x_col],
                -df[y2_col],
                color=color,
                linestyle="--",
                linewidth=1.6,
                label=f"{sheet_name} DTG",
                zorder=2,
            )

        if len(df) > 0:
            residue_idx = (df[x_col] - 800).abs().idxmin()
            residue_temp = float(df[x_col].loc[residue_idx])
            residue_weight = float(df[y1_col].loc[residue_idx])

            ax1.scatter(
                [residue_temp],
                [residue_weight],
                color=color,
                marker="o",
                s=35,
                zorder=4,
            )
            ax1.annotate(
                f"{sheet_name} Residue {residue_weight:.1f}%",
                xy=(residue_temp, residue_weight),
                xytext=(8, -14 if i % 2 == 0 else 16),
                textcoords="offset points",
                fontsize=8,
                color=color,
                zorder=5,
            )

            if y2_col is not None:
                mask = df[x_col] > 150
                if mask.any():
                    dtg_plot = -df.loc[mask, y2_col]
                    if not dtg_plot.empty:
                        peak_idx = dtg_plot.idxmax()
                        peak_temp = float(df[x_col].loc[peak_idx])
                        peak_dtg = float(df[y2_col].loc[peak_idx])

                        ax2.scatter(
                            [peak_temp],
                            [-peak_dtg],
                            color=color,
                            marker="^",
                            s=40,
                            zorder=4,
                        )
                        ax2.annotate(
                            f"{sheet_name} {peak_temp:.0f} °C",
                            xy=(peak_temp, -peak_dtg),
                            xytext=(-12, 12 if i % 2 == 0 else -18),
                            textcoords="offset points",
                            fontsize=8,
                            color=color,
                            zorder=5,
                        )

    ax1.set_xlabel("Temperature (°C)")
    ax1.set_ylabel("Weight (%)")
    ax2.set_ylabel("DTG (%/°C) (inverted)")
    ax1.set_title("TGA (" + ", ".join(sheet for sheet, *_ in prepared) + ")")
    ax1.grid(True, linestyle=":", alpha=0.45)

    handles1, labels1 = ax1.get_legend_handles_labels()
    handles2, labels2 = ax2.get_legend_handles_labels()

    ax1.legend(
        handles1 + handles2,
        labels1 + labels2,
        loc="center left",
        bbox_to_anchor=(1.05, 0.5),
        fontsize=9,
        title="Sample / Signal",
    )

    fig.savefig(
        os.path.join(OUT_DIR, "TGA_overlay.png"),
        dpi=300,
        bbox_inches="tight",
    )
    plt.close(fig)


if __name__ == "__main__":
    main()
