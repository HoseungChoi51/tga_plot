import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import os

# 설정
plt.rcParams["font.family"] = "Noto Sans CJK KR"
OUT_DIR = "out/t2"
os.makedirs(OUT_DIR, exist_ok=True)

# 데이터 로드
file_path = "data/tga_batches.xlsx"
sheet_name = "R3-260428-1"
df = pd.read_excel(file_path, sheet_name=sheet_name)

# 열 이름 확인 및 매핑 (미리보기 기준: A 시간, B 온도, C 중량, D 미분중량)
cols = df.columns.tolist()
temp_col = None
weight_col = None
dwt_col = None

for c in cols:
    if '온도' in str(c):
        temp_col = c
    elif '중량 (%)' in str(c) or ('중량' in str(c) and '%' in str(c)):
        weight_col = c
    elif '미분중량' in str(c) or 'DTG' in str(c).upper():
        dwt_col = c

# 만약 정확한 열 이름을 찾지 못하면 위치 기반으로 시도
if temp_col is None: temp_col = cols[1] # 보통 두번째가 온도
if weight_col is None: weight_col = cols[2] # 보통 세번째가 중량
if dwt_col is None: dwt_col = cols[3] # 보통 네번째가 미분중량

# 데이터 정제 (NaN 제거)
df_plot = df[[temp_col, weight_col, dwt_col]].dropna()
x_temp = df_plot[temp_col].values
y_weight = df_plot[weight_col].values
y_dwt = df_plot[dwt_col].values

# 그래프 그리기
fig, ax1 = plt.subplots(figsize=(10, 6))

# TG 곡선 (좌측 Y축: 중량 %)
color1 = 'tab:blue'
ax1.set_xlabel('온도 (°C)', fontsize=12)
ax1.set_ylabel('중량 (%)', color=color1, fontsize=12)
line1 = ax1.plot(x_temp, y_weight, color=color1, label='TG')[0]
ax1.tick_params(axis='y', labelcolor=color1)
ax1.grid(True, linestyle='--', alpha=0.5)

# DTG 곡선 (우측 Y축: 미분중량 %/°C)
ax2 = ax1.twinx()
color2 = 'tab:red'
ax2.set_ylabel('미분중량 (%/°C)', color=color2, fontsize=12)
line2 = ax2.plot(x_temp, y_dwt, color=color2, label='DTG')

# plot 반환값은 리스트이므로 인덱싱으로 접근하거나 언팩 처리 시 주의 필요
line2_obj = ax2.plot(x_temp, y_dwt, color=color2, label='DTG')[0]
ax2.tick_params(axis='y', labelcolor=color2)

# 범례 추가
lines = [line1, line2_obj]
labels = [l.get_label() for l in lines]
ax1.legend(lines, labels, loc='center right')

plt.title(f'TGA 분석 결과 ({sheet_name})', fontsize=14)
fig.tight_layout()

# 저장
save_path = os.path.join(OUT_DIR, f'tg_dtg_curve_{sheet_name}.png')
plt.savefig(save_path, dpi=300, bbox_inches='tight')
plt.close()
