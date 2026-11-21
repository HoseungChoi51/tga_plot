import pandas as pd
import matplotlib.pyplot as plt
import os

# 환경 설정
OUT_DIR = "out/t1"
os.makedirs(OUT_DIR, exist_ok=True)

# 한글 폰트 설정
plt.rcParams["font.family"] = "Noto Sans CJK KR"
plt.rcParams["axes.unicode_minus"] = False

# 데이터 읽기
file_path = "data/run_log.xlsx"
sheet_name = "런로그"
df = pd.read_excel(file_path, sheet_name=sheet_name)

# 로트별 런 수 집계
lot_counts = df['촉매로트'].value_counts().sort_index()

# 막대 차트 생성
fig, ax = plt.subplots(figsize=(10, 6))
bars = ax.bar(lot_counts.index, lot_counts.values, color='skyblue', edgecolor='black')

# 라벨 및 제목 설정
ax.set_title('촉매 로트별 런 수', fontsize=14)
ax.set_xlabel('촉매 로트', fontsize=12)
ax.set_ylabel('런 수 (개)', fontsize=12)

# x축 레이블 회전 방지 및 정렬
ax.tick_params(axis='x', rotation=0)

# 각 막대 위에 값 표시
for bar in bars:
    height = bar.get_height()
    ax.text(bar.get_x() + bar.get_width()/2., height,
            f'{int(height)}',
            ha='center', va='bottom', fontsize=10)

plt.tight_layout()

# 파일 저장
output_file = os.path.join(OUT_DIR, "cnt_lot_run_count.png")
plt.savefig(output_file, dpi=300)
plt.close()
