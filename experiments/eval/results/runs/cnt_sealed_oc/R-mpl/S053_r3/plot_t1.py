import pandas as pd
import matplotlib.pyplot as plt
import os

# Set Korean font
plt.rcParams["font.family"] = "Noto Sans CJK KR"
plt.rcParams['axes.unicode_minus'] = False

# Output directory
OUT_DIR = "out/t1"
os.makedirs(OUT_DIR, exist_ok=True)

# Load data
file_path = "data/downtime.xlsx"
sheet_name = '정지이력'

try:
    df = pd.read_excel(file_path, sheet_name=sheet_name)
except Exception as e:
    print(f"Error reading file: {e}")
    # Fallback or empty dataframe handling could go here, but assuming success based on prompt context
    
# Clean column names if necessary (strip whitespace)
df.columns = [str(c).strip() for c in df.columns]

# Identify relevant columns
# Expected columns: 일자, 시작시각, 반응기, 원인, 정지시간(분), 비고
col_date = '일자'
col_reactor = '반응기'
col_reason = '원인'
col_duration = '정지시간(분)'

# Check if columns exist, adjust if they have different naming conventions in the actual file vs preview description
if col_duration not in df.columns:
    # Try finding a numeric column that represents duration
    num_cols = df.select_dtypes(include=['number']).columns.tolist()
    if len(num_cols) > 0:
        # Assume the first numeric column is duration if name mismatch, but better to look for keywords
        pass 

# Sort by duration descending and take top 10
# Ensure duration is numeric
df[col_duration] = pd.to_numeric(df[col_duration], errors='coerce')
df_sorted = df.sort_values(by=col_duration, ascending=False).head(10)

# Prepare tick labels: '반응기 / 원인 / 일자'
# Convert date to string for labeling
df_sorted['Label'] = (
    df_sorted[col_reactor].astype(str) + " / " + 
    df_sorted[col_reason].astype(str) + " / " + 
    df_sorted[col_date].astype(str)
)

# Plot
fig, ax = plt.subplots(figsize=(12, 8))

bars = ax.barh(range(len(df_sorted)), df_sorted[col_duration], color='skyblue', edgecolor='black')

# Invert y-axis so the longest bar is at the top
ax.invert_yaxis()

# Set y-ticks to the prepared labels
ax.set_yticks(range(len(df_sorted)))
ax.set_yticklabels(df_sorted['Label'], fontsize=10)

# Add values on bars
for i, v in enumerate(df_sorted[col_duration]):
    ax.text(v + 5, i, str(int(v)), va='center', ha='left', fontsize=9)

ax.set_xlabel('정지시간(분)', fontsize=12)
ax.set_title('Top 10 가장 긴 정지 이벤트', fontsize=14)
ax.grid(axis='x', linestyle='--', alpha=0.7)

plt.tight_layout()
save_path = os.path.join(OUT_DIR, "top_10_downtime.png")
plt.savefig(save_path, dpi=300)
plt.close()

print(f"Plot saved to {save_path}")
