import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import os

# 설정
OUT_DIR = "out/t1"
os.makedirs(OUT_DIR, exist_ok=True)
plt.rcParams["font.family"] = "Noto Sans CJK KR"
plt.rcParams["axes.unicode_minus"] = False

# 데이터 읽기
file_path = "data/run_log.xlsx"
df = pd.read_excel(file_path, sheet_name='런로그')

# 컬럼명 정리: 공백 제거 및 불필요한 특수문자/공백 정규화하여 매칭 용이하게 함
original_cols = df.columns.tolist()
cleaned_cols = [col.strip().replace('  ', ' ') for col in original_cols]
df.columns = cleaned_cols

# 요청된 컬럼 이름과 실제 데이터의 유사한 컬럼 찾기 (부분 일치 활용)
# 생산속도 관련 컬럼 검색
prod_speed_col = None
for c in df.columns:
    if '생산속도' in c or 'Production Rate' in c.lower():
        prod_speed_col = c
        break

# C2H4 유량 관련 컬럼 검색
c2h4_flow_col = None
for c in df.columns:
    if 'C2H4' in c and ('유량' in c or 'Flow' in c):
        c2h4_flow_col = c
        break

# 반응기 컬럼 확인 (보통 '반응기'로 시작)
reactor_col = None
for c in df.columns:
    if '반응기' in c:
        reactor_col = c
        break

if not all([prod_speed_col, c2h4_flow_col, reactor_col]):
    raise ValueError(f"컬럼을 찾을 수 없습니다. 검색 결과: Prod={prod_speed_col}, Flow={c2h4_flow_col}, Reactor={reactor_col}. 전체 컬럼 목록: {df.columns.tolist()}")

# 필요한 컬럼 추출 및 결측치 제거
plot_df = df[[reactor_col, prod_speed_col, c2h4_flow_col]].dropna()

# 그래프 그리기
fig, ax = plt.subplots(figsize=(10, 7))

# 반응기별 색상 및 마커 매핑
colors = {'R1': '#e41a1c', 'R2': '#377eb8', 'R3': '#4daf4a', 'R4': '#984ea3'}
markers = {'R1': 'o', 'R2': 's', 'R3': '^', 'R4': 'D'}

# 유니크한 반응기 값 정렬하여 순서 보장
unique_reactors = sorted(plot_df[reactor_col].unique())

for reactor in unique_reactors:
    subset = plot_df[plot_df[reactor_col] == reactor]
    ax.scatter(subset[c2h4_flow_col], 
               subset[prod_speed_col], 
               label=reactor, 
               color=colors.get(reactor, 'gray'), 
               marker=markers.get(reactor, 'x'),
               alpha=0.7,
               edgecolors='k',
               linewidths=0.5,
               s=60)

# 축 라벨 및 제목
ax.set_xlabel(c2h4_flow_col, fontsize=12)
ax.set_ylabel(prod_speed_col, fontsize=12)
ax.set_title('생산 속도 vs C2H4 유량 (반응기별 분포)', fontsize=14)

# 격자선 추가
ax.grid(True, linestyle='--', alpha=0.6)

# 범례 위치
ax.legend(title='반응기', loc='best', fontsize=10)

# 레이아웃 조정
plt.tight_layout()

# 저장
save_path = os.path.join(OUT_DIR, "production_rate_vs_c2h4_flow.png")
plt.savefig(save_path, dpi=300, bbox_inches='tight')
plt.close(fig)

print(f"Plots saved to {save_path}")
