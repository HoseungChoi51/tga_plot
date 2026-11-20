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

# 컬럼명 매칭 및 타입 변환
# 정확한 열 이름을 찾기 위해 strip 처리 후 검색
target_cols = {c.strip(): c for c in df.columns}

yield_col_key = None
for key, original_name in target_cols.items():
    if "CNT수율" in key:
        yield_col_key = original_name
        break

reactor_col_key = None
for key, original_name in target_cols.items():
    if "반응기" in key:
        reactor_col_key = original_name
        break

if yield_col_key is None or reactor_col_key is None:
    raise ValueError("필요한 컬럼을 찾을 수 없습니다.")

# 데이터를 새로운 변수로 복사하고 타입을 숫자로 강제 변환 (NaN 처리 포함)
# object 타입인 경우 pd.to_numeric(errors='coerce')를 사용하여 숫자화
df['yield_num'] = pd.to_numeric(df[yield_col_key], errors='coerce')
df['reactor_str'] = df[reactor_col_key].astype(str).str.strip()

# 결측치가 있는 행은 그룹핑 시 자동으로 제외되지만, 명시적으로 드롭하여 깔끔하게 작업 가능
# 여기서는 groupby가 NaN을 자동으로 무시하므로 dropna 생략 가능하지만, 안전을 위해 유효 데이터만 사용
valid_df = df.dropna(subset=['yield_num'])

# 반응기별 수율 통계 계산
stats = valid_df.groupby('reactor_str')['yield_num'].agg(['mean', 'std', 'min', 'max', 'count']).reset_index()
stats.columns = ['reactor', 'mean_yield', 'std_yield', 'min_yield', 'max_yield', 'count']

# 시각화: 반응기별 수율 분포 비교 (박스 플롯 + 평균선)
fig, ax = plt.subplots(figsize=(10, 6))

# 박스 플롯 그리기
sorted_reactors = sorted(valid_df['reactor_str'].unique())
box_data = [valid_df[valid_df['reactor_str'] == r]['yield_num'].values for r in sorted_reactors]

bplot = ax.boxplot(box_data, patch_artist=True, labels=sorted_reactors)

# 색상 설정
colors = ['#2ecc71', '#3498db', '#f1c40f', '#e74c3c'] # R1~R4 순서대로 다른 색
for i, patch in enumerate(bplot['boxes']):
    color_idx = i % len(colors)
    patch.set_facecolor(colors[color_idx])
    patch.set_alpha(0.7)

# whisker와 median 선 스타일
for element in ['whiskers', 'caps']:
    plt.setp(bplot[element], color='black')
plt.setp(bplot['medians'], color='black', linewidth=2)

# 평균값 점 표시 및 값 텍스트 추가
for i, reactor in enumerate(sorted_reactors):
    # stats에서 해당 반응기의 평균값 찾기
    mean_val = stats.loc[stats['reactor'] == reactor, 'mean_yield'].values[0]
    
    x_pos = i + 1
    ax.plot(x_pos, mean_val, 'r*', markersize=15, label=f'{reactor} 평균' if i==0 else "")
    
    # 평균값 텍스트를 박스 위에 표시
    max_val = stats.loc[stats['reactor'] == reactor, 'max_yield'].values[0]
    text_y = max_val + 0.5
    ax.text(x_pos, text_y, f"{mean_val:.2f}", ha='center', va='bottom', fontsize=10, weight='bold', color='red')

# 레이블 및 제목
ax.set_title("반응기별 CNT 수율 분포 비교", fontsize=16)
ax.set_xlabel("반응기", fontsize=12)
ax.set_ylabel("CNT 수율 (g/g-cat)", fontsize=12)
ax.grid(axis='y', linestyle='--', alpha=0.7)

plt.tight_layout()

# 저장
save_path = os.path.join(OUT_DIR, "yield_by_reactor_comparison.png")
plt.savefig(save_path, dpi=300, bbox_inches='tight')
plt.close()

print(f"그래프가 {save_path} 에 저장되었습니다.")
