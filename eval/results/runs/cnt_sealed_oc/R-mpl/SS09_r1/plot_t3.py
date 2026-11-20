import pandas as pd
import matplotlib.pyplot as plt
import os

# 설정
plt.rcParams["font.family"] = "Noto Sans CJK KR"
OUT_DIR = "out/t3"
os.makedirs(OUT_DIR, exist_ok=True)

# 데이터 읽기
file_path = "data/run_log.xlsx"
df = pd.read_excel(file_path, sheet_name="런로그")

# 열 이름 공백 제거 및 정리
df.columns = df.columns.str.strip()

# 필요한 컬럼 이름 찾기 (공백 variations 고려)
humidity_col = None
metal_col = None

for col in df.columns:
    if '외기습도' in col:
        humidity_col = col
    if '잔류금속' in col:
        metal_col = col

if humidity_col is None or metal_col is None:
    raise ValueError("Required columns (Humidity or Residual Metal) not found.")

# 결측치 처리 및 수치형으로 강제 변환
# 에러가 'float' 타입을 기대하는 곳에서 문자열이 들어와 발생한 것으로 추정되므로, 
# 해당 컬럼들을 명시적으로 float로 변환합니다.
plot_df = df[[humidity_col, metal_col]].copy()
plot_df[humidity_col] = pd.to_numeric(plot_df[humidity_col], errors='coerce')
plot_df[metal_col] = pd.to_numeric(plot_df[metal_col], errors='coerce')

# 변환 과정에서 생긴 NaN 제거
plot_df = plot_df.dropna()

# 플롯팅: 산점도 (Scatter Plot)
fig, ax = plt.subplots(figsize=(10, 8))

ax.scatter(plot_df[humidity_col], plot_df[metal_col], alpha=0.6, edgecolors='w', s=50, color='tab:blue')

# 축 설정
ax.set_xlabel(humidity_col)
ax.set_ylabel(metal_col)
ax.set_title('외기습도와 잔류금속의 상관관계 (런 단위)')
ax.grid(True, linestyle='--', alpha=0.5)

# 저장
output_file = os.path.join(OUT_DIR, "humidity_vs_metal_scatter.png")
plt.tight_layout()
plt.savefig(output_file, dpi=300)
plt.close()
