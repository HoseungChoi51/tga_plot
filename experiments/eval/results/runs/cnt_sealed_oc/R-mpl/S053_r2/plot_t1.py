import pandas as pd
import matplotlib.pyplot as plt
import os

# Ensure output directory exists
OUT_DIR = "out/t1"
os.makedirs(OUT_DIR, exist_ok=True)

# Set font for Korean text
plt.rcParams["font.family"] = "Noto Sans CJK KR"
plt.rcParams["axes.unicode_minus"] = False  # To display minus sign correctly in plots

# Load data
file_path = "data/downtime.xlsx"
sheet_name = "정지이력"

try:
    df = pd.read_excel(file_path, sheet_name=sheet_name)
except Exception as e:
    print(f"Error loading file: {e}")
    raise e

# Clean column names if necessary (though the preview suggests they are standard)
# The preview shows columns: A 일자, B 시작시각, C 반응기, D 원인, E 정지시간(분), F 비고
# Let's ensure we have the right column names by stripping whitespace
df.columns = [str(col).strip() for col in df.columns]

# Check if required columns exist
required_cols = ['일자', '반응기', '원인', '정지시간(분)']
for col in required_cols:
    if col not in df.columns:
        raise ValueError(f"Required column '{col}' not found in data.")

# Convert '정지시간(분)' to numeric, coercing errors to NaN and dropping them
df['정지시간(분)'] = pd.to_numeric(df['정지시간(분)'], errors='coerce')
df.dropna(subset=['정지시간(분)'], inplace=True)

# Sort by duration descending
df_sorted = df.sort_values(by='정지시간(분)', ascending=False)

# Get Top 10
top_10 = df_sorted.head(10).copy()

# Prepare tick labels: '반응기 / 원인 / 일자'
# We need to format the date if it's a datetime object, otherwise keep as string
def format_label(row):
    reactor = str(row['반응기'])
    cause = str(row['원인'])
    
    # Handle date formatting
    date_val = row['일자']
    if isinstance(date_val, pd.Timestamp) or hasattr(date_val, 'strftime'):
        try:
            date_str = date_val.strftime('%Y-%m-%d')
        except:
            date_str = str(date_val)[:10] # fallback
    else:
        date_str = str(date_val)
        
    return f"{reactor} / {cause} / {date_str}"

tick_labels = top_10.apply(format_label, axis=1)

# Create plot
fig, ax = plt.subplots(figsize=(12, 8))

bars = ax.barh(range(len(top_10)), top_10['정지시간(분)'], color='steelblue')

# Invert y-axis so the longest downtime is at the top
ax.invert_yaxis()

# Set ticks and labels
ax.set_yticks(range(len(top_10)))
ax.set_yticklabels(tick_labels)

# Add value labels on bars
for bar, duration in zip(bars, top_10['정지시간(분)']):
    width = bar.get_width()
    label_x_pos = width + max(top_10['정지시간(분)']) * 0.01 # Small offset
    ax.text(label_x_pos, bar.get_y() + bar.get_height()/2, f'{int(width)} 분', 
            va='center', ha='left', fontsize=9)

# Labels and Title
ax.set_xlabel('정지 시간 (분)', fontsize=12)
ax.set_ylabel('') # No ylabel needed since info is in tick labels
ax.set_title('최장 정지 이벤트 Top 10', fontsize=14, pad=15)

# Grid
ax.xaxis.grid(True, linestyle='--', alpha=0.7)
ax.set_axisbelow(True)

# Layout adjustment to prevent label cutoff
plt.tight_layout()

# Save figure
output_file = os.path.join(OUT_DIR, "top10_downtime.png")
plt.savefig(output_file, dpi=300, bbox_inches='tight')
plt.close(fig)

print(f"Plot saved to {output_file}")
