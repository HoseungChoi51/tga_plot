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
df = pd.read_excel(file_path, sheet_name='런로그')

# 열 이름 매칭 함수: 부분 일치 검색을 통해 정확한 컬럼명을 찾습니다.
def find_col(df, keyword):
    for col in df.columns:
        if keyword in str(col):
            return col
    raise ValueError(f"'{keyword}'을(를) 포함하는 컬럼을 찾을 수 없습니다.")

col_grade = find_col(df, '등급')
col_metal = find_col(df, '잔류금속')
col_raman = find_col(df, 'IG/ID')

print(f"Found columns: Grade='{col_grade}', Metal='{col_metal}', Raman='{col_raman}'")

# 등급 C인 런만 필터링
df_c = df[df[col_grade] == 'C'].copy()

# 불합격 사유 분류 함수
def classify_failure(row):
    # 각 컬럼에 접근하여 조건 검사
    high_metal = row[col_metal] > 5.0
    low_raman = row[col_raman] < 2.2
    
    if high_metal and low_raman:
        return '둘 다'
    elif high_metal:
        return '잔류금속 > 5.0 wt%만'
    elif low_raman:
        return 'IG/ID < 2.2만'
    else:
        # 명시된 세 가지 카테고리에 해당하지 않는 경우 (데이터 정합성 확인용)
        # 요청사항에는 세 가지로 나눠 달라고 했으므로, 이 외의 케이스는 파이 차트에서 제외합니다.
        return None

df_c['불합격사유'] = df_c.apply(classify_failure, axis=1)

# 유효한 사유가 있는 데이터만 추출
df_valid = df_c.dropna(subset=['불합격사유'])

if df_valid.empty:
    print("경고: 분류된 불합격 사유가 없습니다. 빈 차트를 생성합니다.")
    labels = []
    sizes = []
else:
    # 각 사유별 개수 집계
    counts = df_valid['불합격사유'].value_counts()
    
    # 파이 차트 그리기 준비
    # 라벨과 크기를 정렬 순서에 맞춰 준비합니다.
    # 시각적 일관성을 위해 특정 순서(예: 둘다, 금속만, IG/ID만)로 재배열할 수도 있지만,
    # value_counts 기본 순서(빈도순)를 따르는 것이 일반적입니다.
    labels = counts.index.tolist()
    sizes = counts.values.tolist()

fig, ax = plt.subplots(figsize=(8, 6))

if len(sizes) > 0:
    # 색상 지정
    colors = ['#ff9999', '#66b3ff', '#99ff99', '#ffff99']
    
    wedges, texts, autotexts = ax.pie(sizes, 
                                      labels=labels, 
                                      autopct='%1.1f%%', 
                                      startangle=90, 
                                      counterclock=False, 
                                      colors=colors[:len(sizes)])
    
    ax.axis('equal')
    ax.set_title('등급 C 런의 불합격 사유 비율')
else:
    ax.text(0.5, 0.5, '데이터 없음', ha='center', va='center')
    ax.set_title('등급 C 런의 불합격 사유 비율')
    ax.axis('off')

# 저장
output_path = os.path.join(OUT_DIR, 'grade_c_failure_pie.png')
plt.savefig(output_path, dpi=300, bbox_inches='tight')
plt.close()
