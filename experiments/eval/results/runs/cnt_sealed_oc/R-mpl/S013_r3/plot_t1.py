import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import os

# 환경 설정
OUT_DIR = "out/t1"
os.makedirs(OUT_DIR, exist_ok=True)
plt.rcParams["font.family"] = "Noto Sans CJK KR"
plt.rcParams["axes.unicode_minus"] = False

# 데이터 경로
data_file = "data/run_log.xlsx"
sheet_name = "런로그"

# 데이터 읽기
df = pd.read_excel(data_file, sheet_name=sheet_name)

# 컬럼명 확인 및 매핑 (미리보기에 따라 '반응기', '등급', '일자' 사용 가정)
cols = df.columns.tolist()

def find_col(keyword):
    for c in cols:
        if keyword in str(c):
            return c
    return None

reactor_col = find_col('반응기')
grade_col = find_col('등급')
date_col = find_col('일자')

if not all([reactor_col, grade_col, date_col]):
    raise ValueError(f"필수 컬럼을 찾을 수 없습니다. 반응기:{reactor_col}, 등급:{grade_col}, 일자:{date_col}")

# 월 생성
# 'yyyy-mm-dd' 형식 오류 해결을 위해 errors='coerce'를 사용하여 파싱 실패 시 NaT로 변환하고 드롭하거나 처리하지 않음.
# 미리보기상 실제 값은 날짜형이므로 정상이면 잘 될 것이나, 헤더나 설명 텍스트가 섞여 있을 경우 방지.
parsed_dates = pd.to_datetime(df[date_col], format='mixed', errors='coerce')
df['월'] = parsed_dates.dt.month

# 유효한 날짜만 필터링 (NaT 제거)
df_valid = df.dropna(subset=['월']).copy()
df_valid['월'] = df_valid['월'].astype(int)

# 합격률 계산: 등급 A인 런의 비율 (%)
# 각 반응기-월 조합에서 총 런 수와 A 등급 런 수를 집계
grouped = df_valid.groupby([reactor_col, '월'])[grade_col].agg(
    total='count',
    pass_count=lambda x: (x == 'A').sum()
).reset_index()

grouped['합격률'] = (grouped['pass_count'] / grouped['total']) * 100

# 피벗 테이블 생성 (행: 반응기, 열: 월, 값: 합격률)
pivot_table = grouped.pivot(index=reactor_col, columns='월', values='합격률')

# 히트맵 그리기 (matplotlib 사용)
fig, ax = plt.subplots(figsize=(12, 6))

# imshow 대신 pcolor 또는 imshow 사용. seaborn이 없으므로 직접 구현
im = ax.imshow(pivot_table.values, cmap="YlGnBu", aspect="auto")

# 축 눈금 설정
ax.set_xticks(np.arange(len(pivot_table.columns)))
ax.set_yticks(np.arange(len(pivot_table.index)))
ax.set_xticklabels(pivot_table.columns)
ax.set_yticklabels(pivot_table.index)

# 셀 안에 텍스트 추가
for i in range(len(pivot_table.index)):
    for j in range(len(pivot_table.columns)):
        val = pivot_table.iloc[i, j]
        # NaN 처리 (데이터 없는 경우)
        if not np.isnan(val):
            text_color = "white" if val > 75 else "black" # 배경색 대비 고려 (간단히 임계값 지정)
            ax.text(j, i, f"{val:.1f}", ha="center", va="center", color=text_color, fontsize=9)

ax.set_title('반응기 × 월별 CNT 생산 합격률 (%)', fontsize=14)
ax.set_xlabel('월', fontsize=12)
ax.set_ylabel('반응기', fontsize=12)

# 색상막 추가
cbar = fig.colorbar(im, ax=ax)
cbar.set_label('합격률 (%)')

plt.tight_layout()
output_path = os.path.join(OUT_DIR, "reactor_month_passrate_heatmap.png")
plt.savefig(output_path, dpi=300)
plt.close()
