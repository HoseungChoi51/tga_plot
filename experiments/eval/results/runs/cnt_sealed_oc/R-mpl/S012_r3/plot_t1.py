import pandas as pd
import matplotlib.pyplot as plt
import os

# 설정
OUT_DIR = "out/t1"
os.makedirs(OUT_DIR, exist_ok=True)

# 한글 폰트 설정
plt.rcParams["font.family"] = "Noto Sans CJK KR"
plt.rcParams["axes.unicode_minus"] = False

# 데이터 로드
file_path = "data/run_log.xlsx"
sheet_name = "런로그"
df = pd.read_excel(file_path, sheet_name=sheet_name)

# 열 이름 확인 및 공백 제거 등 처리하여 실제 컬럼명 매칭
col_yield = None
for c in df.columns:
    if 'CNT수율' in str(c):
        col_yield = c
        break

if col_yield is None:
    raise ValueError("CNT수율 컬럼을 찾을 수 없습니다.")

# 작업자 컬럼도 안전하게 찾기
col_worker = None
for c in df.columns:
    if '작업자' in str(c):
        col_worker = c
        break

if col_worker is None:
    # 만약 정확히 일치하지 않으면 첫 번째 텍스트 컬럼 중 하나일 가능성이 높으므로 기본값으로 시도하거나 에러 발생
    # 여기서는 미리보기 기준으로 '작업자'가 존재한다고 가정하되, 혹시 모를 경우를 대비해 검색 로직 유지
    raise ValueError("작업자 컬럼을 찾을 수 없습니다.")

# 필요 열만 선택
work_df = df[[col_worker, col_yield]].dropna()

# 중요: 데이터 타입 변환
# Excel에서 숫자가 텍스트로 저장되거나 혼합된 경우 mean() 연산이 실패할 수 있음
# pd.to_numeric을 사용하여 강제로 숫자로 변환하고, 변환 실패 시 NaN 처리
work_df[col_yield] = pd.to_numeric(work_df[col_yield], errors='coerce')

# 변환 후 다시 NaN 제거 (비숫자 값 제거)
work_df = work_df.dropna(subset=[col_yield])

# 작업자별 평균 수율 계산
avg_yield = work_df.groupby(col_worker)[col_yield].mean().reset_index()

# 높은 순으로 정렬
avg_yield_sorted = avg_yield.sort_values(by=col_yield, ascending=False)

# 상위 5명 추출
top_5 = avg_yield_sorted.head(5)

# plotting
fig, ax = plt.subplots(figsize=(10, 6))

y_pos = range(len(top_5))
labels = top_5[col_worker]
values = top_5[col_yield]

bars = ax.barh(y_pos, values, color='skyblue', edgecolor='black')

# 막대 끝에 값 표시
for bar in bars:
    width = bar.get_width()
    ax.text(width + 0.1, bar.get_y() + bar.get_height()/2, f'{width:.2f}', 
            va='center', ha='left', fontsize=10)

# 축 설정
ax.set_yticks(y_pos)
ax.set_yticklabels(labels)
ax.invert_yaxis()  # 첫 번째가 가장 위에 오도록 역전
ax.set_xlabel('평균 CNT수율 (g/g-cat)')
ax.set_title('작업자별 평균 수율 상위 5명')
ax.grid(axis='x', linestyle='--', alpha=0.7)

plt.tight_layout()

# 저장
output_path = os.path.join(OUT_DIR, "worker_top5_yield.png")
plt.savefig(output_path, dpi=300)
plt.close()
