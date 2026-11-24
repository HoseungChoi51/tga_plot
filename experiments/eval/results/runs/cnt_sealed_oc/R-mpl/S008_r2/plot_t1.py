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
df = pd.read_excel(file_path, sheet_name='런로그')

# 컬럼명 공백/특수문자 제거 및 정규화하여 사용 (예: 'CNT수율 (g/g-cat)' -> 'CNT수율(g/g-cat)' 등 가능성 대비)
# 에러 원인 분석: 
# 1. 이전 KeyError는 컬럼명 불일치로 추정됨 (미리보기와 실제 엑셀의 공백 차이 등).
# 2. 이번 TypeError(dtype->object)는 해당 컬럼이 숫자가 아닌 문자열 객체로 읽혔거나, 컬럼 선택 시 문제가 생겼을 가능성 있음.
#    미리보기에 따르면 'CNT수율 (g/g-cat)'은 수치형이어야 함. 
#    하지만 엑셀 파일 구조상 헤더 아래 단位列(units row)이 있거나, 데이터 타입 추론 실패로 object가 될 수 있음.
#    또한 컬럼명이 정확히 일치하지 않아 다른 컬럼을 잡았을 수도 있음.

# 안전한 컬럼 검색: 'CNT'와 '수율'을 포함하는 컬럼 찾기
yield_col = None
for col in df.columns:
    col_str = str(col).strip()
    if 'CNT' in col_str and '수율' in col_str:
        yield_col = col_str
        # 원본 df의 컬럼명과 매칭되도록 처리. 만약 strip된 이름과 다르면 다시 확인 필요하지만, 
        # 보통 pandas read_excel은 헤더를 그대로 읽으므로, 여기서 찾은 col을 그대로 사용해야 함.
        # 단, 위에서 col_str으로 비교했으므로, 원본 컬럼명을 찾아야 함.
        break

if yield_col is None:
    # 혹시 모를 대안: 컬럼명이 조금 다를 수 있으므로 키워드만으로 재검색
    for col in df.columns:
        if '수율' in str(col):
            yield_col = col
            break

if yield_col is None:
    raise ValueError("CNT 수율 컬럼을 찾을 수 없습니다.")

# 주차 컬럼도 안전하게 찾기
week_col = None
for col in df.columns:
    if '주차' in str(col):
        week_col = col
        break
if week_col is None:
    raise ValueError("주차 컬럼을 찾을 수 없습니다.")

# 데이터 전처리: 수율 컬럼을 숫자로 강제 변환 (object인 경우 또는 비어있는 값 처리)
# pd.to_numeric errors='coerce'로 숫자 아님을 NaN으로 만들고 dropna 후 평균 계산
df[yield_col] = pd.to_numeric(df[yield_col], errors='coerce')
df[week_col] = pd.to_numeric(df[week_col], errors='coerce')

# 결측치 제거
clean_df = df.dropna(subset=[week_col, yield_col])

# 주차별 평균 수율 계산 (반응기 구분 없이 전체 평균)
weekly_avg_yield = clean_df.groupby(week_col)[yield_col].mean().reset_index()

# plotting
fig, ax = plt.subplots(figsize=(12, 6))

ax.plot(weekly_avg_yield[week_col], weekly_avg_yield[yield_col], marker='o', linestyle='-', color='#1f77b4', label='평균 CNT 수율')

# 14주차 세로 점선 및 텍스트 추가
target_week = 14
if target_week in weekly_avg_yield[week_col].values:
    # 해당 주차의 y값을 찾아서 텍스트 위치 조정
    y_val = weekly_avg_yield.loc[weekly_avg_yield[week_col] == target_week, yield_col].values[0]
    
    ax.axvline(x=target_week, color='red', linestyle='--', linewidth=1.5, alpha=0.7)
    
    # 텍스트 배치: 선의 오른쪽 상단이나 적절한 곳에 배치
    ax.text(target_week + 0.3, y_val, 'FC-2606 투입', color='red', fontsize=10, verticalalignment='center', ha='left', weight='bold')

# 차트 꾸미기
ax.set_title('주차별 평균 CNT 수율', fontsize=14)
ax.set_xlabel('주차', fontsize=12)
ax.set_ylabel(f'평균 수율 ({yield_col})', fontsize=12)
ax.grid(True, linestyle=':', alpha=0.6)
ax.legend()

# X축 눈금 확인
max_week = weekly_avg_yield[week_col].max()
min_week = weekly_avg_yield[week_col].min()
xticks = range(int(min_week), int(max_week)+1, 1)
ax.set_xticks(list(xticks))

plt.tight_layout()

# 저장
output_filename = os.path.join(OUT_DIR, "weekly_avg_yield_plot.png")
plt.savefig(output_filename, dpi=300, bbox_inches='tight')
plt.close(fig)
