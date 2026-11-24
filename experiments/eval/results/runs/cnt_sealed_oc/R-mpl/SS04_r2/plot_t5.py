import pandas as pd
import matplotlib.pyplot as plt
import os
import numpy as np

# 설정
OUT_DIR = "out/t5"
os.makedirs(OUT_DIR, exist_ok=True)
plt.rcParams["font.family"] = "Noto Sans CJK KR"
plt.rcParams["axes.unicode_minus"] = False

# 데이터 읽기
file_path = "data/run_log.xlsx"
sheet_name = "런로그"
df = pd.read_excel(file_path, sheet_name=sheet_name)

# 열 이름 확인 및 매핑
cols = df.columns.tolist()
week_col = None
prod_col = None
time_col = None
reactor_col = None

for c in cols:
    if '주차' in str(c):
        week_col = c
    if '생산속도' in str(c):
        prod_col = c
    if '가동시간' in str(c):
        time_col = c
    if '반응기' in str(c):
        reactor_col = c

if not all([week_col, prod_col, time_col, reactor_col]):
    raise ValueError(f"필수 컬럼을 찾을 수 없습니다. Found columns: {cols}")

# 생산량 계산 (kg 단위 변환용 g -> kg)
df['생산속도_g_h'] = pd.to_numeric(df[prod_col], errors='coerce')
df['가동시간_h'] = pd.to_numeric(df[time_col], errors='coerce')
df['총생산량_g'] = df['생산속도_g_h'] * df['가동시간_h']
df['총생산량_kg'] = df['총생산량_g'] / 1000.0

# R3 반응기만 필터링
df_r3 = df[df[reactor_col] == 'R3'].copy()

# 주차별 총 생산량 집계 (R3 전용)
weekly_r3_production = df_r3.groupby(week_col)['총생산량_kg'].sum().reset_index()

# 평균선 계산을 위한 값 (전체 주차에 대한 평균 또는 해당 구간 평균? 보통 '평균선'은 전체 데이터셋의 평균을 의미함)
avg_production = weekly_r3_production['총생산량_kg'].mean()

# 선그래프 그리기
fig, ax = plt.subplots(figsize=(10, 6))

# R3 선 그리기
ax.plot(weekly_r3_production[week_col], weekly_r3_production['총생산량_kg'], 
        marker='o', linestyle='-', linewidth=2, label='R3', color='#ff7f0e') # tab10 중 orange 계열 사용

# R3 평균선 추가 (점선으로 표시하여 구분)
ax.axhline(y=avg_production, color='blue', linestyle='--', linewidth=2, label=f'R3 평균 ({avg_production:.2f} kg)')

ax.set_xlabel('주차', fontsize=12)
ax.set_ylabel('주차별 총 생산량 (kg)', fontsize=12)
ax.set_title('주차별 R3 반응기 총 생산량 추이 (평균선 포함)', fontsize=14, pad=15)

# y축 범위 조정 요청: 0~6
ax.set_ylim(0, 6)

# x축 눈금 간격 조정
ax.tick_params(axis='x', rotation=45)

# 범례 추가
ax.legend(title='구분', loc='best')

# 격자 표시
ax.grid(True, linestyle='--', alpha=0.6)

plt.tight_layout()

# 저장
save_path = os.path.join(OUT_DIR, "weekly_production_trend_line_R3_only_with_avg.png")
plt.savefig(save_path, dpi=300, bbox_inches='tight')
plt.close(fig)
