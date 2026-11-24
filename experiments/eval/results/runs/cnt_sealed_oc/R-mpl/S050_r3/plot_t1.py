import pandas as pd
import matplotlib.pyplot as plt
import os

# 설정
plt.rcParams["font.family"] = "Noto Sans CJK KR"
OUT_DIR = "out/t1"
os.makedirs(OUT_DIR, exist_ok=True)

# 데이터 로드
file_path = "data/run_log.xlsx"
sheet_name = "런로그"
df = pd.read_excel(file_path, sheet_name=sheet_name)

# 컬럼 이름 확인 및 정리 (공백 제거 등)
df.columns = df.columns.str.strip()

# 필요한 컬럼 추출: 생산속도, C2H4유량, 반응기
# 헤더가 정확히 일치하지 않을 수 있으므로 contains 로 매칭하여 실제 컬럼명 확인
cols_to_find = ['생산속도', 'C2H4유량', '반응기']
actual_cols = []
for target in cols_to_find:
    matches = [col for col in df.columns if target in col]
    if matches:
        actual_cols.append(matches[0])
    else:
        raise ValueError(f"Column containing '{target}' not found. Available: {df.columns.tolist()}")

prod_col = next(c for c in actual_cols if '생산속도' in c)
c2h4_col = next(c for c in actual_cols if 'C2H4' in c)
reactor_col = next(c for c in actual_cols if '반응기' in c)

plot_df = df[[prod_col, c2h4_col, reactor_col]].dropna()

# 플롯 그리기
fig, ax = plt.subplots(figsize=(10, 6))

# 반응기별로 색상 지정하여 산점도绘制
reactors = plot_df[reactor_col].unique()
colors = {'R1': '#1f77b4', 'R2': '#ff7f0e', 'R3': '#2ca02c', 'R4': '#d62728'}

for reactor in reactors:
    subset = plot_df[plot_df[reactor_col] == reactor]
    ax.scatter(subset[c2h4_col], 
               subset[prod_col], 
               label=f'{reactor}', 
               color=colors.get(reactor, None),
               alpha=0.7,
               s=50)

ax.set_xlabel('C2H4유량 (sccm)')
ax.set_ylabel('생산속도 (g/h)')
ax.set_title('생산속도 vs C2H4유량 (반응기별)')
ax.legend(title='반응기')
ax.grid(True, linestyle='--', alpha=0.6)

# 저장
output_file = os.path.join(OUT_DIR, "scatter_prod_speed_vs_c2h4_by_reactor.png")
plt.tight_layout()
plt.savefig(output_file, dpi=300)
plt.close()
