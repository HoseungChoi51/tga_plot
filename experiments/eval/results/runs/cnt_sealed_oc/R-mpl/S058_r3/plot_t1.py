import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
import os

# Configuration
plt.rcParams["font.family"] = "Noto Sans CJK KR"
plt.rcParams["axes.unicode_minus"] = False
OUT_DIR = "out/t1"
os.makedirs(OUT_DIR, exist_ok=True)

# File paths based on preview
DOWNTIME_FILE = "data/downtime.xlsx"

def load_and_process_downtime():
    # Read the Excel file, sheet '정지이력'
    df = pd.read_excel(DOWNTIME_FILE, sheet_name='정지이력')
    
    # Clean column names if necessary (strip whitespace)
    df.columns = df.columns.str.strip()
    
    # Parse date column '일자'
    df['일자'] = pd.to_datetime(df['일자'], errors='coerce')
    
    # Define reference date for week calculation
    ref_date = datetime(2026, 3, 2)
    
    # Calculate Week number: (date - ref_date) // 7 + 1
    delta_days = (df['일자'] - ref_date).dt.days
    df['week'] = (delta_days // 7) + 1
    
    # Filter for '노즐 막힘' (Nozzle clogging) events only
    df_nozzle = df[df['원인'] == '노즐 막힘'].copy()
    
    # Create Pivot Table: Rows=반응기, Columns=week, Values=count of events
    pivot_table = pd.pivot_table(
        df_nozzle, 
        values='일자', 
        index='반응기', 
        columns='week', 
        aggfunc='count', 
        fill_value=0
    )
    
    # Ensure all reactors R1-R4 are present in rows
    all_reactors = ['R1', 'R2', 'R3', 'R4']
    # Reindex to ensure all reactors are present, filling missing with 0
    pivot_table = pivot_table.reindex(all_reactors, fill_value=0)
    
    # Ensure columns cover weeks 1-26 as per request hint
    all_weeks = list(range(1, 27))
    # Reindex columns to ensure weeks 1-26 are present, filling missing with 0
    pivot_table = pivot_table.reindex(columns=all_weeks, fill_value=0)
    
    return pivot_table

def plot_heatmap(pivot_data):
    fig, ax = plt.subplots(figsize=(14, 5))
    
    # Prepare data for imshow
    # We need a numeric matrix for imshow
    data_matrix = pivot_data.values.astype(float)
    
    # Use imshow to create heatmap since seaborn is not available
    im = ax.imshow(data_matrix, cmap="YlOrRd", aspect='auto')
    
    # Add colorbar
    cbar = ax.figure.colorbar(im, ax=ax)
    cbar.ax.set_ylabel('발생 횟수', rotation=-90, va="bottom")
    
    # Set ticks and labels
    ax.set_xticks(np.arange(len(pivot_data.columns)))
    ax.set_yticks(np.arange(len(pivot_data.index)))
    ax.set_xticklabels(pivot_data.columns)
    ax.set_yticklabels(pivot_data.index)
    
    # Rotate x-tick labels
    plt.setp(ax.get_xticklabels(), rotation=90, ha="right", rotation_mode="anchor")
    
    # Loop over data dimensions and create text annotations
    for i in range(len(pivot_data.index)):
        for j in range(len(pivot_data.columns)):
            val = data_matrix[i, j]
            # Only show text if value > 0 to avoid clutter, or show all? Request says "show as heatmap".
            # Usually heatmaps with counts annotate. Let's annotate integers.
            text_color = "black" if val < 0.5 * data_matrix.max() else "white"
            ax.text(j, i, f"{int(val)}", ha="center", va="center", color=text_color)
            
    ax.set_title('반응기별 주 단위 노즐 막힘 발생 횟수 Heatmap', fontsize=14, pad=20)
    ax.set_xlabel('생산 주차 (Week)', fontsize=12)
    ax.set_ylabel('반응기', fontsize=12, rotation=0, labelpad=15)
    
    plt.tight_layout()
    
    # Save figure
    save_path = os.path.join(OUT_DIR, "nozzle_clogging_weekly_heatmap.png")
    plt.savefig(save_path, dpi=300, bbox_inches='tight')
    plt.close(fig)
    print(f"Heatmap saved to {save_path}")

if __name__ == "__main__":
    try:
        pivot_df = load_and_process_downtime()
        
        if pivot_df.empty:
             # If empty due to some error, still try to plot structure if possible, 
             # but reindex should have filled it with zeros if dates parsed correctly.
             pass
            
        plot_heatmap(pivot_df)
    except Exception as e:
        print(f"Error occurred: {e}")
        import traceback
        traceback.print_exc()
