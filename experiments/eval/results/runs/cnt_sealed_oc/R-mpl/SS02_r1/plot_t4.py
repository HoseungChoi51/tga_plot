import pandas as pd
import matplotlib.pyplot as plt
import os

# 설정
plt.rcParams["font.family"] = "Noto Sans CJK KR"
OUT_DIR = "out/t4"
os.makedirs(OUT_DIR, exist_ok=True)

# 데이터 읽기
file_path = "data/downtime.xlsx"
df = pd.read_excel(file_path, sheet_name="정지이력")

# R2 반응기만 필터링
df_r2 = df[df['반응기'] == 'R2']

# 원인별 정지시간 합계 계산 (분 단위)
cause_sum = df_r2.groupby('원인')['정지시간(분)'].sum().sort_values(ascending=False)

# 파이 차트 그리기
plt.figure(figsize=(10, 8))
colors = plt.cm.Set3.colors

wedges, texts, autotexts = plt.pie(
    cause_sum.values, 
    labels=cause_sum.index, 
    autopct='%1.1f%%', 
    startangle=90,
    colors=colors,
    textprops={'fontsize': 12}
)

# 제목 및 레이아웃 설정
plt.title('R2 반응기 설비 정지 원인별 정지시간 비율', fontsize=16)
plt.axis('equal')
plt.tight_layout()

# 저장
output_file = os.path.join(OUT_DIR, "downtime_cause_pie_time_R2.png")
plt.savefig(output_file, dpi=300)
plt.close()
