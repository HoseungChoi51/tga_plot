import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import os

# 설정
OUT_DIR = "out/t1"
os.makedirs(OUT_DIR, exist_ok=True)
plt.rcParams["font.family"] = "Noto Sans CJK KR"
plt.rcParams['axes.unicode_minus'] = False

# 데이터 경로
file_path = "data/run_log.xlsx"

# 데이터 로드 (시트 '런로그')
df = pd.read_excel(file_path, sheet_name='런로그')

# 컬럼명 공백 제거 및 확인 (실제 헤더와 다를 수 있어 안전성 확보)
df.columns = df.columns.str.strip()

# 일자 컬럼을 datetime으로 변환
# 'yyyy-mm-dd' 형식의 문자열 헤더나 데이터가 섞여 있을 수 있어 errors='coerce'를 사용하여
# 파싱 실패 시 NaT로 처리하고, 이후 필터링에서 제외함
if '일자' in df.columns:
    df['일자'] = pd.to_datetime(df['일자'], format='%Y-%m-%d', errors='coerce')
else:
    # 혹시 컬럼명이 다른 경우를 대비해 첫 번째 날짜형 컬럼을 찾는 로직은 생략하지만,
    # 미리보기에는 '일자'가 있음. 만약 '일자'가 없으면 에러가 나지만, 이번엔 있음.
    pass

# 유효한 날짜만 남기기
df_valid = df.dropna(subset=['일자'])

# 3월과 8월 데이터 필터링
df_march = df_valid[df_valid['일자'].dt.month == 3]
df_august = df_valid[df_valid['일자'].dt.month == 8]

# 반응기별 평균 수율 계산
# 미리보기에 따르면 컬럼명은 'CNT수율 (g/g-cat)' 또는 유사한 형태입니다.
# 앞선 에러(KeyError)는 스페이스 차이 등을 암시하므로, 가장 정확한 컬럼명을 찾아 씁니다.
yield_col = None
for col in df_valid.columns:
    if '수율' in col and 'CNT' in col:
        yield_col = col
        break

if yield_col is None:
    raise ValueError("CNT 수율 컬럼을 찾을 수 없습니다.")

avg_yield_march = df_march.groupby('반응기')[yield_col].mean()
avg_yield_august = df_august.groupby('반응기')[yield_col].mean()

# 모든 반응기(R1~R4)를 포함하기 위해 인덱스 재정렬
reactors = ['R1', 'R2', 'R3', 'R4']
avg_yield_march = avg_yield_march.reindex(reactors).fillna(0)
avg_yield_august = avg_yield_august.reindex(reactors).fillna(0)

# 그래프 생성
x = np.arange(len(reactors))
width = 0.35

fig, ax = plt.subplots(figsize=(10, 6))
rects1 = ax.bar(x - width/2, avg_yield_march.values, width, label='3월 평균 수율', color='#1f77b4')
rects2 = ax.bar(x + width/2, avg_yield_august.values, width, label='8월 평균 수율', color='#ff7f0e')

# 라벨 및 제목 설정
ax.set_xlabel('반응기')
ax.set_ylabel(f'평균 CNT 수율 ({yield_col})')
ax.set_title('반응기별 3월 및 8월 평균 CNT 수율 비교')
ax.set_xticks(x)
ax.set_xticklabels(reactors)
ax.legend()

# 막대 위에 값 표시
def add_value_labels(ax, rects):
    for rect in rects:
        height = rect.get_height()
        if height > 0:
            ax.annotate(f'{height:.2f}',
                        xy=(rect.get_x() + rect.get_width() / 2, height),
                        xytext=(0, 3),  # 3 points vertical offset
                        textcoords="offset points",
                        ha='center', va='bottom')

add_value_labels(ax, rects1)
add_value_labels(ax, rects2)

# y축 범위 조정 (값이 잘 보이도록 약간 여유롭게)
max_val = max(avg_yield_march.max(), avg_yield_august.max())
if max_val == 0:
    ax.set_ylim(0, 10)
else:
    ax.set_ylim(0, max_val * 1.15)

plt.tight_layout()
output_path = os.path.join(OUT_DIR, "reactor_yield_comparison.png")
plt.savefig(output_path, dpi=300)
plt.close()
