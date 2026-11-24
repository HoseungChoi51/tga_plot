import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import os
from scipy import stats

# 설정
plt.rcParams["font.family"] = "Noto Sans CJK KR"
OUT_DIR = "out/t1"
os.makedirs(OUT_DIR, exist_ok=True)

# 데이터 로드
file_path = "data/run_log.xlsx"
df = pd.read_excel(file_path, sheet_name='런로그')

# 컬럼명 자동 매핑 함수: 실제 열 이름과 의도된 이름의 유사성을 기반으로 매칭
def find_column(df, target_str):
    for col in df.columns:
        if target_str in str(col):
            return col
    # 공백이나 특수문자 차이 가능성 대비하여 정규화 비교
    normalized_cols = {str(c).replace(' ', '').replace('(wt%)', '').replace('(', '').replace(')', ''): c for c in df.columns}
    normalized_target = target_str.replace(' ', '').replace('(wt%)', '').replace('(', '').replace(')', '')
    if normalized_target in normalized_cols:
        return normalized_cols[normalized_target]
    raise ValueError(f"Column containing '{target_str}' not found.")

# 필요한 컬럼 식별
try:
    grade_col = find_column(df, '등급')
    metal_col = find_column(df, '잔류금속')
    igid_col = find_column(df, 'IG/ID')
except ValueError as e:
    print("Error finding columns:", e)
    print("Available columns:", df.columns.tolist())
    raise

# 등급 C 런 제외
df_filtered = df[df[grade_col] != 'C'].copy()

# 결측치 제거 (필요한 컬럼만)
cols_needed = [metal_col, igid_col]
df_clean = df_filtered.dropna(subset=cols_needed)

x = df_clean[metal_col]
y = df_clean[igid_col]

# 1차 회귀 분석
slope, intercept, r_value, p_value, std_err = stats.linregress(x, y)
r_squared = r_value**2

# 산점도 및 회귀선 그리기
plt.figure(figsize=(8, 6))
plt.scatter(x, y, alpha=0.6, edgecolors='k', s=50, label='데이터 포인트 (A, B 등급)')

# 회귀선 범위 계산
x_min, x_max = x.min(), x.max()
x_line = np.linspace(x_min, x_max, 100)
y_line = slope * x_line + intercept
plt.plot(x_line, y_line, color='red', linestyle='--', linewidth=2, label=f'회귀선: y = {slope:.3f}x + {intercept:.3f}')

# R² 및 식 텍스트 표시
text_str = f'Regression Equation:\ny = {slope:.4f}x + {intercept:.4f}\n$R^2$ = {r_squared:.4f}'
plt.text(0.05, 0.95, text_str, transform=plt.gca().transAxes, fontsize=10,
         verticalalignment='top', bbox=dict(boxstyle='round,pad=0.5', facecolor='white', alpha=0.8))

plt.xlabel(metal_col)
plt.ylabel(igid_col)
plt.title('잔류금속 vs IG/ID 산점도 (등급 C 제외)')
plt.legend(loc='lower right')
plt.grid(True, linestyle=':', alpha=0.5)

plt.tight_layout()
output_filename = os.path.join(OUT_DIR, 'scatter_residual_metal_vs_igid.png')
plt.savefig(output_filename, dpi=300)
plt.close()
