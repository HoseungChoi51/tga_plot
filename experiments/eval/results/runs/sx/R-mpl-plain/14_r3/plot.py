import pandas as pd
import matplotlib.pyplot as plt
import os

# Set Korean font
plt.rcParams['font.family'] = 'Noto Sans CJK KR'
plt.rcParams['axes.unicode_minus'] = False

# Define paths
DATA_FILE = "/home/chs/Work/tga_plot/tests/inputs/korean_excel.csv"
OUT_DIR = "/home/chs/Work/tga_plot/eval/results/runs/sx/R-mpl-plain/14_r3/out"

# Ensure output directory exists
os.makedirs(OUT_DIR, exist_ok=True)

# Read data with appropriate encoding (likely CP949 or EUC-KR for Korean Windows CSVs)
try:
    df = pd.read_csv(DATA_FILE, encoding='utf-8')
except UnicodeDecodeError:
    try:
        df = pd.read_csv(DATA_FILE, encoding='cp949')
    except UnicodeDecodeError:
        df = pd.read_csv(DATA_FILE, encoding='euc-kr')

# Identify columns based on the preview info
# Columns: "시간(분)", "온도(°C)", "무게(%)", "미분무게(%/°C)"
x_col = "온도(°C)"
y1_col = "무게(%)"
y2_col = "미분무게(%/°C)"

# Create figure and axis
fig, ax1 = plt.subplots(figsize=(10, 6))

# Plot Weight (%) on primary y-axis (left)
color1 = 'tab:blue'
ax1.set_xlabel('온도 (°C)', fontsize=12)
ax1.set_ylabel('무게 (%)', color=color1, fontsize=12)
line1 = ax1.plot(df[x_col], df[y1_col], color=color1, label='무게 (%)')
ax1.tick_params(axis='y', labelcolor=color1)
ax1.grid(True, linestyle='--', alpha=0.5)

# Create secondary y-axis for Derivative Weight (%/°C)
ax2 = ax1.twinx()
color2 = 'tab:red'
ax2.set_ylabel('미분무게 (%/°C)', color=color2, fontsize=12)
line2 = ax2.plot(df[x_col], df[y2_col], color=color2, linestyle='--', label='미분무게 (%/°C)')
ax2.tick_params(axis='y', labelcolor=color2)

# Title
plt.title('TGA 분석 결과 (korean_excel.csv)', fontsize=14)

# Combine legends from both axes
lines = line1 + line2
labels = [l.get_label() for l in lines]
ax1.legend(lines, labels, loc='upper right')

# Adjust layout to prevent clipping
plt.tight_layout()

# Save as PNG
png_path = os.path.join(OUT_DIR, "tga_plot.png")
plt.savefig(png_path, dpi=300, bbox_inches='tight')

# Save as PDF
pdf_path = os.path.join(OUT_DIR, "tga_plot.pdf")
plt.savefig(pdf_path, format='pdf', bbox_inches='tight')

print(f"Saved plots to:\n{png_path}\n{pdf_path}")
