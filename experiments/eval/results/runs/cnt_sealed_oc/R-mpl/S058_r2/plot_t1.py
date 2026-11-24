import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import os

# Set Korean font
plt.rcParams["font.family"] = "Noto Sans CJK KR"
plt.rcParams["axes.unicode_minus"] = False

# Define paths and constants
FILE_PATH = "data/downtime.xlsx"
OUT_DIR = "out/t1"
REF_DATE = pd.to_datetime("2026-03-02")

def generate_plot():
    # Read data
    df = pd.read_excel(FILE_PATH, sheet_name='정지이력')
    
    # Clean column names just in case of whitespace
    df.columns = df.columns.str.strip()
    
    # Ensure '일자' is datetime
    df['일자'] = pd.to_datetime(df['일자'])
    
    # Filter for '노즐 막힘' events
    nozzle_block_df = df[df['원인'] == '노즐 막힘'].copy()
    
    # Calculate Production Week: (일자 - 2026-03-02) // 7 + 1
    delta_days = (nozzle_block_df['일자'] - REF_DATE).dt.days
    # Floor division for weeks
    nozzle_block_df['production_week'] = (delta_days // 7) + 1
    
    # Pivot Table
    # Rows: 반응기, Cols: production_week, Values: count of events
    pivot_table = pd.pivot_table(
        nozzle_block_df,
        index='반응기',
        columns='production_week',
        values='일자',
        aggfunc='count',
        fill_value=0
    )
    
    # Reindex to ensure all reactors R1-R4 are present and sorted
    reactors = ['R1', 'R2', 'R3', 'R4']
    # Reindex rows
    pivot_table = pivot_table.reindex(reactors, fill_value=0)
    
    # Reindex columns to ensure continuous week numbers from min to max observed or full range?
    # The request implies weeks 1-26 might be relevant, but we should show what exists in the data context or just the pivoted result.
    # Usually, for a heatmap of time series, we want contiguous weeks.
    if not pivot_table.empty:
        min_week = pivot_table.columns.min()
        max_week = pivot_table.columns.max()
        # Create full range of weeks
        full_weeks = range(min_week, max_week + 1)
        pivot_table = pivot_table.reindex(columns=full_weeks, fill_value=0)
    
    # Plotting Heatmap using Matplotlib
    fig, ax = plt.subplots(figsize=(14, 6))
    
    # We need to transpose or set orientation so Reactors are rows and Weeks are columns.
    # pivot_table index is reactor (rows), columns are weeks. This matches standard matrix layout for imshow (rows=y, cols=x).
    
    im = ax.imshow(pivot_table.values, cmap='YlOrRd', aspect='auto')
    
    # Add colorbar
    cbar = ax.figure.colorbar(im, ax=ax)
    cbar.ax.set_ylabel('Event Count', rotation=-90, va="bottom", fontsize=12)
    
    # Set ticks and labels
    ax.set_xticks(np.arange(len(pivot_table.columns)))
    ax.set_yticks(np.arange(len(pivot_table.index)))
    ax.set_xticklabels(pivot_table.columns)
    ax.set_yticklabels(pivot_table.index)
    
    # Rotate x-axis labels for better readability
    plt.setp(ax.get_xticklabels(), rotation=45, ha="right", rotation_mode="anchor")
    
    # Labels
    ax.set_xlabel('Production Week', fontsize=12)
    ax.set_ylabel('Reactor', fontsize=12)
    ax.set_title('Nozzle Blockage Event Counts by Reactor and Production Week', fontsize=14)
    
    # Annotate cells with values if not too crowded (optional but good practice)
    # Given 26 weeks * 4 reactors = 104 cells, annotation might be messy. 
    # We will skip automatic annotation unless requested, or make it very small.
    # For clarity, let's keep it clean. If specific values were asked to be shown, we'd add them.
    
    fig.tight_layout()
    
    # Save figure
    os.makedirs(OUT_DIR, exist_ok=True)
    output_path = os.path.join(OUT_DIR, "nozzle_blockage_heatmap.png")
    plt.savefig(output_path, dpi=300)
    plt.close()

if __name__ == "__main__":
    generate_plot()
