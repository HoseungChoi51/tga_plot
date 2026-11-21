import pandas as pd
import matplotlib.pyplot as plt
import os

# Set Korean font
plt.rcParams["font.family"] = "Noto Sans CJK KR"
plt.rcParams["axes.unicode_minus"] = False

# Define output directory
OUT_DIR = "out/t1"
os.makedirs(OUT_DIR, exist_ok=True)

# Read data
file_path = "data/run_log.xlsx"
df = pd.read_excel(file_path, sheet_name="런로그")

# Clean column names to remove potential hidden whitespace or special characters
df.columns = df.columns.str.strip()

# Ensure date column is datetime
df['일자'] = pd.to_datetime(df['일자'], errors='coerce')
df = df.dropna(subset=['일자'])

# Filter for March to August (3~8월)
mask = (df['일자'].dt.month >= 3) & (df['일자'].dt.month <= 8)
df_filtered = df[mask].copy()

# Identify columns dynamically to avoid KeyError due to slight naming differences
# We look for columns containing '생산속도' and '가동시간'
prod_speed_col = [c for c in df_filtered.columns if '생산속도' in c][0]
run_time_col = [c for c in df_filtered.columns if '가동시간' in c][0]

# Calculate production per run: 생산속도(g/h) * 가동시간(h) / 1000 -> kg
df_filtered['생산량_kg'] = df_filtered[prod_speed_col] * df_filtered[run_time_col] / 1000

# Group by reactor and sum production
reactor_production = df_filtered.groupby('반응기')['생산량_kg'].sum().reset_index()

# Sort reactors for consistent plotting order (R1, R2, R3, R4)
reactor_order = ['R1', 'R2', 'R3', 'R4']
reactor_production['반응기'] = pd.Categorical(reactor_production['반응기'], categories=reactor_order, ordered=True)
reactor_production = reactor_production.sort_values('반응기')

# Plotting
fig, ax = plt.subplots(figsize=(10, 6))

bars = ax.bar(reactor_production['반응기'], reactor_production['생산량_kg'], color=['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728'])

# Add labels and title
ax.set_xlabel('반응기', fontsize=12)
ax.set_ylabel('누적 총 생산량 (kg)', fontsize=12)
ax.set_title('3~8월 반응기별 누적 총 생산량', fontsize=14)

# Add value labels on top of bars
for bar in bars:
    height = bar.get_height()
    ax.text(bar.get_x() + bar.get_width()/2., height,
            f'{height:.1f}',
            ha='center', va='bottom', fontsize=10)

# Adjust layout
plt.tight_layout()

# Save figure
output_path = os.path.join(OUT_DIR, "reactor_cumulative_production.png")
plt.savefig(output_path, dpi=300)
plt.close()
