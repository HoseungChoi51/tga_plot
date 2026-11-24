import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import os

# 설정
OUT_DIR = "out/t1"
os.makedirs(OUT_DIR, exist_ok=True)

plt.rcParams["font.family"] = "Noto Sans CJK KR"
plt.rcParams["axes.unicode_minus"] = False

# 데이터 로드
file_path = "data/run_log.xlsx"
df = pd.read_excel(file_path, sheet_name="런로그")

# 컬럼 이름이 공백이나 특수문자 차이로 안 잡힐 수 있으므로, 
# 실제 존재하는 컬럼명을 확인하고 매칭하는 로직 추가 (유지보수성 향상)
def get_column_name(df, target_str):
    # target_str을 포함하는 컬럼 찾기 (대소문자/공백 무시 등 유연하게)
    for col in df.columns:
        if target_str.replace(" ", "") in str(col).replace(" ", ""):
            return col
    raise KeyError(f"Column containing '{target_str}' not found.")

try:
    col_humidity = get_column_name(df, "외기습도")
    col_grade = get_column_name(df, "등급")
    col_yield = get_column_name(df, "CNT수율")
    col_oxidation = get_column_name(df, "산화개시온도")
except Exception as e:
    print(f"Error identifying columns: {e}")
    cols_needed = ["외기습도 (%)", "등급 (A/B/C)", "CNT수율 (g/g-cat)", "산화개시온도 (°C)"]
    available_cols = [c for c in cols_needed if c in df.columns]
    missing_cols = [c for c in cols_needed if c not in df.columns]
    if missing_cols:
        raise ValueError(f"Missing columns even after fallback check: {missing_cols}. Actual columns: {df.columns.tolist()}")
    
    col_humidity = "외기습도 (%)"
    col_grade = "등급 (A/B/C)"
    col_yield = "CNT수율 (g/g-cat)"
    col_oxidation = "산화개시온도 (°C)"

# 데이터 전처리: 필요 컬럼 추출 및 결측치 제거
df_plot = df[[col_humidity, col_grade, col_yield, col_oxidation]].dropna()

# 등급 순서 정의
grade_order = ['C', 'B', 'A']

# 플롯 구성: 3개의 서브플롯으로 습도와 품질 지표의 관계 시각화
fig, axes = plt.subplots(3, 1, figsize=(12, 14))

# 1. 습도 구간별 평균 품질 지표 비교 (박스 플롯)
ax1 = axes[0]
# 등급별 습도 분포
# 박스플롯은 그룹별로 데이터를 리스트로 전달해야 함
box_data = []
for g in grade_order:
    subset = df_plot[df_plot[col_grade] == g][col_humidity]
    box_data.append(subset.values)

# tick_labels는 문자열 리스트여야 함 (float 에러 방지)
bp = ax1.boxplot(box_data, labels=grade_order, patch_artist=True)

colors = ['#FF9999', '#66B2FF', '#99FF99'] # C(빨강), B(파랑), A(초록)
for patch, color in zip(bp['boxes'], colors):
    patch.set_facecolor(color)
    
ax1.set_title('외기 습도에 따른 품질 등급(A/B/C) 분포')
ax1.set_ylabel('외기 습도 (%)')
ax1.grid(True, axis='y', linestyle='--', alpha=0.7)

# 2. 습도와 CNT 수율의 산점도 + 이동평균선 (Bin Average)
ax2 = axes[1]
# 데이터가 숫자형인지 확인 후 프로팅
hum_vals = pd.to_numeric(df_plot[col_humidity], errors='coerce')
yield_vals = pd.to_numeric(df_plot[col_yield], errors='coerce')
valid_mask = ~(hum_vals.isna() | yield_vals.isna())

ax2.scatter(hum_vals[valid_mask], yield_vals[valid_mask], alpha=0.6, s=20, color='#4c72b0', label='Data Points')

# 습도 구간별 평균 수율 계산 후 선으로 연결
bins = np.arange(30, 105, 5) # 30~100까지 커버하기 위해 105로 끝
# 바이닝된 값은 카테고리일 수 있으나, 여기서 그룹핑 시 bin center를 재계산하여 사용
temp_df = df_plot[valid_mask].copy()
temp_df['습도_bin'] = pd.cut(temp_df[col_humidity], bins=bins)
grouped = temp_df.groupby('습도_bin', observed=True)[col_yield].mean().reset_index()

# bin_center 계산: Interval 객체에서 left/right 속성 접근
grouped['bin_center'] = grouped['습도_bin'].apply(lambda x: (x.left + x.right) / 2 if not pd.isna(x) else np.nan)

# 유효한 bin center와 mean만 plotting
valid_bins = grouped.dropna(subset=['bin_center'])
if not valid_bins.empty:
    ax2.plot(valid_bins['bin_center'], valid_bins[col_yield], 'ro-', linewidth=2, markersize=8, label='Average Yield per Humidity Bin')

ax2.set_xlabel('외기 습도 (%)')
ax2.set_ylabel('CNT 수율 (g/g-cat)')
ax2.set_title('외기 습도와 CNT 수율 관계')
ax2.legend(loc='best')
ax2.grid(True, linestyle='--', alpha=0.7)

# 3. 습도와 산화개시온도(순도/품질 관련 지표) 관계
ax3 = axes[2]
oxi_vals = pd.to_numeric(df_plot[col_oxidation], errors='coerce')
valid_mask_oxi = ~(hum_vals.isna() | oxi_vals.isna())

ax3.scatter(hum_vals[valid_mask_oxi], oxi_vals[valid_mask_oxi], alpha=0.6, s=20, color='#dd8452', label='Data Points')

# 습도 구간별 평균 산화개시온도
temp_df_oxi = df_plot[valid_mask_oxi].copy()
temp_df_oxi['습도_bin'] = pd.cut(temp_df_oxi[col_humidity], bins=bins)
grouped_temp = temp_df_oxi.groupby('습도_bin', observed=True)[col_oxidation].mean().reset_index()
grouped_temp['bin_center'] = grouped_temp['습도_bin'].apply(lambda x: (x.left + x.right) / 2 if not pd.isna(x) else np.nan)

valid_bins_temp = grouped_temp.dropna(subset=['bin_center'])
if not valid_bins_temp.empty:
    ax3.plot(valid_bins_temp['bin_center'], valid_bins_temp[col_oxidation], 'gs-', linewidth=2, markersize=8, label='Avg Oxidation Onset Temp')

ax3.set_xlabel('외기 습도 (%)')
ax3.set_ylabel('산화 개시 온도 (°C)')
ax3.set_title('외기 습도와 산화 개시 온도(순도 지표) 관계')
ax3.legend(loc='best')
ax3.grid(True, linestyle='--', alpha=0.7)

plt.tight_layout()
output_filename = os.path.join(OUT_DIR, "humidity_vs_quality_analysis.png")
plt.savefig(output_filename, dpi=300)
plt.close()

print(f"Plot saved to {output_filename}")
