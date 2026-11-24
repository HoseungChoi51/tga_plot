import pandas as pd
import matplotlib.pyplot as plt
import os

# 설정
OUT_DIR = "out/t1"
os.makedirs(OUT_DIR, exist_ok=True)
plt.rcParams["font.family"] = "Noto Sans CJK KR"
plt.rcParams["axes.unicode_minus"] = False

# 데이터 읽기
file_path = "data/downtime.xlsx"
df = pd.read_excel(file_path, sheet_name="정지이력")

# 원인별 정지시간 합산 및 내림차순 정렬
downtime_by_cause = df.groupby("원인")["정지시간(분)"].sum().sort_values(ascending=False)

# 차트 그리기
fig, ax = plt.subplots(figsize=(10, 6))
bars = ax.bar(downtime_by_cause.index, downtime_by_cause.values, color="skyblue", edgecolor="black")

# 막대 위에 값 표시
for bar in bars:
    height = bar.get_height()
    ax.text(bar.get_x() + bar.get_width()/2., height,
            f'{int(height)}',
            ha='center', va='bottom', fontsize=10)

ax.set_title("원인별 총 정지 시간 (분)", fontsize=14)
ax.set_xlabel("원인", fontsize=12)
ax.set_ylabel("총 정지 시간 (분)", fontsize=12)
ax.tick_params(axis='x', rotation=0)
ax.grid(axis='y', linestyle='--', alpha=0.7)

plt.tight_layout()
output_path = os.path.join(OUT_DIR, "downtime_by_cause.png")
plt.savefig(output_path, dpi=300)
plt.close()
