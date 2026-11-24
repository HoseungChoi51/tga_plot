import pandas as pd
import matplotlib.pyplot as plt
import os

# 설정
OUT_DIR = "out/t1"
os.makedirs(OUT_DIR, exist_ok=True)

# 한글 폰트 설정
plt.rcParams["font.family"] = "Noto Sans CJK KR"
plt.rcParams["axes.unicode_minus"] = False

# 데이터 읽기
file_path = "data/downtime.xlsx"
df = pd.read_excel(file_path, sheet_name='정지이력')

# 정지시간(분) 컬럼명 확인 및 처리 (공백 제거 등)
time_col = '정지시간(분)'
reactor_col = '반응기'

# 반응기별 총 정지 시간 합산
total_downtime = df.groupby(reactor_col)[time_col].sum().sort_values(ascending=False)

# 막대 그래프 그리기
fig, ax = plt.subplots(figsize=(10, 6))

# 색상 지정: 가장 큰 값은 빨간색, 나머지는 회색
max_val = total_downtime.iloc[0]
colors = ['red' if val == max_val else 'gray' for val in total_downtime]

bars = ax.barh(total_downtime.index.astype(str), total_downtime.values, color=colors)

# 막대에 값 표시
for bar in bars:
    width = bar.get_width()
    label_y_pos = bar.get_y() + bar.get_height()/2
    ax.text(width, label_y_pos, f'{int(width):,} 분', ha='left', va='center', fontsize=9)

# 축 라벨 및 제목
ax.set_xlabel('총 정지 시간 (분)')
ax.set_ylabel('반응기')
ax.set_title('반응기별 총 설비 정지시간')

# y축 방향을 위에서 아래로 내림차순으로 유지하기 위해 반전 (barh는 기본이 아래에서 위로 올라감)
ax.invert_yaxis()

# 레이아웃 조정
plt.tight_layout()

# 저장
save_path = os.path.join(OUT_DIR, "downtime_by_reactor.png")
plt.savefig(save_path, dpi=300)
plt.close()
