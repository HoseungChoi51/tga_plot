import pandas as pd
import matplotlib.pyplot as plt
import os

# 설정
OUT_DIR = "out/t3"
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

# 주차와 반응기 기준으로 총 생산량 집계
# groupby 후 sum하여 각 주차별 각 반응기의 누적 생산량을 구함
pivot_df = df.groupby([week_col, reactor_col])['총생산량_kg'].sum().reset_index()

# 선그래프 그리기
fig, ax = plt.subplots(figsize=(10, 6))

# 반응기별로 색상 구분하여 선 그리기
colors = plt.cm.tab10.colors
for i, reactor in enumerate(sorted(pivot_df[reactor_col].unique())):
    subset = pivot_df[pivot_df[reactor_col] == reactor]
    # x축: 주차, y축: 해당 주차의 총 생산량(kg)
    ax.plot(subset[week_col], subset['총생산량_kg'], 
            marker='o', linestyle='-', linewidth=2, label=f'{reactor}', color=colors[i % len(colors)])

ax.set_xlabel('주차', fontsize=12)
ax.set_ylabel('주차별 총 생산량 (kg)', fontsize=12)
ax.set_title('주차별 반응기별 총 생산량 추이', fontsize=14, pad=15)

# x축 눈금 간격 조정 (주차가 많으면 일부만 표시하거나 회전)
ax.tick_params(axis='x', rotation=45)

# 범례 추가
ax.legend(title='반응기', loc='best')

# 격자 표시
ax.grid(True, linestyle='--', alpha=0.6)

plt.tight_layout()

# 저장
save_path = os.path.join(OUT_DIR, "weekly_production_trend_line.png")
plt.savefig(save_path, dpi=300, bbox_inches='tight')
plt.close(fig)
