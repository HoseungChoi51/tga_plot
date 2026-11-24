import pandas as pd
import matplotlib.pyplot as plt
import os
import numpy as np

# Configuration
OUT_DIR = "out/t1"
DATA_FILE = "data/run_log.xlsx"
SHEET_NAME = "런로그"
OUTPUT_FILENAME = "pass_rate_by_reactor_week.png"

# Setup Font
plt.rcParams["font.family"] = "Noto Sans CJK KR"
plt.rcParams["axes.unicode_minus"] = False

# Create Output Directory
os.makedirs(OUT_DIR, exist_ok=True)

def generate_plot():
    # 1. Load Data
    try:
        df = pd.read_excel(DATA_FILE, sheet_name=SHEET_NAME)
    except Exception as e:
        print(f"Failed to load Excel file: {e}")
        return

    # 2. Check Required Columns and clean names if necessary
    # The preview shows '등급 (A/B/C)', but sometimes headers have extra spaces or encoding issues.
    # We will strip whitespace from all column names to be safe.
    df.columns = df.columns.str.strip()
    
    required_cols = ['반응기', '주차', '등급 (A/B/C)']
    
    # Try to find the grade column flexibly if exact match fails due to hidden chars
    grade_col = None
    for col in df.columns:
        if '등급' in col or 'Grade' in col:
            grade_col = col
            break
            
    if grade_col is None:
        # Fallback: check if 'V' header exists and rename? No, rely on name search.
        print("Could not identify Grade column.")
        return
        
    # Ensure other columns exist
    if '반응기' not in df.columns or '주차' not in df.columns:
        print("Missing essential columns: 반응기 or 주차")
        return

    # 3. Preprocess
    # Define Pass: A or B. 
    # Strip values just in case they have leading/trailing spaces like ' A'
    df['Grade_Clean'] = df[grade_col].astype(str).str.strip()
    df['Is_Pass'] = df['Grade_Clean'].isin(['A', 'B'])
    
    # Convert 주차 to numeric to ensure proper sorting and plotting
    # Some weeks might be read as strings or floats
    df['주차'] = pd.to_numeric(df['주차'], errors='coerce')
    
    # Drop rows where 주차 or 반응기 is NaN after conversion
    df = df.dropna(subset=['주차', '반응기', 'Is_Pass'])
    
    if df.empty:
        print("No valid data remaining after cleaning.")
        return

    # Calculate Pass Rate (%) per Reactor per Week
    # Group by Reactor and Week, take mean of Is_Pass (bool -> float), multiply by 100
    grouped_data = df.groupby(['반응기', '주차'])['Is_Pass'].mean().reset_index()
    grouped_data.rename(columns={'Is_Pass': 'Pass_Rate'}, inplace=True)
    
    # Sort for plotting consistency
    grouped_data.sort_values(by=['반응기', '주차'], inplace=True)

    # 4. Plotting
    fig, ax = plt.subplots(figsize=(12, 8))
    
    reactors = sorted(df['반응기'].unique())
    colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd', '#8c564b']
    
    has_plot = False
    for i, reactor in enumerate(reactors):
        subset = grouped_data[grouped_data['반응기'] == reactor]
        
        if not subset.empty:
            pass_rates = subset['Pass_Rate'] * 100
            weeks = subset['주차']
            
            ax.plot(weeks, pass_rates, 
                    marker='o', 
                    linestyle='-', 
                    linewidth=2, 
                    markersize=6,
                    label=f'{reactor}', 
                    color=colors[i % len(colors)])
            has_plot = True

    if not has_plot:
        print("No data points to plot.")
        plt.close(fig)
        return

    # 5. Formatting
    ax.set_title('반응기별 주차별 합격률 추이', fontsize=16, fontweight='bold')
    ax.set_xlabel('주차', fontsize=12)
    ax.set_ylabel('합격률 (%)', fontsize=12)
    ax.grid(True, linestyle='--', alpha=0.7)
    ax.legend(title='반응기', loc='best')
    
    # Set Y-axis limits reasonably (0-100)
    ax.set_ylim(0, 105)
    
    # X-ticks rotation
    plt.xticks(rotation=45)
    
    # Adjust layout
    plt.tight_layout()
    
    # 6. Save
    output_path = os.path.join(OUT_DIR, OUTPUT_FILENAME)
    try:
        plt.savefig(output_path, dpi=300)
        print(f"Figure successfully saved to: {output_path}")
    except Exception as e:
        print(f"Failed to save figure: {e}")
    finally:
        plt.close(fig)

if __name__ == "__main__":
    generate_plot()
