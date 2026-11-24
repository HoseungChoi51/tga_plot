import pandas as pd
import matplotlib.pyplot as plt
import os

# 설정
OUT_DIR = "out/t3"
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

# 결측치 처리 (둘 중 하나라도 NaN인 행은 제외)
plot_df = df[[humidity_col, metal_col]].dropna().copy()

# 수치형으로 강제 변환 (문자열이나 기타 비수치 값이 섞여있을 경우 방지)
# errors='coerce'로 변환 실패 시 NaN으로 만들고 다시 dropna
plot_df[humidity_col] = pd.to_numeric(plot_df[humidity_col], errors='coerce')
plot_df[metal_col] = pd.to_numeric(plot_df[metal_col], errors='coerce')

# 최종적으로 유효한 수치만 남기기
plot_df = plot_df.dropna(subset=[humidity_col, metal_col])

# 플롯 그리기 (Scatter Plot)
fig, ax = plt.subplots(figsize=(8, 6))

ax.scatter(plot_df[humidity_col], plot_df[metal_col], 
           alpha=0.6, color='#2ca02c', edgecolors='w', s=50, label='개별 런')

# 축 레이블 및 제목
ax.set_xlabel("외기습도 (%)")
ax.set_ylabel("잔류금속 (wt%)")
ax.set_title("외기습도와 잔류금속 상관관계 (개별 런)")
ax.legend()
ax.grid(True, linestyle='--', alpha=0.5)

plt.tight_layout()
save_path = os.path.join(OUT_DIR, "scatter_humidity_metal.png")
plt.savefig(save_path, dpi=300)
plt.close()
