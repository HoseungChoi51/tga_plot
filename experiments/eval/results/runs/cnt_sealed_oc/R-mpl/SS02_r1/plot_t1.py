import pandas as pd
import matplotlib.pyplot as plt
import os

# 설정
plt.rcParams["font.family"] = "Noto Sans CJK KR"
OUT_DIR = "out/t1"
os.makedirs(OUT_DIR, exist_ok=True)

# 데이터 읽기
file_path = "data/downtime.xlsx"
df = pd.read_excel(file_path, sheet_name="정지이력")

# 원인별 건수 계산 (결측치는 제외하고 카운트)
cause_counts = df['원인'].value_counts()

# 그래프 그리기
plt.figure(figsize=(10, 6))
bars = plt.bar(cause_counts.index, cause_counts.values, color='skyblue', edgecolor='black')

# 막대 위에 값 표시
for bar in bars:
    height = bar.get_height()
    plt.text(bar.get_x() + bar.get_width() / 2., height,
             f'{int(height)}',
             ha='center', va='bottom')

# 레이블 및 제목 설정
plt.title('설비 정지 원인별 건수', fontsize=14)
plt.xlabel('정지 원인', fontsize=12)
plt.ylabel('건수', fontsize=12)
plt.xticks(rotation=45, ha='right')
plt.tight_layout()

# 저장
output_file = os.path.join(OUT_DIR, "downtime_cause_count.png")
plt.savefig(output_file, dpi=300)
plt.close()
