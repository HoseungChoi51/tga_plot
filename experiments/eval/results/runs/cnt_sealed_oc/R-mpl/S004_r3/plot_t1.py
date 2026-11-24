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

# Clean column names: remove leading/trailing spaces
df.columns = df.columns.str.strip()

# Identify correct column names for production speed and operating time
col_speed = None
col_time = None
col_grade = None

for c in df.columns:
    if '생산속도' in c:
        col_speed = c
    elif '가동시간' in c:
        col_time = c
    elif '등급' in c:
        col_grade = c

if not all([col_speed, col_time, col_grade]):
    raise ValueError("Required columns not found.")

# Convert necessary columns to numeric, coercing errors to NaN
df[col_speed] = pd.to_numeric(df[col_speed], errors='coerce')
df[col_time] = pd.to_numeric(df[col_time], errors='coerce')

# Drop rows where speed or time is NaN (cannot calculate production amount)
df_clean = df.dropna(subset=[col_speed, col_time])

# Calculate production amount (kg) per run
# Production Speed is in g/h, Operating Time is in h -> Product is in g
# Convert to kg by dividing by 1000
df_clean["생산량(kg)"] = df_clean[col_speed] * df_clean[col_time] / 1000.0

# Group by Grade and sum the production amount
grade_production = df_clean.groupby(col_grade)["생산량(kg)"].sum().reset_index()

# Prepare data for pie chart
labels = grade_production[col_grade].astype(str) # Ensure labels are strings
sizes = grade_production["생산량(kg)"]

# Create figure and axis
fig, ax = plt.subplots(figsize=(8, 6))

# Plot pie chart
wedges, texts, autotexts = ax.pie(sizes, labels=labels, autopct='%1.1f%%', startangle=90, colors=['#FF9999', '#66B2FF', '#FFCC66'])

# Style settings for better readability
ax.axis('equal')
plt.title('등급별 생산량 비중 (kg)', fontsize=14)

# Save plot
output_path = os.path.join(OUT_DIR, "grade_production_pie.png")
plt.savefig(output_path, dpi=300, bbox_inches='tight')
plt.close()
