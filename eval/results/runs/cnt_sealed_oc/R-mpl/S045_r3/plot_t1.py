import pandas as pd
import matplotlib.pyplot as plt
import os

# Set Korean font
plt.rcParams["font.family"] = "Noto Sans CJK KR"

# Define output directory
OUT_DIR = "out/t1"
os.makedirs(OUT_DIR, exist_ok=True)

# Read data
file_path = "data/run_log.xlsx"
sheet_name = '런로그'

try:
    df = pd.read_excel(file_path, sheet_name=sheet_name)
    
    # Check if '작업자' column exists
    if '작업자' not in df.columns:
        raise KeyError("Column '작업자' not found in the dataframe.")
    
    # Count runs per operator
    operator_counts = df['작업자'].value_counts()
    
    # Create pie chart
    fig, ax = plt.subplots(figsize=(8, 6))
    
    # Use autopct to show percentage on slices
    # Sort by count for better visualization (optional, but value_counts is already sorted desc)
    wedges, texts, autotexts = ax.pie(operator_counts.values, labels=operator_counts.index, 
                                      autopct='%1.1f%%', startangle=90, textprops={'fontsize': 12})
    
    # Equal aspect ratio ensures that pie is drawn as a circle.
    ax.axis('equal')
    
    # Title
    plt.title('작업자별 런 담당 비율', fontsize=14, pad=20)
    
    # Save figure
    output_file = os.path.join(OUT_DIR, "operator_run_ratio_pie.png")
    plt.tight_layout()
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    plt.close()
    
except Exception as e:
    print(f"An error occurred: {e}")
