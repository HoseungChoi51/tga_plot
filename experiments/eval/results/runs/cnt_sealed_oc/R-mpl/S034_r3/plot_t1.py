import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import os

# 설정
plt.rcParams["font.family"] = "Noto Sans CJK KR"
OUT_DIR = "out/t1"
os.makedirs(OUT_DIR, exist_ok=True)

# 데이터 읽기
file_path = "data/run_log.xlsx"
df = pd.read_excel(file_path, sheet_name="런로그")

# 컬럼명 확인 및 매칭 (미리보기의 헤더와 실제 파일의 공백/특수문자 차이 가능성 대응)
# 미리보기: '2존온도 (°C)', 'CNT수율 (g/g-cat)'
# 오류 메시지: 해당 컬럼이 없음 -> 실제 컬럼명이 다를 수 있음. 
# 안전한 방법: 컬럼명에 키워드가 포함된 것을 찾음.

col_zone2 = None
col_yield = None

for c in df.columns:
    # 2존 온도 찾기
    if "2존" in str(c) and ("온도" in str(c) or "temp" in str(c).lower()):
        col_zone2 = c
    # CNT 수율 찾기
    if "수율" in str(c) or "yield" in str(c).lower():
        col_yield = c

# 만약 명시적으로 안 잡히면 인덱스나 다른 방식으로 보완 (예시 데이터 기준으로는 위 조건으로 충분할 것으로 예상)
if col_zone2 is None:
    # 폴백: 열 이름에 숫자 2와 온도가 있는 것 중 가장 가까운 것 등 복잡한 로직 대신,
    # 미리보기 순서를 신뢰하여 위치로 찾을 수도 있으나, 여기서는 키워드 매칭을 우선함.
    # 그래도 없으면 에러 처리를 위해 기본값 시도
    possible_cols = [c for c in df.columns if "2존" in str(c)]
    if possible_cols:
        col_zone2 = possible_cols[0]
    else:
        raise ValueError("2존 온도 컬럼을 찾을 수 없습니다.")

if col_yield is None:
    possible_cols = [c for c in df.columns if "수율" in str(c)]
    if possible_cols:
        col_yield = possible_cols[0]
    else:
        raise ValueError("CNT 수율 컬럼을 찾을 수 없습니다.")

print(f"Using columns: Zone2='{col_zone2}', Yield='{col_yield}'")

# 결측치 제거 및 타입 변환 확인
# 숫자로 변환 시도 (비숫자 문자열 등이 섞여 있을 경우 대비)
df[col_zone2] = pd.to_numeric(df[col_zone2], errors='coerce')
df[col_yield] = pd.to_numeric(df[col_yield], errors='coerce')

df_plot = df[[col_zone2, col_yield]].dropna()

# 그래프 그리기: 산점도 + 회귀선
fig, ax = plt.subplots(figsize=(10, 7))

# 1. 산점도
ax.scatter(df_plot[col_zone2], df_plot[col_yield], alpha=0.6, edgecolors='w', s=50, label='개별 런 데이터')

# 2. 선형 추세선
z = np.polyfit(df_plot[col_zone2], df_plot[col_yield], 1)
p = np.poly1d(z)
x_line = np.linspace(df_plot[col_zone2].min(), df_plot[col_zone2].max(), 100)
ax.plot(x_line, p(x_line), "r--", linewidth=2, label=f'선형 추세선 (y={z[0]:.2f}x+{z[1]:.2f})')

# 축 라벨 및 제목
ax.set_xlabel(col_zone2, fontsize=12)
ax.set_ylabel(col_yield, fontsize=12)
ax.set_title("2존 온도와 CNT 수율의 관계", fontsize=14, fontweight='bold')
ax.legend(loc='best')
ax.grid(True, linestyle=':', alpha=0.5)

# 상관계수 계산하여 텍스트로 표시
correlation = df_plot[col_zone2].corr(df_plot[col_yield])
ax.text(0.05, 0.95, f'상관계수 (Pearson): {correlation:.3f}', transform=ax.transAxes, fontsize=10, verticalalignment='top', bbox=dict(boxstyle='round,pad=0.5', facecolor='white', alpha=0.8))

plt.tight_layout()

# 저장
save_path = os.path.join(OUT_DIR, "zone2_temp_vs_yield.png")
plt.savefig(save_path, dpi=300)
plt.close()
