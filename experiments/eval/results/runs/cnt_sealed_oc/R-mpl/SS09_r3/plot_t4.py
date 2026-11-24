import pandas as pd
import matplotlib.pyplot as plt
import os

# 설정
OUT_DIR = "out/t4"
os.makedirs(OUT_DIR, exist_ok=True)
plt.rcParams["font.family"] = "Noto Sans CJK KR"
plt.rcParams["axes.unicode_minus"] = False

# 데이터 읽기
file_path = "data/run_log.xlsx"
df = pd.read_excel(file_path, sheet_name="런로그")

# 컬럼명 공백 제거 및 통일
df.columns = df.columns.str.strip()

# 외기습도 컬럼 찾기
humidity_col = None
for col in df.columns:
    if '외기습도' in str(col):
        humidity_col = col
        break

if humidity_col is None:
    raise ValueError("외기습도 컬럼을 찾을 수 없습니다.")

# 잔류금속 컬럼 찾기
metal_col = None
for col in df.columns:
    if '잔류금속' in str(col):
        metal_col = col
        break

if metal_col is None:
    raise ValueError("잔류금속 컬럼을 찾을 수 없습니다.")

# 반응기 컬럼 확인 (미리보기에 '반응기'가 있음)
reactor_col = None
for col in df.columns:
    if '반응기' in str(col):
        reactor_col = col
        break

if reactor_col is None:
    # 만약 이름이 다르다면 첫 번째 컬럼 중 텍스트형인 것을 추측하거나 에러 처리 가능하지만, 미리보기 기준 사용
    raise ValueError("반응기 컬럼을 찾을 수 없습니다.")

# 결측치 및 타입 변환 처리
plot_df = df[[humidity_col, metal_col, reactor_col]].dropna().copy()

# 수치형으로 강제 변환
plot_df[humidity_col] = pd.to_numeric(plot_df[humidity_col], errors='coerce')
plot_df[metal_col] = pd.to_numeric(plot_df[metal_col], errors='coerce')

# 최종적으로 유효한 수치만 남기기
plot_df = plot_df.dropna(subset=[humidity_col, metal_col])

# 반응기별 색상 매핑 정의
# R1~R4에 대해 구분 가능한 색상이나 스타일 지정
reactors = sorted(plot_df[reactor_col].unique())
colors = ['#e41a1c', '#377eb8', '#4daf4a', '#984ea3'] # 빨강, 파랑, 초록, 보라 등 대비 좋은 색상
# 반응기가 4개 이상이면 색상을 더 늘리거나 반복되도록 설정 가능하지만 보통 R1-R4임
color_map = {r: colors[i % len(colors)] for i, r in enumerate(reactors)}

# 플롯 그리기 (Scatter Plot with Hue)
fig, ax = plt.subplots(figsize=(10, 7))

for reactor in reactors:
    subset = plot_df[plot_df[reactor_col] == reactor]
    ax.scatter(subset[humidity_col], subset[metal_col], 
               color=color_map[reactor], 
               alpha=0.6, edgecolors='w', s=50, label=f'{reactor}')

# 축 레이블 및 제목
ax.set_xlabel("외기습도 (%)")
ax.set_ylabel("잔류금속 (wt%)")
ax.set_title("반응기별 외기습도와 잔류금속 상관관계 (개별 런)")
ax.legend(title="반응기", loc='best')
ax.grid(True, linestyle='--', alpha=0.5)

plt.tight_layout()
save_path = os.path.join(OUT_DIR, "scatter_humidity_metal_by_reactor.png")
plt.savefig(save_path, dpi=300)
plt.close()
