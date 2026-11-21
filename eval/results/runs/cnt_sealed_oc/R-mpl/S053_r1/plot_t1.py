import pandas as pd
import matplotlib.pyplot as plt
import os

# Ensure output directory exists
OUT_DIR = "out/t1"
os.makedirs(OUT_DIR, exist_ok=True)

# Set Korean font
plt.rcParams["font.family"] = "Noto Sans CJK KR"
plt.rcParams["axes.unicode_minus"] = False

# Read data
file_path = "data/downtime.xlsx"
df = pd.read_excel(file_path, sheet_name='정지이력')

# Identify columns by their Korean headers from the preview
# A 일자, B 시작시각, C 반응기, D 원인, E 정지시간(분), F 비고
col_date = '일자'
col_reactor = '반응기'
col_reason = '원인'
col_duration = '정지시간(분)'

# Clean data: ensure duration is numeric and drop rows with missing critical info for sorting/labeling
df[col_duration] = pd.to_numeric(df[col_duration], errors='coerce')
df_clean = df.dropna(subset=[col_duration, col_reactor, col_reason, col_date])

# Sort by duration descending and get top 10
top_10 = df_clean.sort_values(by=col_duration, ascending=False).head(10)

# Prepare labels: '반응기 / 원인 / 일자'
# Note: Date might be a datetime object or string. We'll format it to string for label consistency if needed, 
# but usually str() works fine. Let's ensure date is readable.
def make_label(row):
    # Convert date to string if it's not already simple text, keeping it concise
    date_str = str(row[col_date]).split(' ')[0] # Remove time part if present in date column
    return f"{row[col_reactor]} / {row[col_reason]} / {date_str}"

labels = top_10.apply(make_label, axis=1)
durations = top_10[col_duration].values

# Plotting
fig, ax = plt.subplots(figsize=(12, 8))
bars = ax.barh(range(len(durations)), durations, color='steelblue', edgecolor='black')

# Set y-ticks to labels
ax.set_yticks(range(len(labels)))
ax.set_yticklabels(labels)
ax.invert_yaxis() # So longest is at the top

# Add value labels on bars
for i, v in enumerate(durations):
    ax.text(v + max(durations)*0.01, i, str(int(v)), va='center', ha='left', fontsize=9)

ax.set_xlabel('정지 시간 (분)', fontsize=12)
ax.set_title('최장 정지 사건 Top 10 (반응기별/원인별)', fontsize=14)
ax.grid(axis='x', linestyle='--', alpha=0.7)

plt.tight_layout()
save_path = os.path.join(OUT_DIR, "top10_downtime.png")
plt.savefig(save_path, dpi=300)
plt.close()
