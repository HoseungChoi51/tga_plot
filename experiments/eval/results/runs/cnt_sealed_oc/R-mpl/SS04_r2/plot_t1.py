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
sheet_name = "런로그"
df = pd.read_excel(file_path, sheet_name=sheet_name)

# 열 이름 확인 및 매핑 (공백이나 특수문자 차이 가능성 대비하여 정규화 접근보다는 미리보기 기준의 정확한 이름 사용 시도)
# 미리보기: R 생산속도 (g/h), P 가동시간 (h)
# 만약 에러가 난다면 공백 문제일 수 있음. 하지만 위 에러는 '생산속도 (g/h)'를 못 찾음.
# 엑셀 파일의 실제 헤더가 다를 수 있으므로, 가장 안전한 방법은 컬럼명을 찾아서 할당하는 것임.
cols = df.columns.tolist()
prod_col = None
time_col = None
reactor_col = None

for c in cols:
    if '생산속도' in str(c):
        prod_col = c
    if '가동시간' in str(c):
        time_col = c
    if '반응기' in str(c):
        reactor_col = c

if prod_col is None or time_col is None or reactor_col is None:
    raise ValueError(f"필수 컬럼을 찾을 수 없습니다. Found columns: {cols}")

# 생산량 계산 (g): 생산속도(g/h) × 가동시간(h)
df['생산속도_g_h'] = pd.to_numeric(df[prod_col], errors='coerce')
df['가동시간_h'] = pd.to_numeric(df[time_col], errors='coerce')
df['총생산량_g'] = df['생산속도_g_h'] * df['가동시간_h']

# 반응기별 총 생산량 집계
reactor_production = df.groupby(reactor_col)['총생산량_g'].sum()

# 파이차트 그리기
fig, ax = plt.subplots(figsize=(8, 6))
wedges, texts, autotexts = ax.pie(
    reactor_production.values,
    labels=reactor_production.index,
    autopct='%1.1f%%',
    startangle=90,
    colors=plt.cm.Paired.colors[:len(reactor_production)]
)

ax.set_title("반응기별 총 생산량 비중", fontsize=14, pad=20)

# 한국어 폰트 적용 확인을 위해 tight_layout 사용
plt.tight_layout()

# 저장
save_path = os.path.join(OUT_DIR, "reactor_production_pie.png")
plt.savefig(save_path, dpi=300, bbox_inches='tight')
plt.close(fig)
