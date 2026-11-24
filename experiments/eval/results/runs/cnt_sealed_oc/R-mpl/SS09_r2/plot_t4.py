import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import os

# 설정
OUT_DIR = "out/t4"
os.makedirs(OUT_DIR, exist_ok=True)
plt.rcParams["font.family"] = "Noto Sans CJK KR"
plt.rcParams["axes.unicode_minus"] = False

# 데이터 로드
file_path = "data/run_log.xlsx"
sheet_name = "런로그"

df = pd.read_excel(file_path, sheet_name=sheet_name)

# 컬럼명 매칭 (유연하게 처리)
humidity_col_name = None
metal_col_name = None
reactor_col_name = None

for col in df.columns:
    col_str = str(col)
    if '외기습도' in col_str:
        humidity_col_name = col
    elif '잔류금속' in col_str:
        metal_col_name = col
    elif '반응기' in col_str:
        reactor_col_name = col

if humidity_col_name is None or metal_col_name is None or reactor_col_name is None:
    raise ValueError("필요한 컬럼(외기습도, 잔류금속, 반응기)을 찾을 수 없습니다.")

# 수치형 변환 및 결측치 제거
df[humidity_col_name] = pd.to_numeric(df[humidity_col_name], errors='coerce')
df[metal_col_name] = pd.to_numeric(df[metal_col_name], errors='coerce')
df = df.dropna(subset=[humidity_col_name, metal_col_name])

# 플롯 생성
fig, ax = plt.subplots(figsize=(12, 8))

# 반응기별 색상 지정 (R1-R4)
colors = {'R1': '#1f77b4', 'R2': '#ff7f0e', 'R3': '#2ca02c', 'R4': '#d62728'}

# 각 반응기별로 데이터를 분리하여 산점도 그리기
unique_reactors = df[reactor_col_name].dropna().unique()

for reactor in unique_reactors:
    subset = df[df[reactor_col_name] == reactor]
    color = colors.get(reactor, 'gray') # 기본 회색으로 처리
    
    ax.scatter(subset[humidity_col_name], 
               subset[metal_col_name], 
               alpha=0.6, 
               color=color, 
               edgecolors='w', 
               s=50, 
               label=f'{reactor}')

# 축 레이블 및 제목
ax.set_title('반응기별 외기습도와 잔류금속 관계 산점도', fontsize=14)
ax.set_xlabel(f'{humidity_col_name}', fontsize=12)
ax.set_ylabel(f'{metal_col_name}', fontsize=12)

# 그리드 추가
ax.grid(True, linestyle='--', alpha=0.7)

# 범례 표시 (위치 조정)
ax.legend(loc='upper right', title='반응기')

# 레이아웃 조정
plt.tight_layout()

# 저장
save_path = os.path.join(OUT_DIR, "scatter_humidity_metal_by_reactor.png")
plt.savefig(save_path, dpi=300)
plt.close()

print(f"그림이 {save_path}에 저장되었습니다.")
