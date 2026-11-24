import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import os

# Setup environment variables and paths
OUT_DIR = "out/t1"
os.makedirs(OUT_DIR, exist_ok=True)
DATA_FILE = "data/downtime.xlsx"

# Set Korean font for matplotlib
plt.rcParams["font.family"] = "Noto Sans CJK KR"
plt.rcParams["axes.unicode_minus"] = False

# Load data
try:
    df = pd.read_excel(DATA_FILE, sheet_name='정지이력')
except Exception as e:
    print(f"Error reading file: {e}")
    exit()

# Ensure date column is datetime
df['일자'] = pd.to_datetime(df['일자'])

# Filter for June–August 2026 (2026-06-01 to 2026-08-30)
start_date = '2026-06-01'
end_date = '2026-08-30'
mask = (df['일자'] >= start_date) & (df['일자'] <= end_date)
df_filtered = df[mask]

# Group by reactor and sum downtime minutes
grouped = df_filtered.groupby('반응기')['정지시간(분)'].sum().reset_index()

# Check if there's any data
if grouped.empty:
    print("No data found for the specified period.")
else:
    # Sort by reactor name for consistent pie chart order
    grouped = grouped.sort_values(by='반응기')
    
    labels = grouped['반응기']
    sizes = grouped['정지시간(분)']
    
    # Create figure and axis
    fig, ax = plt.subplots(figsize=(8, 8))
    
    # Plot pie chart
    wedges, texts, autotexts = ax.pie(sizes, 
                                       labels=labels, 
                                       autopct='%1.1f%%', 
                                       startangle=90, 
                                       colors=plt.cm.Pastel1(np.arange(len(labels))))
    
    # Add title and labels
    ax.set_title('반응기별 총 정지 시간 비율 (2026년 6월 ~ 8월)', fontsize=14, pad=20)
    
    # Equal aspect ratio ensures that pie is drawn as a circle
    ax.axis('equal')
    
    # Save plot
    output_path = os.path.join(OUT_DIR, "downtime_pie_jun_aug.png")
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close(fig)
    print(f"Plot saved to {output_path}")
