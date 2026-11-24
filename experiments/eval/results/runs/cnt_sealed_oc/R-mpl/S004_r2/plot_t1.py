import pandas as pd
import matplotlib.pyplot as plt
import os

# 환경 설정
OUT_DIR = "out/t1"
os.makedirs(OUT_DIR, exist_ok=True)

plt.rcParams["font.family"] = "Noto Sans CJK KR"
plt.rcParams["axes.unicode_minus"] = False

# 데이터 읽기
file_path = "data/run_log.xlsx"
df = pd.read_excel(file_path, sheet_name='런로그')

# 컬럼명 확인 및 매핑 (공백이나 특수문자 차이 대응)
cols = df.columns.tolist()
col_prod_speed = None
col_op_time = None
col_grade = None

for c in cols:
    c_clean = str(c).strip()
    if "생산속도" in c_clean:
        col_prod_speed = c
    elif "가동시간" in c_clean:
        col_op_time = c
    elif "등급" in c_clean:
        col_grade = c

if not all([col_prod_speed, col_op_time, col_grade]):
    raise ValueError(f"필수 컬럼을 찾을 수 없습니다. 사용 가능한 컬럼: {cols}")

# 숫자형으로 변환 (문자열이 섞여 있을 경우 에러 방지)
df[col_prod_speed] = pd.to_numeric(df[col_prod_speed], errors='coerce')
df[col_op_time] = pd.to_numeric(df[col_op_time], errors='coerce')

# 생산량 계산: 생산속도(g/h) * 가동시간(h) -> 단위: g
# kg 단위로 변환
df['생산량_kg'] = (df[col_prod_speed] * df[col_op_time]) / 1000

# 결측치 제거 후 등급별 합산
valid_df = df.dropna(subset=['생산량_kg', col_grade])
grade_grouped = valid_df.groupby(col_grade)['생산량_kg'].sum()

# 파이 차트 그리기
fig, ax = plt.subplots(figsize=(8, 6))

# 색상 매핑
custom_colors = {'A': '#4CAF50', 'B': '#2196F3', 'C': '#FFC107'}
color_list = [custom_colors.get(str(idx), '#gray') for idx in grade_grouped.index]

wedges, texts, autotexts = ax.pie(
    grade_grouped, 
    labels=grade_grouped.index, 
    autopct='%1.1f%%', 
    startangle=90,
    colors=color_list,
    textprops={'fontsize': 12}
)

ax.set_title('등급별 생산량 비중 (kg)', fontsize=14)
ax.axis('equal')  # 원형 유지

# 저장
save_path = os.path.join(OUT_DIR, 'production_by_grade_pie.png')
plt.tight_layout()
plt.savefig(save_path, dpi=300, bbox_inches='tight')
plt.close(fig)

print(f"Chart saved to {save_path}")
