import pandas as pd
import matplotlib.pyplot as plt
import os

# Ensure output directory exists
OUT_DIR = "out/t2"
os.makedirs(OUT_DIR, exist_ok=True)

# Set Korean font
plt.rcParams["font.family"] = "Noto Sans CJK KR"

# Load data
file_path = "data/run_log.xlsx"
df = pd.read_excel(file_path, sheet_name='런로그')

# Define column names based on preview
prod_speed_col = '생산속도 (g/h)'
operating_time_col = '가동시간 (h)'
reactor_col = '반응기'

# Check if columns exist, otherwise try common variations if needed
if prod_speed_col not in df.columns:
    matching_cols = [c for c in df.columns if '생산속도' in str(c)]
    if matching_cols:
        prod_speed_col = matching_cols[0]

if operating_time_col not in df.columns:
    matching_cols = [c for c in df.columns if '가동시간' in str(c)]
    if matching_cols:
        operating_time_col = matching_cols[0]

if reactor_col not in df.columns:
    matching_cols = [c for c in df.columns if '반응기' in str(c)]
    if matching_cols:
        reactor_col = matching_cols[0]

# Convert relevant columns to numeric to handle any string representations or errors
df[prod_speed_col] = pd.to_numeric(df[prod_speed_col], errors='coerce')
df[operating_time_col] = pd.to_numeric(df[operating_time_col], errors='coerce')

# Drop rows where conversion failed (NaNs) for these specific columns to avoid calculation issues
df_clean = df.dropna(subset=[prod_speed_col, operating_time_col])

# Calculate total production per row (in grams)
df_clean['총생산량_g'] = df_clean[prod_speed_col] * df_clean[operating_time_col]

# Group by reactor and sum the production quantity
total_production_by_reactor = df_clean.groupby(reactor_col)['총생산량_g'].sum()

# Sort reactors for consistent ordering (e.g., R1, R2, R3, R4)
total_production_by_reactor = total_production_by_reactor.sort_index()

# Prepare data for bar chart
labels = total_production_by_reactor.index.tolist()
values = total_production_by_reactor.values.tolist()

# Plotting
fig, ax = plt.subplots(figsize=(8, 6))

bars = ax.bar(labels, values, color=plt.cm.Paired.colors[:len(labels)])

# Add title and labels
ax.set_title('반응기별 총 생산량')
ax.set_xlabel('반응기')
ax.set_ylabel('총 생산량 (g)')

# Add value labels on top of bars
for bar in bars:
    height = bar.get_height()
    ax.text(bar.get_x() + bar.get_width()/2., height,
            f'{height:,.0f}',
            ha='center', va='bottom', fontsize=10)

# Save plot
output_file = os.path.join(OUT_DIR, "production_bar_by_reactor.png")
plt.tight_layout()
plt.savefig(output_file, dpi=300)
plt.close()
