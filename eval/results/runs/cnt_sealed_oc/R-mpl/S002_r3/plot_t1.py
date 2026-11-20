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
df = pd.read_excel(file_path, sheet_name='정지이력')

# 반응기별 총 정지시간 합산
total_downtime = df.groupby('반응기')['정지시간(분)'].sum().sort_values(ascending=False)

# plotting
fig, ax = plt.subplots(figsize=(10, 6))

colors = ['#FF0000' if i == 0 else '#808080' for i in range(len(total_downtime))]

bars = ax.barh(total_downtime.index, total_downtime.values, color=colors)

# 가로막대 차트에서 y축 레이블은 인덱스, x축 값은 길이
ax.set_xlabel("총 정지시간 (분)")
ax.set_ylabel("반응기")
ax.set_title("반응기별 총 설비 정지시간")

# 막대 끝에 수치 표시
for bar in bars:
    width = bar.get_width()
    ax.text(width + max(total_downtime)*0.01, 
            bar.get_y() + bar.get_height()/2.,
            f'{int(width)}', 
            va='center', 
            ha='left')

# 축 범위 조정
ax.set_xlim(0, max(total_downtime) * 1.15)

# 그리드 생략 또는 최소한으로 유지 (가로막대라 y축 눈금선만 보일 수 있음)
ax.grid(axis='x', linestyle='--', alpha=0.7)
ax.set_axisbelow(True)

# 저장
output_filename = os.path.join(OUT_DIR, "downtime_by_reactor.png")
plt.tight_layout()
plt.savefig(output_filename, dpi=300)
plt.close()
