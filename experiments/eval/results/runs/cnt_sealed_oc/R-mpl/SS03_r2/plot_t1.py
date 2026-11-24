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

# 컬럼명 확인 및 매핑
# 실제 파일의 헤더는 공백이나 특수문자 차이로 인해 '등급 (A/B/C)'와 다를 수 있음
# 가장 유사한 컬럼명을 찾거나, 일반적으로 마지막 컬럼이 등급일 가능성이 높으므로 처리함
grade_col = None
for col in df.columns:
    if '등급' in str(col):
        grade_col = col
        break

if grade_col is None:
    # 만약 '등급'이라는 단어가 없으면 마지막 컬럼을 가정 (데이터 미리보기상 V열이 등급)
    grade_col = df.columns[-1]

# 데이터 전처리: 등급 컬럼 확인 및 필터링
# A·B 등급을 합격으로 간주
# 값에 공백 등이 있을 수 있어 strip() 적용 후 비교
df['합격 여부'] = df[grade_col].astype(str).str.strip().isin(['A', 'B'])

# 반응기별 통계 계산
# 1. 각 반응기의 총 런 수
total_runs = df.groupby('반응기')['런ID'].count()

# 2. 각 반응기의 합격(A+B) 런 수
pass_runs = df[df['합격 여부']].groupby('반응기')['런ID'].count()

# 3. 합격률 (%) 계산
# pass_runs가 없는 반응기가 있을 수 있으므로 reindex로 채우고 fillna(0) 처리
pass_ratio = (pass_runs.reindex(total_runs.index).fillna(0) / total_runs * 100)

# 정렬 (R1, R2, R3, R4 순서대로 표시하기 위해 인덱스 재정렬, 만약 데이터에 없으면 있는 것만 사용)
reactors = sorted(df['반응기'].unique())
pass_ratio = pass_ratio.reindex(reactors)

# 그래프 그리기
fig, ax = plt.subplots(figsize=(8, 6))

bars = ax.bar(reactors, pass_ratio.values, color='skyblue', edgecolor='black')

# 값 라벨 추가
for bar in bars:
    height = bar.get_height()
    ax.text(bar.get_x() + bar.get_width()/2., height + 1,
            f'{height:.1f}%',
            ha='center', va='bottom', fontsize=12)

ax.set_title('반응기별 합격률 (A·B 등급)', fontsize=16, pad=15)
ax.set_xlabel('반응기', fontsize=14)
ax.set_ylabel('합격률 (%)', fontsize=14)
ax.set_ylim(0, 110) # y축 상단 여백 확보
ax.grid(axis='y', linestyle='--', alpha=0.7)

plt.tight_layout()

# 저장
output_file = os.path.join(OUT_DIR, "reactor_pass_rate.png")
plt.savefig(output_file, dpi=300)
plt.close()
