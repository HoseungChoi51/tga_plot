import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import os

# 설정
DATA_FILE = "/home/chs/Work/tga_plot/eval/inputs_b/polymers.xlsx"
OUT_DIR = "/home/chs/Work/tga_plot/eval/results/runs/sx/R-mpl-plain/B19_r1/out"
SHEET_NAME = "PVC"

# 한글 폰트 설정
plt.rcParams['font.family'] = 'Noto Sans CJK KR'
plt.rcParams['axes.unicode_minus'] = False

# 데이터 로드
df = pd.read_excel(DATA_FILE, sheet_name=SHEET_NAME)

# 필요한 컬럼 추출 (Temperature, Weight)
temp_col = 'Temperature (°C)'
weight_col = 'Weight (%)'

# 200도에서 400도 사이의 데이터 필터링
mask = (df[temp_col] >= 200) & (df[temp_col] <= 400)
df_range = df[mask].copy()

if df_range.empty:
    raise ValueError("200~400 °C 구간에 데이터가 없습니다.")

# 질량 감소량 계산
# 가장 낮은 온도(200도에 가까운 점)의 무게와 가장 높은 온도(400도에 가까운 점)의 무게 차이
# TGA에서는 보통 구간 시작점과 끝점의 무게 차이를 감소량으로 봅니다.
w_start = df_range.iloc[0][weight_col]
w_end = df_range.iloc[-1][weight_col]
mass_loss = w_start - w_end

print(f"PVC 200-400°C Mass Loss: {mass_loss:.2f}%")

# 그래프 그리기 준비
fig, ax1 = plt.subplots(figsize=(10, 6))

# 전체 데이터로 TG 곡선 그리기 (맥락 파악용)
ax1.plot(df[temp_col], df[weight_col], color='black', label='TG Curve (PVC)', linewidth=2)
ax1.set_xlabel('Temperature (°C)', fontsize=12)
ax1.set_ylabel('Weight (%)', color='black', fontsize=12)
ax1.tick_params(axis='y', labelcolor='black')
ax1.grid(True, linestyle='--', alpha=0.5)

# DTG 데이터가 있다면 우측 축에 표시 (선택사항이지만 일반적으로 함께 보임)
# 여기서는 요청이 질량 감소량 표시이므로 TG 곡선에 초점을 맞춤
# 하지만 시각적 명확성을 위해 200-400 구간을 강조

# 200-400 구간 강조
ax1.fill_between(df_range[temp_col], df_range[weight_col], 0, color='orange', alpha=0.3, label=f'200-400°C Region')

# 질량 감소량을 나타내는 화살표 또는 텍스트 추가
# 그래프 상단에 결과를 명시하는 것이 가장 명확함
text_str = f'Mass Loss (200-400°C): {mass_loss:.2f}%'
ax1.text(0.05, 0.95, text_str, transform=ax1.transAxes, 
         verticalalignment='top', horizontalalignment='left',
         bbox=dict(boxstyle='round,pad=0.5', facecolor='yellow', alpha=0.8),
         fontsize=12, fontweight='bold')

# 참고선을 200도와 400도에 그림
ax1.axvline(x=200, color='gray', linestyle=':', linewidth=1.5)
ax1.axvline(x=400, color='gray', linestyle=':', linewidth=1.5)
ax1.text(200, 105, '200°C', rotation=90, va='bottom', ha='center', fontsize=10)
ax1.text(400, 105, '400°C', rotation=90, va='bottom', ha='center', fontsize=10)

# 범례
ax1.legend(loc='lower left')
ax1.set_title(f'TGA of PVC with Mass Loss Calculation (200-400°C)', fontsize=14)

# 저장
os.makedirs(OUT_DIR, exist_ok=True)
output_path = os.path.join(OUT_DIR, 'pvc_mass_loss_200_400.png')
plt.tight_layout()
plt.savefig(output_path, dpi=300)
plt.close()

print(f"Figure saved to {output_path}")
