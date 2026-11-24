import pandas as pd
import matplotlib.pyplot as plt
import os

# 설정
OUT_DIR = "out/t2"
os.makedirs(OUT_DIR, exist_ok=True)
plt.rcParams["font.family"] = "Noto Sans CJK KR"
plt.rcParams["axes.unicode_minus"] = False

# 데이터 읽기
file_path = "data/run_log.xlsx"
sheet_name = "런로그"
df = pd.read_excel(file_path, sheet_name=sheet_name)

# 열 이름 확인 및 매핑 (공백이나 특수문자 차이 가능성 대비)
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

# 막대 차트 그리기
fig, ax = plt.subplots(figsize=(8, 6))
bars = ax.bar(reactor_production.index, reactor_production.values, color=plt.cm.Paired.colors[:len(reactor_production)])

# 각 막대 위에 값 표시 (kg 단위로 변환하여 표시하거나 g 그대로 표시 가능. 요청은 '비중'이였지만 이제 '막대'로 변경됨. 절대값인 생산량을 나타냄.)
# 합계를 구해 백분율로 보여줄지, 절대량을 보여줄지 결정 필요. 이전 요청은 '비중'이었으나 이번에는 단순히 '이걸 막대로 바꿔 주세요'라고 함.
# 파이차트가 비중이었으므로, 막대 차트도 보통 절대량 또는 상대량을 모두 보여줄 수 있음. 
# 일반적으로 생산량은 kg 단위가 더 직관적일 수 있으나 데이터는 g임. 
# 여기서는 총 생산량(kg)으로 환산하여 y축 라벨과 값을 표시하는 것이 실무에서 더 유용할 수 있음.
# 하지만 원본 데이터 단위인 g를 유지하되, 큰 숫자라 readability 위해 kg로 변환해서 plotting 하는 것도 좋음.
# 일단 계산된 값이 g이므로, 그래프에서는 kg으로 변환해서 보여주는 게 낫겠음.

production_kg = reactor_production / 1000.0

ax.clear() # 다시 그려야 함
bars = ax.bar(reactor_production.index, production_kg.values, color=plt.cm.Paired.colors[:len(reactor_production)])

# 값 텍스트 추가
for bar in bars:
    height = bar.get_height()
    ax.text(bar.get_x() + bar.get_width()/2., height,
            f'{height:.1f}',
            ha='center', va='bottom', fontsize=10)

ax.set_ylabel('총 생산량 (kg)', fontsize=12)
ax.set_xlabel('반응기', fontsize=12)
ax.set_title("반응기별 총 생산량", fontsize=14, pad=20)

# y축 범위 조정 (여백 확보)
max_val = production_kg.max()
ax.set_ylim(0, max_val * 1.15)

plt.tight_layout()

# 저장
save_path = os.path.join(OUT_DIR, "reactor_production_bar.png")
plt.savefig(save_path, dpi=300, bbox_inches='tight')
plt.close(fig)
