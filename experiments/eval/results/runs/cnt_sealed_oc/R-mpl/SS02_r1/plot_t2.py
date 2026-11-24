import pandas as pd
import matplotlib.pyplot as plt
import os

# 설정
plt.rcParams["font.family"] = "Noto Sans CJK KR"
OUT_DIR = "out/t2"
os.makedirs(OUT_DIR, exist_ok=True)

# 데이터 읽기
file_path = "data/downtime.xlsx"
df = pd.read_excel(file_path, sheet_name="정지이력")

# 원인별 건수 계산 (결측치는 제외하고 카운트)
cause_counts = df['원인'].value_counts()

# 파이 차트 그리기
plt.figure(figsize=(10, 8))
colors = plt.cm.Set3.colors  # 색상이 구분되도록 설정

wedges, texts, autotexts = plt.pie(
    cause_counts.values, 
    labels=cause_counts.index, 
    autopct='%1.1f%%', 
    startangle=90,
    colors=colors,
    textprops={'fontsize': 12}
)

# 제목 및 레이아웃 설정
plt.title('설비 정지 원인별 비율', fontsize=16)
plt.axis('equal')  # 원형 유지
plt.tight_layout()

# 저장
output_file = os.path.join(OUT_DIR, "downtime_cause_pie.png")
plt.savefig(output_file, dpi=300)
plt.close()
