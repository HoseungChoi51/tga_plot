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

# 열 이름 정리: 공백 제거 및 특수문자 확인을 위해 strip 적용
df.columns = df.columns.str.strip()

# 실제 사용된 2존온도 컬럼명 찾기 (데이터 미리보기상에는 'I 2존온도 (°C)'라고 표시되어 있지만, 
# pandas가 읽었을 때 헤더의 공백이나 줄바꿈에 따라 이름이 다를 수 있음. 
# 가장 안전한 방법은 '2존'을 포함하는 컬럼을 찾는 것임.)
col_zone2_candidates = [c for c in df.columns if '2존' in c]
if not col_zone2_candidates:
    raise ValueError("2존 온도 컬럼을 찾을 수 없습니다.")
col_zone2 = col_zone2_candidates[0]

# 근무조와 반응기도 유사하게 확인 필요하지만 미리보기 기준으로 존재한다고 가정.
col_shift_candidates = [c for c in df.columns if '근무조' in c]
col_reactor_candidates = [c for c in df.columns if '반응기' in c]

if not col_shift_candidates or not col_reactor_candidates:
    raise ValueError("근무조 또는 반응기 컬럼을 찾을 수 없습니다.")

col_shift = col_shift_candidates[0]
col_reactor = col_reactor_candidates[0]

# 결측치 처리
df_clean = df.dropna(subset=[col_zone2, col_shift, col_reactor]).copy()

# 타입 변환: 그룹화 및 평균 계산을 위해 수치형으로 변환
# Excel에서 텍스트로 저장되었거나 빈 문자열이 섞여 있을 경우를 대비해 errors='coerce' 사용 후 다시 dropna
df_clean[col_zone2] = pd.to_numeric(df_clean[col_zone2], errors='coerce')
df_clean = df_clean.dropna(subset=[col_zone2])

# 그룹화: 반응기별, 근무조별 평균 2존 온도
grouped = df_clean.groupby([col_reactor, col_shift])[col_zone2].mean().reset_index()

# 피벗 테이블로 주간/야간을 컬럼으로 분리
pivot_df = grouped.pivot(index=col_reactor, columns=col_shift, values=col_zone2)

# 막대 그래프 그리기
reactors = pivot_df.index.tolist()
x = np.arange(len(reactors))
width = 0.35

fig, ax = plt.subplots(figsize=(10, 6))

# 주간과 야간 막대
# pivot_df에서 컬럼명으로 접근하므로, get을 사용하여 없으면 빈 배열처럼 처리하거나 에러 방지
vals_day = pivot_df.get('주간', pd.Series([np.nan]*len(reactors), index=reactors))
vals_night = pivot_df.get('야간', pd.Series([np.nan]*len(reactors), index=reactors))

bars_day = ax.bar(x - width/2, vals_day, width, label='주간', color='#4CAF50')
bars_night = ax.bar(x + width/2, vals_night, width, label='야간', color='#2196F3')

# 라벨 및 타이틀 설정
ax.set_xlabel('반응기', fontsize=12)
ax.set_ylabel(f'평균 {col_zone2}', fontsize=12) # 원본 컬럼명을 그대로 사용하거나 깔끔하게 가공 가능. 여기서는 명확성을 위해 원본 기반.
ax.set_title('반응기별 근무조에 따른 평균 2존 온도 비교', fontsize=14)
ax.set_xticks(x)
ax.set_xticklabels(reactors)
ax.legend()

# Y축 범위 조정 (차이를 더 잘 보이게 하기 위해 최소값에서 여유를 둠)
all_vals = np.concatenate((vals_day.values, vals_night.values))
all_vals = all_vals[~np.isnan(all_vals)]

if len(all_vals) > 0:
    y_min = all_vals.min() - 10
    y_max = all_vals.max() + 10
    ax.set_ylim(y_min, y_max)

# 값 텍스트 표시
def add_value_labels(ax, bars):
    for bar in bars:
        height = bar.get_height()
        if not np.isnan(height):
            ax.annotate(f'{height:.1f}',
                        xy=(bar.get_x() + bar.get_width() / 2, height),
                        xytext=(0, 3),  # 3 points vertical offset
                        textcoords="offset points",
                        ha='center', va='bottom', fontsize=9)

add_value_labels(ax, bars_day)
add_value_labels(ax, bars_night)

plt.tight_layout()
save_path = os.path.join(OUT_DIR, "reactor_zone2_temp_by_shift.png")
plt.savefig(save_path, dpi=300)
plt.close()
