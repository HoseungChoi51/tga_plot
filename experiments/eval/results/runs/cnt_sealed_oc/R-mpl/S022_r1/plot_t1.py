import pandas as pd
import matplotlib.pyplot as plt
import os

# 설정
OUT_DIR = "out/t1"
os.makedirs(OUT_DIR, exist_ok=True)

plt.rcParams["font.family"] = "Noto Sans CJK KR"
plt.rcParams["axes.unicode_minus"] = False

# 데이터 읽기
file_path = "data/run_log.xlsx"
df = pd.read_excel(file_path, sheet_name="런로그")

# 필요한 컬럼 확인 (잔류금속, 산화개시온도, 반응기)
# 컬럼명이 정확히 매칭되지 않을 수 있으므로 유사한 이름으로 검색하거나 직접 지정
# 미리보기 기준으로: S 잔류금속 (wt%), T 산화개시온도 (°C), E 반응기
col_yield_metal = "잔류금속 (wt%)" # 실제 엑셀 헤더가 스페이스 포함 가능성 높음
col_oxidation_temp = "산화개시온도 (°C)"
col_reactor = "반응기"

# 만약 헤더에 공백이 없는 경우 등을 대비하여 정규화할 수도 있으나, 
# 미리보기 표기법을 그대로 따르는 것이 안전합니다.
# 일부 시스템에서는 '잔류금속(wt%)' 처럼 공백이 없을 수도 있음.
#稳健을 위해 find를 통해 실제 컬럼명을 찾습니다.
def find_col(df, keywords):
    for col in df.columns:
        if all(kw in str(col) for kw in keywords):
            return col
    return None

col_res_metal = find_col(df, ["잔류금속"])
col_oxi_temp = find_col(df, ["산화개시", "온도"])
col_react = find_col(df, ["반응기"])

if col_res_metal is None or col_oxi_temp is None or col_react is None:
    raise ValueError("컬럼을 찾을 수 없습니다.")

# 플롯 그리기
fig, ax = plt.subplots(figsize=(10, 7))

reactors = sorted(df[col_react].dropna().unique())
colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728'] # R1~R4 색상 예시
markers = ['o', 's', '^', 'D']

for i, r in enumerate(reactors):
    subset = df[df[col_react] == r]
    x_vals = subset[col_res_metal]
    y_vals = subset[col_oxi_temp]
    
    ax.scatter(x_vals, y_vals, label=f"{r}", color=colors[i % len(colors)], marker=markers[i % len(markers)], alpha=0.7, s=50)

ax.set_xlabel(f"{col_res_metal}")
ax.set_ylabel(f"{col_oxi_temp}")
ax.set_title("반응기별 잔류금속 vs 산화개시온도 산점도")
ax.legend(title="반응기")
ax.grid(True, linestyle='--', alpha=0.5)

plt.tight_layout()
save_path = os.path.join(OUT_DIR, "scatter_metal_vs_oxidation.png")
plt.savefig(save_path, dpi=300)
plt.close()
