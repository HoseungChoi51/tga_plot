import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import os

# Setup Korean font and output directory
plt.rcParams["font.family"] = "Noto Sans CJK KR"
plt.rcParams["axes.unicode_minus"] = False
OUT_DIR = "out/t1"
os.makedirs(OUT_DIR, exist_ok=True)

# Read data
file_path = "data/run_log.xlsx"
df = pd.read_excel(file_path, sheet_name="런로그")

# Helper function to find column by partial match (robust against whitespace/special char variations)
def find_col(df, pattern):
    cols = [c for c in df.columns if pattern in str(c)]
    if not cols:
        raise ValueError(f"Column matching '{pattern}' not found in {list(df.columns)}")
    return cols[0]

humidity_col = find_col(df, "외기습도")
yield_col = find_col(df, "CNT수율")
grade_col = find_col(df, "등급")

# Drop rows with missing values in relevant columns first
plot_df = df[[humidity_col, yield_col, grade_col]].dropna()

# Convert columns to numeric, forcing errors to NaN (handles cases where units might be inside the cell like "32%")
# This fixes the ValueError: could not convert string to float: '%'
plot_df[humidity_col] = pd.to_numeric(plot_df[humidity_col], errors='coerce')
plot_df[yield_col] = pd.to_numeric(plot_df[yield_col], errors='coerce')

# Drop any rows that became NaN after conversion
plot_df = plot_df.dropna(subset=[humidity_col, yield_col])

if plot_df.empty:
    print("No valid data remaining after cleaning.")
else:
    # 1. Scatter Plot: Humidity vs Yield colored by Grade
    fig, ax = plt.subplots(figsize=(10, 6))

    colors = {"A": "#2ca02c", "B": "#ff7f0e", "C": "#d62728"} # Green, Orange, Red

    for grade in ["A", "B", "C"]:
        subset = plot_df[plot_df[grade_col] == grade]
        if not subset.empty:
            ax.scatter(subset[humidity_col], subset[yield_col], 
                       label=f"Grade {grade}", color=colors.get(grade, "gray"), alpha=0.6, edgecolors='w', linewidth=0.5)

    ax.set_xlabel("외기습도 (%)")
    ax.set_ylabel("CNT수율 (g/g-cat)")
    ax.set_title("습도와 CNT 수율 관계 (등급별 색상 구분)")
    
    # Calculate correlation for trend line
    corr = plot_df[humidity_col].corr(plot_df[yield_col])
    
    # Only add trend line if there is variance and enough points
    if not np.isnan(corr) and len(plot_df) > 1:
        z = np.polyfit(plot_df[humidity_col], plot_df[yield_col], 1)
        p = np.poly1d(z)
        x_line = np.linspace(plot_df[humidity_col].min(), plot_df[humidity_col].max(), 100)
        ax.plot(x_line, p(x_line), "k--", alpha=0.5, label=f"전체 추세선 (r={corr:.2f})")
        
    ax.legend(title="품질 등급", loc="upper right")
    ax.grid(True, linestyle="--", alpha=0.3)

    plt.tight_layout()
    plt.savefig(os.path.join(OUT_DIR, "humidity_vs_yield_scatter.png"), dpi=300)
    plt.close()

    # 2. Box Plot: Humidity distribution per Grade
    fig, ax = plt.subplots(figsize=(8, 6))

    grades_order = ["A", "B", "C"]
    data_by_grade = []
    valid_grades = []
    
    for g in grades_order:
        subset = plot_df[plot_df[grade_col] == g][humidity_col]
        if not subset.empty:
            data_by_grade.append(subset.values)
            valid_grades.append(g)

    if data_by_grade:
        box = ax.boxplot(data_by_grade, labels=valid_grades, patch_artist=True)

        # Color the boxes
        for patch, grade in zip(box['boxes'], valid_grades):
            patch.set_facecolor(colors.get(grade, "lightgray"))
            patch.set_alpha(0.7)

        ax.set_ylabel("외기습도 (%)")
        ax.set_xlabel("품질 등급")
        ax.set_title("품질 등급별 외기습도 분포")
        ax.grid(True, axis="y", linestyle="--", alpha=0.3)

        # Add text annotations for means
        means = [np.mean(d) for d in data_by_grade]
        for i, mean_val in enumerate(means):
            ax.text(i+1, mean_val + 2, f"Mean: {mean_val:.1f}%", ha="center", fontsize=9, weight="bold")

        plt.tight_layout()
        plt.savefig(os.path.join(OUT_DIR, "humidity_distribution_by_grade.png"), dpi=300)
        plt.close()
    else:
        print("No data for box plot.")

    # 3. Moving Average / Binned Analysis to smooth out noise
    # Bin humidity into intervals and calculate mean yield and std dev
    # Adjust bins based on actual data range to avoid empty groups causing issues
    min_h = plot_df[humidity_col].min()
    max_h = plot_df[humidity_col].max()
    
    # Create bins roughly every 10 units starting from floor(min/10)*10
    start_bin = int(np.floor(min_h / 10) * 10)
    end_bin = int(np.ceil(max_h / 10) * 10) + 10
    bins = np.arange(start_bin, end_bin, 10) 

    try:
        plot_df["습도구간"] = pd.cut(plot_df[humidity_col], bins=bins)

        binned_stats = plot_df.groupby("습도구간").agg({
            yield_col: ["mean", "std", "count"]
        }).reset_index()

        # Flatten multi-index columns
        binned_stats.columns = ["습도구간", "평균수율", "수율표준편차", "런개수"]
        
        # Filter out groups with too few samples or NaNs
        binned_stats = binned_stats.dropna(subset=["평균수율"])
        binned_stats = binned_stats[binned_stats["런개수"] >= 1]

        if not binned_stats.empty:
            fig, ax = plt.subplots(figsize=(10, 6))

            # Calculate center points for plotting
            centers = [interval.mid for interval in binned_stats["습도구간"]]

            # Handle case where std is 0 or NaN (single sample groups)
            yerr = binned_stats["수율표준편차"].fillna(0).values
            
            ax.errorbar(centers, binned_stats["평균수율"], yerr=yerr, 
                        fmt="o-", capsize=5, markersize=8, linewidth=2, label="습도 구간별 평균 수율 (±STD)")

            ax.set_xlabel("외기습도 (%)")
            ax.set_ylabel("CNT수율 (g/g-cat)")
            ax.set_title("습도 구간별 평균 CNT 수율 변화")
            ax.grid(True, linestyle="--", alpha=0.3)
            ax.legend()

            # Annotate counts on top of each point
            # Determine a vertical offset for text so it doesn't overlap error bars too much
            avg_std = np.nanmean(yerr) if np.any(yerr > 0) else 1.0
            offset = max(0.5, avg_std * 0.2)
            
            for x, y, c in zip(centers, binned_stats["평균수율"], binned_stats["런개수"]):
                ax.text(x, y + offset, f"N={int(c)}", ha="center", va="bottom", fontsize=8)

            plt.tight_layout()
            plt.savefig(os.path.join(OUT_DIR, "humidity_binned_yield_analysis.png"), dpi=300)
            plt.close()
        else:
            print("Not enough data for binned analysis.")
    except Exception as e:
        print(f"Binned analysis failed: {e}")

print(f"Plots saved to {OUT_DIR}")
