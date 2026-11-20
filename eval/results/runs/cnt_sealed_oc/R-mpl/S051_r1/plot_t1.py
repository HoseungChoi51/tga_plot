import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import os

# 설정
OUT_DIR = "out/t1"
os.makedirs(OUT_DIR, exist_ok=True)

# 폰트 설정 (한글 지원)
plt.rcParams["font.family"] = "Noto Sans CJK KR"
plt.rcParams["axes.unicode_minus"] = False

# 데이터 읽기
file_path = "data/run_log.xlsx"
df = pd.read_excel(file_path, sheet_name="런로그")

# 열 이름 정리: 공백이나 특수문자로 인한 매칭 오류 방지
# 미리보기에 따르면 정확한 열 이름은 다음과 같습니다:
# N 체류시간 (s), Q CNT수율 (g/g-cat), P 가동시간 (h)
# 하지만 Excel에서 읽을 때 줄바꿈 문자(\n)나 불필요한 공백이 포함될 수 있으므로
# 안전하게 처리합니다.

def clean_column_names(cols):
    return [col.replace('\n', ' ').strip() for col in cols]

df.columns = clean_column_names(df.columns)

# 주차 열을 숫자로 변환 (문자열로 읽혔을 경우 대비)
try:
    df["주차"] = pd.to_numeric(df["주차"], errors='coerce')
except Exception:
    pass

# 필터링: 주차 14~26, 반응기 R1 또는 R2
filtered_df = df[
    (df["주차"] >= 14) & 
    (df["주차"] <= 26) & 
    (df["반응기"].isin(["R1", "R2"]))
].copy()

# 필요한 컬럼 확인 및 결측치 제거
# 열 이름이 정확히 일치하는지 확인
cols_to_check = ["체류시간 (s)", "CNT수율 (g/g-cat)", "가동시간 (h)"]
missing_cols = [c for c in cols_to_check if c not in filtered_df.columns]

if missing_cols:
    raise ValueError(f"Missing columns after cleaning: {missing_cols}. Available: {list(filtered_df.columns)}")

filtered_df = filtered_df.dropna(subset=cols_to_check)

# 플롯 생성
fig, ax = plt.subplots(figsize=(10, 7))

# 산점도: x=체류시간, y=CNT수율, size ∝ 가동시간
size_factor = 15 
scatter = ax.scatter(
    filtered_df["체류시간 (s)"],
    filtered_df["CNT수율 (g/g-cat)"],
    s=filtered_df["가동시간 (h)"] * size_factor,
    c=filtered_df["반응기"].map({"R1": "#d62728", "R2": "#1f77b4"}), # 색상으로 반응기 구분
    alpha=0.6,
    edgecolors='w',
    linewidth=0.5
)

# 레이어 추가 및 라벨링
ax.set_xlabel("체류시간 (s)")
ax.set_ylabel("CNT수율 (g/g-cat)")
ax.set_title("주차 14–26, 반응기 R1/R2의 체류시간 vs CNT수율 산점도\n(마커 크기 ∝ 가동시간)")

# 범례: 반응기 색상 범례 추가
from matplotlib.patches import Patch
legend_elements = [
    Patch(facecolor='#d62728', label='R1'),
    Patch(facecolor='#1f77b4', label='R2')
]
ax.legend(handles=legend_elements, title="반응기", loc="best")

# 가동시간 크기에 대한 참고 정보 추가 (텍스트로)
if not filtered_df.empty:
    min_time = filtered_df["가동시간 (h)"].min()
    max_time = filtered_df["가동시간 (h)"].max()
    info_text = f"마커 크기 범위: {min_time:.1f} ~ {max_time:.1f} h"
    ax.text(0.95, 0.05, info_text, transform=ax.transAxes, fontsize=9, verticalalignment='bottom', horizontalalignment='right')

# 격자
ax.grid(True, linestyle="--", alpha=0.5)

# 저장
output_filename = "scatter_residence_time_vs_yield_R1R2.png"
output_path = os.path.join(OUT_DIR, output_filename)
plt.tight_layout()
plt.savefig(output_path, dpi=300)
plt.close()

print(f"Plots saved to {output_path}")
