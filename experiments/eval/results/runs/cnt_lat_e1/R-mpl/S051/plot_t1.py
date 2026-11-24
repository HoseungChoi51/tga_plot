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

# Clean column names: strip whitespace and remove potential unit parentheses if they cause issues, 
# but here we just ensure exact match or handle variations. 
# The error suggests the columns might have different names or spaces.
# Let's inspect and rename to standard keys for safety, or just use the exact strings from preview carefully.
# Preview says: N 체류시간 (s), Q CNT수율 (g/g-cat), P 가동시간 (h)
# Sometimes Excel headers have trailing spaces. Let's strip all column names.
df.columns = df.columns.str.strip()

# Ensure '주차' is numeric
df["주차"] = pd.to_numeric(df["주차"], errors="coerce")

# Filter: 주차 14-26 and 반응기 in {R1, R2}
filtered_df = df[(df["주차"] >= 14) & (df["주차"] <= 26) & (df["반응기"].isin(["R1", "R2"]))]

# Identify correct column names by checking what exists after stripping
col_residence = [c for c in filtered_df.columns if "체류시간" in c][0]
col_yield = [c for c in filtered_df.columns if "CNT수율" in c][0]
col_duration = [c for c in filtered_df.columns if "가동시간" in c][0]

# Drop rows with NaN in key columns for plotting
filtered_df = filtered_df.dropna(subset=[col_residence, col_yield, col_duration])

# Prepare plot
fig, ax = plt.subplots(figsize=(10, 7))

# Scatter plot: 체류시간 vs CNT수율, marker size proportional to 가동시간
# Scale marker sizes for visibility
sizes = filtered_df[col_duration] * 50  # Adjust multiplier for visual clarity

scatter = ax.scatter(
    filtered_df[col_residence],
    filtered_df[col_yield],
    s=sizes,
    c=filtered_df["반응기"],
    alpha=0.6,
    edgecolors="w",
    linewidth=0.5
)

# Add legend for reactors
handles, labels = scatter.legend_elements(prop="colors", alpha=0.6)
legend = ax.legend(handles, labels, title="반응기", loc="best")

# Labels and title
ax.set_xlabel(col_residence)
ax.set_ylabel(col_yield)
ax.set_title("주차 14–26, R1/R2: 체류시간 vs CNT수율 (마커 크기 ∝ 가동시간)")

# Grid
ax.grid(True, linestyle="--", alpha=0.5)

# Save figure
output_path = os.path.join(OUT_DIR, "scatter_residence_yield.png")
plt.tight_layout()
plt.savefig(output_path, dpi=300)
plt.close()
