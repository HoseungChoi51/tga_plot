import pandas as pd
import matplotlib.pyplot as plt
import os

# 설정
OUT_DIR = "out/t1"
os.makedirs(OUT_DIR, exist_ok=True)
plt.rcParams["font.family"] = "Noto Sans CJK KR"
plt.rcParams["axes.unicode_minus"] = False

# 데이터 로드
file_path = "data/run_log.xlsx"
df = pd.read_excel(file_path, sheet_name="런로그")

# 컬럼명 확인 및 필요 컬럼만 추출 (공백 제거 포함 안전장치)
col_metal = [c for c in df.columns if "잔류금속" in str(c)][0]
col_oxidation = [c for c in df.columns if "산화개시온도" in str(c)][0]
col_reactor = [c for c in df.columns if "반응기" in str(c)][0]

# 결측치 처리 및 타입 변환
df_plot = df[[col_metal, col_oxidation, col_reactor]].dropna()
df_plot[col_metal] = pd.to_numeric(df_plot[col_metal], errors="coerce")
df_plot[col_oxidation] = pd.to_numeric(df_plot[col_oxidation], errors="coerce")
df_plot = df_plot.dropna()

# 산점도 그리기
fig, ax = plt.subplots(figsize=(10, 8))

# 반응기별 색상과 마커 지정
reactors = sorted(df_plot[col_reactor].unique())
colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728']
markers = ['o', 's', '^', 'D']

for i, reactor in enumerate(reactors):
    subset = df_plot[df_plot[col_reactor] == reactor]
    ax.scatter(subset[col_metal], 
               subset[col_oxidation], 
               label=f"{reactor}",
               color=colors[i % len(colors)],
               marker=markers[i % len(markers)],
               alpha=0.7,
               edgecolors='k',
               linewidths=0.5,
               s=50)

# 라벨 및 제목
ax.set_xlabel("잔류금속 (wt%)", fontsize=12)
ax.set_ylabel("산화개시온도 (°C)", fontsize=12)
ax.set_title("반응기별 잔류금속 vs 산화개시온도 산점도", fontsize=14, pad=10)

# 범례
ax.legend(title="반응기", loc="best", frameon=True)

# 격자
ax.grid(True, linestyle="--", alpha=0.6)

# 레이아웃 조정 및 저장
plt.tight_layout()
output_filename = os.path.join(OUT_DIR, "scatter_metal_vs_oxidation_temp.png")
plt.savefig(output_filename, dpi=300, bbox_inches='tight')
plt.close()
