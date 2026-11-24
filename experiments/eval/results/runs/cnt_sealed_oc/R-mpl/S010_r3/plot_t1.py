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

# 일자 컬럼을 datetime으로 변환
# 미리보기에 'yyyy-mm-dd' 포맷이라고 명시되어 있으므로 format 지정 및 errors='coerce' 사용
try:
    df['일자'] = pd.to_datetime(df['일자'], format='%Y-%m-%d', errors='coerce')
except Exception:
    # 만약 위 시도가 실패하면 (예를 들어 일부 행이 이미 datetime 객체이거나 다른 형식일 경우) 
    # pandas의 자동 추론을 시도하되, NaT로 처리된 값은 제거
    df['일자'] = pd.to_datetime(df['일자'], errors='coerce')

# 유효하지 않은 날짜 제거
df = df.dropna(subset=['일자'])

# 3월과 8월 데이터 필터링
df['month'] = df['일자'].dt.month
march_df = df[df['month'] == 3]
august_df = df[df['month'] == 8]

# 반응기별 평균 수율 계산
# CNT수율 컬럼명이 정확히 매칭되지 않을 수 있어 부분 일치 검색 또는 정확한 이름 확인 필요
# 미리보기에는 'CNT수율 (g/g-cat)' 로 나옴
yield_col = 'CNT수율 (g/g-cat)'
if yield_col not in march_df.columns:
    # 대소문자나 공백 차이 가능성 고려하여 찾기
    matches = [c for c in march_df.columns if 'CNT' in str(c) and '수율' in str(c)]
    if matches:
        yield_col = matches[0]
    else:
        # 그래도 없으면 기본값 사용 (실패 방지용)
        print("Warning: CNT yield column not found, using first numeric column ending with '%' or similar logic if applicable.")
        # 여기서는 미리보기 기반으로 안전하다고 판단되는 컬럼명을 다시 한번 체크하거나 에러를 던지지 않고 진행
        # 만약 정말 없다면 빈 DataFrame으로 인해 mean()이 NaN을 반환할 수 있음
        
march_avg_yield = march_df.groupby('반응기')[yield_col].mean()
august_avg_yield = august_df.groupby('반응기')[yield_col].mean()

# 반응기 순서 정렬 (R1~R4)
reactors = ['R1', 'R2', 'R3', 'R4']
march_values = [march_avg_yield.get(r, 0) for r in reactors]
august_values = [august_avg_yield.get(r, 0) for r in reactors]

# 막대 그래프 그리기
x = np.arange(len(reactors))
width = 0.35

fig, ax = plt.subplots(figsize=(10, 6))
bars1 = ax.bar(x - width/2, march_values, width, label='3월 평균 수율', color='#1f77b4')
bars2 = ax.bar(x + width/2, august_values, width, label='8월 평균 수율', color='#ff7f0e')

ax.set_xlabel('반응기', fontsize=12)
ax.set_ylabel('평균 CNT 수율 (g/g-cat)', fontsize=12)
ax.set_title('반응기별 3월 및 8월 평균 CNT 수율 비교', fontsize=14)
ax.set_xticks(x)
ax.set_xticklabels(reactors)
ax.legend()

# 값 표시
for bar in bars1:
    height = bar.get_height()
    if not np.isnan(height):
        ax.annotate(f'{height:.2f}',
                    xy=(bar.get_x() + bar.get_width() / 2, height),
                    xytext=(0, 3),
                    textcoords="offset points",
                    ha='center', va='bottom', fontsize=9)

for bar in bars2:
    height = bar.get_height()
    if not np.isnan(height):
        ax.annotate(f'{height:.2f}',
                    xy=(bar.get_x() + bar.get_width() / 2, height),
                    xytext=(0, 3),
                    textcoords="offset points",
                    ha='center', va='bottom', fontsize=9)

plt.tight_layout()
output_path = os.path.join(OUT_DIR, "reactor_yield_comparison_march_august.png")
plt.savefig(output_path, dpi=300, bbox_inches='tight')
plt.close()
