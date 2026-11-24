import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import os

# 설정
OUT_DIR = "out/t1"
os.makedirs(OUT_DIR, exist_ok=True)
plt.rcParams["font.family"] = "Noto Sans CJK KR"
plt.rcParams['axes.unicode_minus'] = False

# 데이터 경로
file_path = "data/run_log.xlsx"

# 데이터 읽기 (시트 '런로그')
df = pd.read_excel(file_path, sheet_name="런로그")

# 컬럼 이름이 정확히 일치하지 않을 수 있으므로, 실제 컬럼 이름을 확인하고 매칭합니다.
# 미리보기에 따르면 '체류시간 (s)'와 'CNT수율 (g/g-cat)'가 있지만,
# 공백이나 괄호 형태 차이로 에러가 발생했습니다.
# 가장 유사한 컬럼을 찾아서 사용합니다.

col_x = None
for col in df.columns:
    if "체류시간" in str(col):
        col_x = col
        break

col_y = None
for col in df.columns:
    # CNT수율 컬럼을 찾되, '잔류금속'이나 다른 수율이 아닌 CNT 관련 수율을 우선 탐색
    if "CNT수율" in str(col):
        col_y = col
        break
    elif "수율" in str(col) and "금속" not in str(col) and "생산" not in str(col):
        # 혹시 이름이 다를 경우를 대비해 느슨하게 잡지만, 금속은 제외
        if col_y is None:
            col_y = col

if col_x is None or col_y is None:
    raise ValueError(f"컬럼을 찾을 수 없습니다. x: {col_x}, y: {col_y}. Available columns: {list(df.columns)}")

print(f"Using X column: '{col_x}'")
print(f"Using Y column: '{col_y}'")

# 결측치 처리 및 데이터 타입 변환
plot_df = df[[col_x, col_y]].dropna()

# 산점도(Spatter)를 그리려면 수치형(Numeric)이어야 합니다.
# Excel에서 텍스트로 저장되었거나 다른 형태로 들어왔을 수 있어 float로 강제 변환합니다.
try:
    plot_df[col_x] = pd.to_numeric(plot_df[col_x], errors='coerce')
    plot_df[col_y] = pd.to_numeric(plot_df[col_y], errors='coerce')
except Exception as e:
    print(f"Error converting types: {e}")

# 변환 후 다시 NaN 제거
plot_df = plot_df.dropna(subset=[col_x, col_y])

# 플롯 그리기
fig, ax = plt.subplots(figsize=(10, 7))

ax.scatter(plot_df[col_x], plot_df[col_y], alpha=0.6, edgecolors='w', s=50)

# 라벨 및 제목 설정
ax.set_xlabel(str(col_x), fontsize=12)
ax.set_ylabel(str(col_y), fontsize=12)
ax.set_title("Scatter Plot: 체류시간 vs CNT수율", fontsize=14)

# 격자 추가
ax.grid(True, linestyle="--", alpha=0.5)

# 파일 저장
output_file = os.path.join(OUT_DIR, "scatter_residence_time_vs_yield.png")
plt.tight_layout()
plt.savefig(output_file, dpi=300)
plt.close()
