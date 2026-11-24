import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import os

# 설정
plt.rcParams["font.family"] = "Noto Sans CJK KR"
plt.rcParams["axes.unicode_minus"] = False
OUT_DIR = "out/t1"
os.makedirs(OUT_DIR, exist_ok=True)

# 데이터 로드
file_path = "data/run_log.xlsx"
df = pd.read_excel(file_path, sheet_name="런로그")

# 컬럼명 공백 제거 및 정규화 (미리보기의 헤더와 실제 엑셀 헤더의 차이 처리)
# 예를 들어 'CNT수율 (g/g-cat)'가 실제로는 다른 이름일 수 있으므로 부분 일치 검색 사용
def find_column(df, keyword):
    cols = [c for c in df.columns if keyword in str(c)]
    return cols[0] if len(cols) > 0 else None

date_col = find_column(df, "일자")
yield_col = find_column(df, "수율")

if date_col is None or yield_col is None:
    raise ValueError(f"필요한 컬럼을 찾을 수 없습니다. columns: {list(df.columns)}")

print(f"날짜 컬럼: {date_col}, 수율 컬럼: {yield_col}")

# 날짜 변환
df[date_col] = pd.to_datetime(df[date_col], errors='coerce')
df_valid = df.dropna(subset=[date_col]).copy()
df_valid = df_valid.sort_values(date_col)

# 이동 평균 계산
WINDOW_SIZE = 10
df_valid['수율_이동평균'] = df_valid[yield_col].rolling(window=WINDOW_SIZE, min_periods=1).mean()

# 플롯 생성
fig, ax1 = plt.subplots(figsize=(14, 8))

# 1. 개별 런 데이터 (산점도)
ax1.scatter(df_valid[date_col], df_valid[yield_col], color='gray', alpha=0.6, s=30, label='개별 런 수율', edgecolors='none')
ax1.set_xlabel('생산 일자')
ax1.set_ylabel('CNT 수율 (g/g-cat)', color='black')
ax1.tick_params(axis='y', labelcolor='black')
ax1.grid(True, linestyle='--', alpha=0.5)

# 2. 이동평균선
ax1.plot(df_valid[date_col], df_valid['수율_이동평균'], color='red', linewidth=2.5, label=f'{WINDOW_SIZE}회 런 이동평균')

# 제목 및 레전드
min_date = df_valid[date_col].min().strftime("%Y-%m-%d")
max_date = df_valid[date_col].max().strftime("%Y-%m-%d")
ax1.set_title(f'CNT 생산 수율 추세 분석 ({min_date} ~ {max_date})', fontsize=16, pad=20)
ax1.legend(loc='upper left', bbox_to_anchor=(0.01, 0.98), frameon=True, shadow=True)

# 레이아웃 조정
plt.tight_layout()

# 저장
save_path = os.path.join(OUT_DIR, "yield_trend_analysis.png")
plt.savefig(save_path, dpi=300, bbox_inches='tight')
plt.close()

print(f"그래프가 저장되었습니다: {save_path}")
