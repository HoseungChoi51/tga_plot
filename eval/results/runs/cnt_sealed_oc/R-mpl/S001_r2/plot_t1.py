import pandas as pd
import matplotlib.pyplot as plt
import os

# Set Korean font
plt.rcParams["font.family"] = "Noto Sans CJK KR"
plt.rcParams['axes.unicode_minus'] = False

# Define output directory
OUT_DIR = "out/t1"
os.makedirs(OUT_DIR, exist_ok=True)

# Load data
file_path = "data/run_log.xlsx"
df = pd.read_excel(file_path, sheet_name="런로그")

# Clean column names: strip whitespace and newlines to ensure matching
df.columns = df.columns.str.strip()

# Ensure date column is datetime
# The previous error suggested 'yyyy-mm-dd' might be in the data or parsing issues.
# We use errors='coerce' to turn unparseable dates into NaT, then drop them.
df['일자'] = pd.to_datetime(df['일자'], errors='coerce')
df = df.dropna(subset=['일자'])

# Filter for March to August (3~8월)
start_date = pd.Timestamp('2026-03-01')
end_date = pd.Timestamp('2026-08-31')
df_filtered = df[(df['일자'] >= start_date) & (df['일자'] <= end_date)].copy()

# Identify production columns by checking which ones contain the key substrings
# This handles potential minor variations in spacing or units notation if stripping didn't fix it completely
prod_speed_col = None
oper_time_col = None

for col in df_filtered.columns:
    if '생산속도' in col and '(g/h)' in col:
        prod_speed_col = col
    elif '가동시간' in col and '(h)' in col:
        oper_time_col = col

if prod_speed_col is None or oper_time_col is None:
    # Fallback to exact names from preview if fuzzy match fails, after ensuring strip worked
    if '생산속도 (g/h)' in df_filtered.columns:
        prod_speed_col = '생산속도 (g/h)'
    if '가동시간 (h)' in df_filtered.columns:
        oper_time_col = '가동시간 (h)'

if prod_speed_col is None or oper_time_col is None:
    raise ValueError(f"Required columns not found. Columns present: {list(df_filtered.columns)}")

# Calculate production per run in kg: (생산속도 g/h * 가동시간 h) / 1000
df_filtered['run_production_kg'] = (df_filtered[prod_speed_col] * df_filtered[oper_time_col]) / 1000.0

# Group by Reactor and sum the production
grouped = df_filtered.groupby('반응기')['run_production_kg'].sum().reset_index()

# Sort reactors R1-R4 for consistent plotting
reactor_order = ['R1', 'R2', 'R3', 'R4']
grouped['반응기'] = pd.Categorical(grouped['반응기'], categories=reactor_order, ordered=True)
grouped = grouped.sort_values('반응기')

# Plotting
fig, ax = plt.subplots(figsize=(8, 6))
bars = ax.bar(grouped['반응기'], grouped['run_production_kg'], color='steelblue', edgecolor='black')

# Add value labels on top of bars
for bar in bars:
    height = bar.get_height()
    ax.text(bar.get_x() + bar.get_width() / 2., height,
            f'{height:.1f}',
            ha='center', va='bottom', fontsize=10)

# Labels and Title
ax.set_xlabel('반응기')
ax.set_ylabel('누적 총 생산량 (kg)')
ax.set_title('반응기별 누적 총 생산량 (2026년 3월 ~ 8월)')
ax.grid(axis='y', linestyle='--', alpha=0.7)

# Save plot
output_file = os.path.join(OUT_DIR, "reactor_total_production.png")
plt.tight_layout()
plt.savefig(output_file, dpi=300)
plt.close()
