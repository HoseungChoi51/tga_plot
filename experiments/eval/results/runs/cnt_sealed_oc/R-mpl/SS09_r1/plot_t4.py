import pandas as pd
import matplotlib.pyplot as plt
import os

# 설정
plt.rcParams["font.family"] = "Noto Sans CJK KR"
OUT_DIR = "out/t4"
os.makedirs(OUT_DIR, exist_ok=True)

# 데이터 읽기
file_path = "data/run_log.xlsx"
df = pd.read_excel(file_path, sheet_name="런로그")

# 열 이름 공백 제거 및 정리
df.columns = df.columns.str.strip()

# 필요한 컬럼 이름 찾기 (공백 variations 고려)
humidity_col = None
metal_col = None
reactor_col = None

for col in df.columns:
    if '외기습도' in col:
        humidity_col = col
    if '잔류금속' in col:
        metal_col = col
    if '반응기' in col:
        reactor_col = col

if humidity_col is None or metal_col is None or reactor_col is None:
    raise ValueError("Required columns (Humidity, Residual Metal, Reactor) not found.")

# 결측치 처리 및 수치형으로 강제 변환
plot_df = df[[humidity_col, metal_col, reactor_col]].copy()
plot_df[humidity_col] = pd.to_numeric(plot_df[humidity_col], errors='coerce')
plot_df[metal_col] = pd.to_numeric(plot_df[metal_col], errors='coerce')

# 변환 과정에서 생긴 NaN 제거
plot_df = plot_df.dropna(subset=[humidity_col, metal_col])

# 플롯팅: 반응기별 색상 구분 산점도
fig, ax = plt.subplots(figsize=(10, 8))

# 반응기 종류별로 다른 색상과 마커를 지정하여 시각적 구분을 명확히 함
reactors = plot_df[reactor_col].unique()
colors = ['tab:red', 'tab:blue', 'tab:green', 'tab:orange'] # R1~R4 순서 가정 또는 유니크 값 순서대로 매핑
markers = ['o', 's', '^', 'D']

for i, reactor in enumerate(reactors):
    subset = plot_df[plot_df[reactor_col] == reactor]
    # 색상이 부족하면 모듈로 연산으로 반복 사용 가능하지만, 여기서는 4종이므로 4개 색상 충분
    c_idx = i % len(colors)
    m_idx = i % len(markers)
    
    ax.scatter(
        subset[humidity_col], 
        subset[metal_col], 
        color=colors[c_idx], 
        marker=markers[m_idx], 
        label=f'{reactor} 반응기', 
        alpha=0.7, 
        edgecolors='w', 
        s=50
    )

# 축 설정
ax.set_xlabel(humidity_col)
ax.set_ylabel(metal_col)
ax.set_title('외기습도와 잔류금속의 상관관계 (반응기별)')
ax.grid(True, linestyle='--', alpha=0.5)
ax.legend(loc='best', title='반응기')

# 저장
output_file = os.path.join(OUT_DIR, "humidity_vs_metal_scatter_by_reactor.png")
plt.tight_layout()
plt.savefig(output_file, dpi=300)
plt.close()
