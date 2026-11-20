import pandas as pd
import matplotlib.pyplot as plt
import os

# 설정
OUT_DIR = "out/t1"
os.makedirs(OUT_DIR, exist_ok=True)

plt.rcParams["font.family"] = "Noto Sans CJK KR"
plt.rcParams["axes.unicode_minus"] = False

# 데이터 로드
file_path = "data/run_log.xlsx"
df = pd.read_excel(file_path, sheet_name="런로그")

# 열 이름 확인 및 처리
cols = df.columns.tolist()
col_speed = [c for c in cols if '생산속도' in c][0]
col_time = [c for c in cols if '가동시간' in c][0]
col_grade = [c for c in cols if '등급' in c][0]

# 숫자열로 변환 (문자열인 경우 float로 강제 변환 시도)
# 에러 원인: 'can't multiply sequence by non-int of type 'str''
# 즉, 해당 컬럼에 문자열 값이 섞여 있거나 전체가 object dtype일 가능성이 높음.
try:
    df[col_speed] = pd.to_numeric(df[col_speed], errors='coerce')
    df[col_time] = pd.to_numeric(df[col_time], errors='coerce')
except Exception as e:
    print(f"Numeric conversion failed: {e}")

# 결측치(NaN) 제거 또는 0으로 대체하여 계산 진행
# 여기서는 계산 가능한 행만 남기고 진행합니다.
df_clean = df.dropna(subset=[col_speed, col_time, col_grade])

# 생산량 계산: 생산속도 (g/h) * 가동시간 (h) -> g 단위로 계산 후 kg 변환
df_clean['생산량_g'] = df_clean[col_speed] * df_clean[col_time]
df_clean['생산량_kg'] = df_clean['생산량_g'] / 1000

# 등급별 합산
grade_totals = df_clean.groupby(col_grade)['생산량_kg'].sum()

# 파이 차트 그리기
fig, ax = plt.subplots(figsize=(8, 6))

# 색상 매핑을 위해 정렬된 인덱스 사용
grade_totals = grade_totals.sort_index()

# 자동 색상 팔레트 사용
import numpy as np
cmap = plt.get_cmap('tab10')
n_grades = len(grade_totals)
colors_auto = [cmap(i) for i in range(n_grades)]

ax.pie(grade_totals.values, labels=grade_totals.index, autopct='%1.1f%%', startangle=90, colors=colors_auto)
ax.axis('equal') # 동그란 원 유지
ax.set_title('등급별 생산량 비중 (kg 기준)')

plt.tight_layout()
plt.savefig(os.path.join(OUT_DIR, "production_by_grade_pie.png"), dpi=300)
plt.close()
