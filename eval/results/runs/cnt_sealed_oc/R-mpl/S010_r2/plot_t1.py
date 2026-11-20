import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import os

# 설정
OUT_DIR = "out/t1"
os.makedirs(OUT_DIR, exist_ok=True)

# 한글 폰트 설정
plt.rcParams["font.family"] = "Noto Sans CJK KR"
plt.rcParams["axes.unicode_minus"] = False

# 데이터 읽기
file_path = "data/run_log.xlsx"
df = pd.read_excel(file_path, sheet_name="런로그")

# 컬럼 이름 확인 및 정규화 (공백, 특수문자 등 차이 해결을 위해 가장 유사한 컬럼명을 찾거나 직접 지정)
# 미리보기에 따르면 'CNT수율 (g/g-cat)' 또는 유사한 형태일 수 있습니다.
# 에러 메시지에서 'CNT수율 (g/g-cat)'을 찾지 못한다고 했으므로, 실제 컬럼명을 확인하는 로직을 추가합니다.
yield_col = None
for col in df.columns:
    if 'CNT' in str(col) and '수율' in str(col):
        yield_col = col
        break

if yield_col is None:
    # 만약 일치하는 것이 없다면, 미리보기의 정확한 문자열이나 다른 변형을 시도
    possible_names = ['CNT수율', 'CNT 수율', '수율', 'CNT수율(g/g-cat)', 'CNT수율 (g/g-cat)']
    for name in possible_names:
        if name in df.columns:
            yield_col = name
            break
            
if yield_col is None:
    raise ValueError("Could not find the CNT yield column. Columns available: " + str(df.columns.tolist()))

# 일자 컬럼을 datetime으로 변환
# 헤더에 단위나 설명이 포함될 수 있으므로, 컬럼명이 '일자'인 것을 우선 찾습니다.
date_col = None
for col in df.columns:
    if '일자' in str(col) or 'Date' in str(col):
        date_col = col
        break

if date_col is None:
    raise ValueError("Could not find the date column.")

df[date_col] = pd.to_datetime(df[date_col], errors='coerce')

# 유효한 날짜를 가진 행만 필터링
df_valid = df.dropna(subset=[date_col])

# 3월과 8월 데이터 필터링
df_march = df_valid[df_valid[date_col].dt.month == 3]
df_august = df_valid[df_valid[date_col].dt.month == 8]

# 반응기별 평균 수율 계산
avg_yield_march = df_march.groupby('반응기')[yield_col].mean()
avg_yield_august = df_august.groupby('반응기')[yield_col].mean()

# 반응기 정렬 (R1, R2, R3, R4 순서로 유지하기 위해 인덱스 재설정 및 정렬)
reactors = ['R1', 'R2', 'R3', 'R4']
avg_yield_march = avg_yield_march.reindex(reactors)
avg_yield_august = avg_yield_august.reindex(reactors)

# 그래프 그리기
fig, ax = plt.subplots(figsize=(10, 6))

x = np.arange(len(reactors))  # 막대 그룹의 위치
width = 0.35  # 막대의 너비

# 묶은 막대 차트
rects1 = ax.bar(x - width/2, avg_yield_march.values, width, label='3월', color='#1f77b4')
rects2 = ax.bar(x + width/2, avg_yield_august.values, width, label='8월', color='#ff7f0e')

# 라벨, 제목, 축 범위 등 추가
ax.set_ylabel(f'평균 CNT 수율 ({yield_col.split("(")[0].strip()} {yield_col[yield_col.find("("):]})', fontsize=12)
ax.set_title('반응기별 월간 평균 CNT 수율 비교 (3월 vs 8월)', fontsize=14, fontweight='bold')
ax.set_xticks(x)
ax.set_xticklabels(reactors)
ax.legend(loc='upper right', fontsize=10)

# 막대 위에 값 표시
def add_value_labels(ax):
    for rect in ax.containers:
        height = rect.get_height()
        if not np.isnan(height):
            ax.annotate(f'{height:.2f}',
                        xy=(rect.get_x() + rect.get_width() / 2, height),
                        xytext=(0, 3),  # 3 points vertical offset
                        textcoords="offset points",
                        ha='center', va='bottom', fontsize=9)

add_value_labels(ax)

# y축 제한 조정하여 상단 여백 확보
max_val = max(avg_yield_march.max(), avg_yield_august.max())
ax.set_ylim(0, max_val * 1.15)

# 격자선 추가 (가로선만)
ax.grid(axis='y', linestyle='--', alpha=0.7)
ax.set_axisbelow(True)

# 레이아웃 정리
plt.tight_layout()

# 파일 저장
output_file = os.path.join(OUT_DIR, "reactor_yield_comparison.png")
plt.savefig(output_file, dpi=300)
plt.close()
