import pandas as pd
import matplotlib.pyplot as plt
import os

# Ensure output directory exists
OUT_DIR = "out/t1"
os.makedirs(OUT_DIR, exist_ok=True)

# Set font for Korean text
plt.rcParams["font.family"] = "Noto Sans CJK KR"

# Load data
file_path = "data/run_log.xlsx"
df = pd.read_excel(file_path, sheet_name="런로그")

# Clean column names by stripping whitespace to ensure consistent matching
df.columns = df.columns.str.strip()

# Identify the correct column name for CNT yield
yield_col = None
for col in df.columns:
    if "CNT수율" in col:
        yield_col = col
        break

if yield_col is None:
    raise ValueError("Could not find CNT yield column in dataframe")

# Ensure the yield column is numeric (convert errors to NaN)
df[yield_col] = pd.to_numeric(df[yield_col], errors='coerce')

# Calculate average yield per worker
worker_yield = df.groupby("작업자")[yield_col].mean().reset_index()
worker_yield.columns = ["작업자", "평균 수율"]

# Sort by yield descending and take top 5
top_5_workers = worker_yield.sort_values(by="평균 수율", ascending=False).head(5)

# Plotting horizontal bar chart
fig, ax = plt.subplots(figsize=(10, 6))
bars = ax.barh(top_5_workers["작업자"], top_5_workers["평균 수율"], color="skyblue", edgecolor="black")

# Add labels to bars
for bar in bars:
    width = bar.get_width()
    ax.text(width + 0.2, bar.get_y() + bar.get_height()/2., f'{width:.2f}', 
            ha='left', va='center', fontsize=10)

# Formatting
ax.set_xlabel(f"평균 CNT 수율 ({yield_col.split('(')[-1].strip(')') if '(' in yield_col else 'g/g-cat'})", fontsize=12)
ax.set_title("작업자별 평균 수율 상위 5명", fontsize=14, pad=10)
ax.invert_yaxis()  # To have the highest value at the top
ax.grid(axis="x", linestyle="--", alpha=0.7)

# Save figure
output_file = os.path.join(OUT_DIR, "worker_top5_yield.png")
plt.tight_layout()
plt.savefig(output_file, dpi=300)
plt.close()
