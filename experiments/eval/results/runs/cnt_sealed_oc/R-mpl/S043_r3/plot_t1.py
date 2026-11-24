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
df = pd.read_excel(file_path, sheet_name="런로그")

# 필요 열만 선택 및 데이터 정제
# 주차(C), 반응기(E), IG/ID(U)
cols_to_use = ['주차', '반응기', 'IG/ID']
df_plot = df[cols_to_use].dropna()

# IG/ID 컬럼이 문자열로 읽혔을 수 있으므로 숫자형으로 변환 시도
# 변환되지 않는 값은 NaN 처리
df_plot['IG/ID'] = pd.to_numeric(df_plot['IG/ID'], errors='coerce')
df_plot['주차'] = pd.to_numeric(df_plot['주차'], errors='coerce')

# NaN인 행 제거
df_plot = df_plot.dropna(subset=['IG/ID', '주차'])

# 피벗 테이블 생성: 행은 반응기(R1-R4), 열은 주차(1-26), 값은 IG/ID 평균
pivot_table = df_plot.pivot_table(values='IG/ID', index='반응기', columns='주차', aggfunc='mean')

# 반응기 순서 고정 (R1, R2, R3, R4)
reactor_order = ['R1', 'R2', 'R3', 'R4']
pivot_table = pivot_table.reindex(reactor_order)

# 그래프 그리기 (히트맵)
fig, ax = plt.subplots(figsize=(14, 5))

# seaborn이 없으므로 imshow 사용
im = ax.imshow(pivot_table.values, cmap='YlOrBr', aspect='auto')

# 눈금 레이블 설정
ax.set_xticks(np.arange(len(pivot_table.columns)))
ax.set_yticks(np.arange(len(pivot_table.index)))
ax.set_xticklabels(pivot_table.columns.astype(int)) # 주차를 정수로 표시
ax.set_yticklabels(pivot_table.index)

# 색상막 추가
cbar = ax.figure.colorbar(im, ax=ax)
cbar.ax.set_ylabel('IG/ID 비율', rotation=-90, va="bottom")

# 제목 및 라벨
ax.set_title("반응기별 주간 IG/ID 비율 히트맵", fontsize=16, pad=20)
ax.set_xlabel("주차", fontsize=12)
ax.set_ylabel("반응기", fontsize=12)

# 모든 셀에 값 표시 (선택적, 가독성을 위해 작은 글씨로)
for i in range(len(pivot_table.index)):
    for j in range(len(pivot_table.columns)):
        val = pivot_table.iloc[i, j]
        if not np.isnan(val):
            # 배경색에 따라 텍스트 색 결정 (어두우면 흰색, 밝으면 검은색)
            # 값의 범위 기준으로 상대적인 위치를 계산하여 색상 선택
            vmin, vmax = np.nanmin(pivot_table.values), np.nanmax(pivot_table.values)
            norm_val = (val - vmin) / (vmax - vmin + 1e-6)
            color = "white" if norm_val > 0.5 else "black"
            
            text = ax.text(j, i, f"{val:.2f}",
                           ha="center", va="center", color=color, fontsize=7)

plt.tight_layout()

# 저장
output_path = os.path.join(OUT_DIR, "heatmap_igid_by_reactor_week.png")
plt.savefig(output_path, dpi=300)
plt.close()
