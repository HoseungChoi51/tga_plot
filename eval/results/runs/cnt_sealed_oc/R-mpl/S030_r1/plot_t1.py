import pandas as pd
import matplotlib.pyplot as plt
import os

# 환경 설정
plt.rcParams["font.family"] = "Noto Sans CJK KR"
OUT_DIR = "out/t1"
os.makedirs(OUT_DIR, exist_ok=True)

# 데이터 읽기
file_path = "data/run_log.xlsx"
df = pd.read_excel(file_path, sheet_name="런로그")

# 열 이름 매칭 함수: 키워드를 포함하는 실제 컬럼명을 찾음
def find_column(df, keywords):
    for col in df.columns:
        if all(kw in str(col) for kw in keywords):
            return col
    # 부분 일치 시도 (공백/특수문자 차이 대비)
    for col in df.columns:
        clean_col = str(col).replace(' ', '').replace('(', '').replace(')', '')
        if all(kw.replace(' ', '') in clean_col for kw in keywords):
            return col
    raise ValueError(f"컬럼을 찾을 수 없습니다: {keywords}")

# 필요한 컬럼명 확인
col_grade = find_column(df, ['등급'])
col_metal = find_column(df, ['잔류금속'])
col_raman = find_column(df, ['IG/ID', 'I_G/I_D', 'G/D']) # Raman 관련 명칭 유연하게 처리

# 등급 C 판정 런 필터링
df_c = df[df[col_grade] == 'C'].copy()

# 불합격 사유 분류
# 1. 잔류금속 > 5.0 wt% AND IG/ID >= 2.2 -> '잔류금속 > 5.0 wt%만'
# 2. 잔류금속 <= 5.0 wt% AND IG/ID < 2.2 -> 'IG/ID < 2.2만'
# 3. 잔류금속 > 5.0 wt% AND IG/ID < 2.2 -> '둘 다'

# 조건 정의
cond_metal_only = (df_c[col_metal] > 5.0) & (df_c[col_raman] >= 2.2)
cond_raman_only = (df_c[col_metal] <= 5.0) & (df_c[col_raman] < 2.2)
cond_both = (df_c[col_metal] > 5.0) & (df_c[col_raman] < 2.2)

# 카운트
count_metal_only = cond_metal_only.sum()
count_raman_only = cond_raman_only.sum()
count_both = cond_both.sum()

labels = ['잔류금속 > 5.0 wt%만', 'IG/ID < 2.2만', '둘 다']
sizes = [count_metal_only, count_raman_only, count_both]

# 파이 차트 그리기
fig, ax = plt.subplots(figsize=(8, 6))
colors = ['#ff9999', '#66b3ff', '#99ff99']

# 모든 값이 0인 경우 처리 방지
if sum(sizes) > 0:
    wedges, texts, autotexts = ax.pie(
        sizes, 
        labels=labels, 
        autopct='%1.1f%%', 
        startangle=90, 
        colors=colors,
        textprops={'fontsize': 12}
    )
    ax.axis('equal')
    ax.set_title(f"등급 C 판정 런의 불합격 사유 분포 (총 {sum(sizes)}건)", fontsize=14, pad=20)
else:
    ax.text(0.5, 0.5, '데이터가 없거나 기준에 부합하는 런이 없습니다.', ha='center', va='center', fontsize=12)
    ax.axis('off')

# 저장
output_file = os.path.join(OUT_DIR, "grade_c_failure_reasons_pie.png")
plt.tight_layout()
plt.savefig(output_file, dpi=300, bbox_inches='tight')
plt.close()
