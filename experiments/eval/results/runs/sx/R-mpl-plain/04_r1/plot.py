import pandas as pd
import matplotlib.pyplot as plt
import os

# 설정
DATA_FILE = "/home/chs/CNT/Plot/tests/inputs/TGA.xlsx"
OUT_DIR = "/home/chs/CNT/Plot/eval/results/runs/sx/R-mpl-plain/04_r1/out"
SHEET_NAME = "1006R1-V normal"

# 한글 폰트 설정
plt.rcParams['font.family'] = 'Noto Sans CJK KR'
plt.rcParams['axes.unicode_minus'] = False

# 데이터 읽기
df = pd.read_excel(DATA_FILE, sheet_name=SHEET_NAME)

# TGA 플롯 생성
fig, ax1 = plt.subplots(figsize=(10, 6))

# Weight(%) - 왼쪽 Y축
color1 = 'tab:blue'
ax1.set_xlabel('Temperature (°C)', fontsize=12)
ax1.set_ylabel('Weight (%)', color=color1, fontsize=12)
line1 = ax1.plot(df['Temperature'], df['Weight(%)'], color=color1, label='Weight (%)')
ax1.tick_params(axis='y', labelcolor=color1)

# D.W(%/C) - 오른쪽 Y축
ax2 = ax1.twinx()
color2 = 'tab:red'
ax2.set_ylabel('D.W (%/°C)', color=color2, fontsize=12)
line2 = ax2.plot(df['Temperature'], df['D.W(%/C)'], color=color2, linestyle='--', label='D.W (%/°C)')
ax2.tick_params(axis='y', labelcolor=color2)

# 제목 설정: 글자 크기 18, 색깔 남색(navy)
ax1.set_title('CNT 산화 거동', fontsize=18, color='navy')

# 범례 추가
lines = line1 + line2
labels = [l.get_label() for l in lines]
ax1.legend(lines, labels, loc='upper right')

# 레이아웃 조정 및 저장
fig.tight_layout()
os.makedirs(OUT_DIR, exist_ok=True)
output_path = os.path.join(OUT_DIR, "TGA_normal.png")
plt.savefig(output_path, dpi=300)
plt.close()
