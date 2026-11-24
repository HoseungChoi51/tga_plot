import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import os

# 설정
OUT_DIR = "out/t1"
os.makedirs(OUT_DIR, exist_ok=True)

# 한글 폰트 설정
plt.rcParams["font.family"] = "Noto Sans CJK KR"
plt.rcParams["axes.unicode_minus"] = False

# 데이터 읽기
file_path = "data/run_log.xlsx"
sheet_name = "런로그"
df = pd.read_excel(file_path, sheet_name=sheet_name)

# 컬럼명 정밀 매칭을 위해 실제 컬럼명을 확인하고 필요한 컬럼 추출
def find_column(df, target_substring):
    for col in df.columns:
        if target_substring in str(col):
            return col.strip()
    return None

col_humidity = find_column(df, '외기습도')
col_yield = find_column(df, 'CNT수율')
col_grade = find_column(df, '등급')

if not all([col_humidity, col_yield, col_grade]):
    raise ValueError(f"필요한 컬럼을 찾을 수 없습니다. humidity:{col_humidity}, yield:{col_yield}, grade:{col_grade}")

plot_df = df[[col_humidity, col_yield, col_grade]].dropna().copy()

# [중요] 숫자형으로 변환하기 전에 문자열에서 '%' 기호 제거 및 공백 제거
# 미리보기상 수치라고 했지만, 실제 파일에는 '%' 문자가 포함되었거나 타입이 object일 가능성이 높음
try:
    plot_df[col_humidity] = plot_df[col_humidity].astype(str).str.replace('%', '', regex=False).str.strip()
    plot_df[col_humidity] = pd.to_numeric(plot_df[col_humidity], errors='coerce')
except Exception as e:
    print(f"Warning during humidity conversion: {e}")
    # 만약 실패하면 원본 그대로 사용 (나중에 필터링 시 결측 처리됨)

try:
    plot_df[col_yield] = plot_df[col_yield].astype(str).str.replace('g/g-cat', '', regex=False).str.strip()
    plot_df[col_yield] = pd.to_numeric(plot_df[col_yield], errors='coerce')
except Exception as e:
    print(f"Warning during yield conversion: {e}")

# 최종적으로 결측치(NaN)인 행은 제외
plot_df = plot_df.dropna(subset=[col_humidity, col_yield])

# 시각화 1: 산점도 (Scatter Plot) - 습도 vs 수율
fig, ax = plt.subplots(figsize=(10, 6))

# 등급별 색상 구분
colors = {'A': '#2ecc71', 'B': '#f39c12', 'C': '#e74c3c'}
for grade, color in colors.items():
    subset = plot_df[plot_df[col_grade] == grade]
    if not subset.empty:
        ax.scatter(subset[col_humidity], 
                   subset[col_yield], 
                   label=f'등급 {grade}', 
                   color=color, 
                   alpha=0.6, 
                   edgecolors='k', 
                   linewidths=0.5,
                   s=50)

ax.set_xlabel('외기습도 (%)', fontsize=12)
ax.set_ylabel('CNT수율 (g/g-cat)', fontsize=12)
ax.set_title('습도에 따른 CNT 수율 분포 (등급별 구분)', fontsize=14, pad=15)
ax.legend(title='제품 등급', loc='best')
ax.grid(True, linestyle='--', alpha=0.3)

# 상관계수 계산하여 텍스트로 표시
corr_val = plot_df[col_humidity].corr(plot_df[col_yield])
ax.text(0.05, 0.95, f'피어슨 상관계수 (r): {corr_val:.3f}', 
        transform=ax.transAxes, va='top', ha='left',
        bbox=dict(boxstyle='round,pad=0.5', facecolor='white', alpha=0.8))

plt.tight_layout()
plt.savefig(os.path.join(OUT_DIR, "humidity_vs_yield_scatter.png"), dpi=300)
plt.close(fig)

# 시각화 2: 박스 플롯 (Box Plot) - 습도 구간별 수율 분포
# 습도를 구간으로 나누어 품질 변동성을 보기 위해
bins = [0, 40, 60, 80, 100]
labels = ['저습도\n(<40%)', '중저습도\n(40-60%)', '중고습도\n(60-80%)', '고습도\n(>80%)']
plot_df['습도_구간'] = pd.cut(plot_df[col_humidity], bins=bins, labels=labels, include_lowest=True)

fig_box, ax_box = plt.subplots(figsize=(8, 6))

# 그룹핑하여 박스플롯 데이터 준비
grouped_data = []
group_labels = []
for label in labels:
    data_subset = plot_df[plot_df['습도_구간'] == label][col_yield].dropna()
    if not data_subset.empty:
        grouped_data.append(data_subset.values)
        group_labels.append(label)

bp = ax_box.boxplot(grouped_data, tick_labels=group_labels, patch_artist=True)

# 색상 입히기
box_colors = ['#a8dadc', '#457b9d', '#1d3557', '#e63946']
for patch, color in zip(bp['boxes'], box_colors[:len(bp['boxes'])]):
    patch.set_facecolor(color)
    patch.set_alpha(0.6)

ax_box.set_title('습도 구간에 따른 CNT 수율 분포', fontsize=14, pad=15)
ax_box.set_xlabel('외기습도 구간', fontsize=12)
ax_box.set_ylabel('CNT수율 (g/g-cat)', fontsize=12)
ax_box.grid(axis='y', linestyle='--', alpha=0.3)

# 평균값 마커 추가
means = [np.mean(d) for d in grouped_data]
ax_box.plot(range(1, len(means)+1), means, 'ko-', markersize=8, label='평균값')
ax_box.legend(loc='upper right')

plt.tight_layout()
plt.savefig(os.path.join(OUT_DIR, "humidity_vs_yield_boxplot.png"), dpi=300)
plt.close(fig_box)

print(f"Plots saved to '{OUT_DIR}' directory.")
