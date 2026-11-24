import pandas as pd
import matplotlib.pyplot as plt
import os

# 설정
OUT_DIR = "out/t1"
os.makedirs(OUT_DIR, exist_ok=True)

plt.rcParams["font.family"] = "Noto Sans CJK KR"
plt.rcParams["axes.unicode_minus"] = False

# 데이터 읽기
file_path = "data/run_log.xlsx"
sheet_name = "런로그"

try:
    df = pd.read_excel(file_path, sheet_name=sheet_name)
except Exception as e:
    print(f"Error reading file: {e}")
    exit()

# 작업자별 런 수 계산
worker_counts = df['작업자'].value_counts()

# 원그래프 그리기
fig, ax = plt.subplots(figsize=(10, 8))

# 비율이므로 pie chart 사용
wedges, texts, autotexts = ax.pie(
    worker_counts.values, 
    labels=worker_counts.index, 
    autopct='%1.1f%%',
    startangle=90,
    textprops={'fontsize': 12}
)

# 제목 및 축 레이블 설정
ax.set_title("작업자별 런 수행 비율", fontsize=16, pad=20)

# 그래프 모양을 동그랗게 유지
ax.axis('equal')

# 저장
output_filename = os.path.join(OUT_DIR, "worker_run_ratio_pie.png")
plt.tight_layout()
plt.savefig(output_filename, dpi=300)
plt.close()

print(f"Plot saved to {output_filename}")
