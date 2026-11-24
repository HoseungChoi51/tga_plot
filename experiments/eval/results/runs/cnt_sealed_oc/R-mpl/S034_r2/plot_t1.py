import pandas as pd
import matplotlib.pyplot as plt
import os

# 환경 설정
OUT_DIR = "out/t1"
os.makedirs(OUT_DIR, exist_ok=True)
plt.rcParams["font.family"] = "Noto Sans CJK KR"
plt.rcParams["axes.unicode_minus"] = False

# 데이터 로드
file_path = "data/run_log.xlsx"
try:
    df = pd.read_excel(file_path, sheet_name='런로그')
except Exception as e:
    print(f"Error reading file: {e}")
    exit()

# 컬럼명 매칭 로직 추가 (공백이나 특수문자 차이 대응)
cols = df.columns.tolist()

def find_col(keyword):
    """컬럼명에 keyword가 포함된 첫 번째 컬럼을 반환"""
    for c in cols:
        if keyword in str(c):
            return c
    return None

x_col = find_col('2존온도')
y_col = find_col('CNT수율')
reactor_col = find_col('반응기')

if x_col is None or y_col is None:
    raise ValueError(f"필요한 컬럼을 찾을 수 없습니다. x_col={x_col}, y_col={y_col}")

# 그래프 생성
fig, ax = plt.subplots(figsize=(10, 6))

# 반응기별 색상 정의
colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728'] # R1, R2, R3, R4 순서로 가정
reactors = ['R1', 'R2', 'R3', 'R4']

for i, reactor in enumerate(reactors):
    subset = df[df[reactor_col] == reactor][[x_col, y_col]].dropna()
    if not subset.empty:
        ax.scatter(subset[x_col], subset[y_col], 
                   color=colors[i], 
                   label=f'반응기 {reactor}', 
                   alpha=0.6, 
                   s=50, 
                   edgecolors='w',
                   linewidth=0.5)

# 축 레이블 및 제목
ax.set_xlabel(x_col, fontsize=12)
ax.set_ylabel(y_col, fontsize=12)
ax.set_title('2존 온도와 CNT 수율의 상관관계 분석', fontsize=14, pad=15)

# 그리드 추가
ax.grid(True, linestyle='--', alpha=0.7)

# 범례 위치 지정
ax.legend(title='구분', loc='best', frameon=True, fancybox=True, shadow=True)

# 레이아웃 조정
plt.tight_layout()

# 저장
save_path = os.path.join(OUT_DIR, 'temperature_vs_yield_scatter.png')
plt.savefig(save_path, dpi=300)
print(f"Graph saved to {save_path}")

plt.close(fig)
