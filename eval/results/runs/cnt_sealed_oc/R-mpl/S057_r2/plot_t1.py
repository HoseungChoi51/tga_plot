import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import os

# 설정
plt.rcParams["font.family"] = "Noto Sans CJK KR"
plt.rcParams["axes.unicode_minus"] = False
OUT_DIR = "out/t1"
os.makedirs(OUT_DIR, exist_ok=True)

# 데이터 로드
file_path = "data/run_log.xlsx"
sheet_name = "런로그"
df = pd.read_excel(file_path, sheet_name=sheet_name)

# 분석에 필요한 컬럼 선택
cols_of_interest = [
    '체류시간 (s)', 
    'H2/C2H4비', 
    '2존온도 (°C)', 
    '3존온도 (°C)', 
    '외기습도 (%)', 
    'CNT수율 (g/g-cat)', 
    '잔류금속 (wt%)', 
    '산화개시온도 (°C)', 
    'IG/ID'
]

# 존재하는 컬럼만 필터링하여 사용
available_cols = [c for c in cols_of_interest if c in df.columns]
if len(available_cols) == 0:
    # 만약 정확히 매칭되지 않으면 유사한 이름 찾기 시도 (예를 들어 공백 차이 등)
    # 하지만 미리보기 기준이므로 일단 진행
    pass

df_corr = df[available_cols].copy()

# 숫자로 변환할 수 없는 값(문자열 '-' 등)을 NaN으로 처리
for col in available_cols:
    df_corr[col] = pd.to_numeric(df_corr[col], errors='coerce')

# NaN인 행 제거 (상관관계 계산용)
df_corr = df_corr.dropna()

if df_corr.empty or len(df_corr) < 2:
    raise ValueError("Not enough valid data rows to compute correlation.")

# Pearson 상관관계 계산
corr_matrix = df_corr.corr(method='pearson')

# 히트맵 생성 (Matplotlib만으로 구현)
fig, ax = plt.subplots(figsize=(10, 8))

# Imshow로 히트맵 그리기
im = ax.imshow(corr_matrix.values, cmap='RdBu_r', vmin=-1, vmax=1)

# 눈금 위치와 레이블 설정
ax.set_xticks(np.arange(len(available_cols)))
ax.set_yticks(np.arange(len(available_cols)))
ax.set_xticklabels(available_cols)
ax.set_yticklabels(available_cols)

# X축 라벨 회전 및 정렬
plt.setp(ax.get_xticklabels(), rotation=45, ha="right", rotation_mode="anchor")

# 각 셀에 값 annotate
for i in range(len(available_cols)):
    for j in range(len(available_cols)):
        val = corr_matrix.iloc[i, j]
        # 배경색에 따라 글자색 결정
        # RdBu_r: 파랑(-1) -> 흰색(0) -> 빨강(1)
        # 절대값이 큰 경우 흰색 글자가 잘 보임
        color = "white" if abs(val) > 0.6 else "black"
        text = ax.text(j, i, f"{val:.2f}",
                       ha="center", va="center", color=color)

# 컬러바 추가
cbar = ax.figure.colorbar(im, ax=ax)
cbar.ax.set_ylabel('Correlation Coefficient', rotation=-90, va="bottom")

# 타이틀
ax.set_title("Pearson Correlation Heatmap of Process Parameters and Product Quality")

# 레이아웃 조정 및 저장
plt.tight_layout()
output_filename = os.path.join(OUT_DIR, "correlation_heatmap.png")
plt.savefig(output_filename, dpi=300, bbox_inches='tight')
plt.close()
