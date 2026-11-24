import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import os

# 데이터 파일 경로와 출력 디렉토리 설정
DATA_FILE = "/home/chs/Work/tga_plot/eval/inputs_b/caox.csv"
OUT_DIR = "/home/chs/Work/tga_plot/eval/results/runs/sx/R-mpl-plain/B01_r3/out"

# 한글 폰트 설정
plt.rcParams['font.family'] = 'Noto Sans CJK KR'
plt.rcParams['axes.unicode_minus'] = False

# 데이터 읽기
df = pd.read_csv(DATA_FILE)

# 열 이름 확인 및 정리 (공백 제거 등)
df.columns = df.columns.str.strip()

# 필요한 열 추출
temp_col = "Temperature (°C)"
weight_col = "Weight (%)"

# 구간 정의: (시작 온도, 끝 온도, 라벨, 색상)
regions = [
    (120, 250, "H₂O", "#FFB6C1"),   # Light Pink
    (430, 580, "CO", "#ADD8E6"),    # Light Blue
    (640, 830, "CO₂", "#98FB98")    # Light Green
]

# 플롯 생성
fig, ax = plt.subplots(figsize=(10, 6))

# TGA 곡선 그리기 (질량 변화)
ax.plot(df[temp_col], df[weight_col], color='black', linewidth=1.5, label='TGA')

# 구간별 음영 칠하기 및 라벨 추가
for start, end, label, color in regions:
    # 해당 구간의 데이터 필터링
    mask = (df[temp_col] >= start) & (df[temp_col] <= end)
    
    if not mask.any():
        continue
        
    x_fill = df.loc[mask, temp_col]
    y_fill = df.loc[mask, weight_col]
    
    # 음영 채우기 (y=0부터가 아니라 곡선 아래까지 채우는 것이 일반적이지만, 
    # 여기서는 배경처럼 보이게 전체 높이 또는 특정 높이까지 채울 수 있음.
    # 보통 TGA 그래프에서 구간 강조는 배경에 색을 입히는 방식이 많음.
    # ax.fill_between을 사용하여 배경을 칠하되, 투명도를 낮게 설정하거나 밝은 색 사용)
    ax.axvspan(start, end, alpha=0.3, color=color, label=f'{label} Region')
    
    # 라벨 위치 계산: 구간의 중앙 X 좌표, Y 좌표는 현재 구간 내 최소 질량 근처나 고정된 상단 위치
    mid_x = (start + end) / 2
    
    # Y 위치는 가독성을 위해 그래프 상단에 고정하거나, 데이터의 평균값 위쪽에 배치
    # 여기서는 그래프의 상단 부분(예: 100% 근처)에 텍스트를 배치하여 간섭 최소화
    y_pos = 95 
    
    ax.text(mid_x, y_pos, label, ha='center', va='bottom', fontsize=12, fontweight='bold', color='black')

# 축 레이블 및 제목 설정
ax.set_xlabel('Temperature (°C)', fontsize=12)
ax.set_ylabel('Weight (%)', fontsize=12)
ax.set_title('TGA Curve with Decomposition Regions', fontsize=14)

# 범례 표시 (구간 색상 설명용)
# ax.legend(loc='lower left') # 필요 시 주석 해제

# 격자 표시
ax.grid(True, linestyle='--', alpha=0.6)

# 레이아웃 조정
plt.tight_layout()

# 출력 파일명 설정
output_filename = os.path.join(OUT_DIR, "tga_regions.png")

# 이미지 저장
plt.savefig(output_filename, dpi=300, bbox_inches='tight')

# 플롯 닫기
plt.close(fig)

print(f"Plot saved to {output_filename}")
