import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import os

# 설정
plt.rcParams["font.family"] = "Noto Sans CJK KR"
plt.rcParams["axes.unicode_minus"] = False

OUT_DIR = "out/t1"
os.makedirs(OUT_DIR, exist_ok=True)

# 데이터 읽기
file_path = "data/diameters.csv"
df = pd.read_csv(file_path)

# 컬럼 이름 확인 (미리보기 기준: '직경(nm)' 등일 수 있음, 혹은 영문/한글 혼재 가능성)
# 미리보기에 'D 직경(nm)'이라고 되어있으므로 실제 컬럼명은 '직경(nm)' 또는 유사할 것으로 예상
# 안전한 처리를 위해 포함 문자열로 찾기
col_name = None
for col in df.columns:
    if '직경' in col or 'diameter' in col.lower() or 'nm' in col:
        col_name = col
        break

if col_name is None:
    # 마지막 컬럼이 수치형인 경우 fallback
    numeric_cols = df.select_dtypes(include=[np.number]).columns
    if len(numeric_cols) > 0:
        col_name = numeric_cols[-1]
    else:
        raise ValueError("Could not find diameter column")

# 직경 데이터 추출 및 결측치 제거
diameters = df[col_name].dropna()

# 필터링: 요청된 범위 4~28 nm 내의 데이터만 사용 (히스토그램 범위에 맞추기 위해 전체 데이터를 쓰되 bins 설정으로 제한하거나, 먼저 필터링)
# bin 폭 0.5, range 4-28 -> bins count = (28-4)/0.5 = 48 bins
bins = np.arange(4, 28 + 0.5, 0.5)

# 통계량 계산
mean_val = diameters.mean()
median_val = diameters.median()

# 플롯 그리기
fig, ax = plt.subplots(figsize=(10, 6))

ax.hist(diameters, bins=bins, edgecolor='black', alpha=0.7, color='skyblue')

# 평균 및 중앙값 세로선
ax.axvline(mean_val, color='red', linestyle='--', linewidth=2, label=f'평균: {mean_val:.2f} nm')
ax.axvline(median_val, color='green', linestyle='-.', linewidth=2, label=f'중앙값: {median_val:.2f} nm')

# 라벨 및 제목
ax.set_xlabel('직경 (nm)', fontsize=12)
ax.set_ylabel('빈도 (Count)', fontsize=12)
ax.set_title('TEM 직경 분포 히스토그램 (전체 시료 합산)', fontsize=14)
ax.legend(loc='upper right')

# x축 범위 설정
ax.set_xlim(4, 28)

plt.tight_layout()

# 저장
save_path = os.path.join(OUT_DIR, "tem_diameter_histogram.png")
plt.savefig(save_path, dpi=300)
plt.close(fig)

print(f"Plot saved to {save_path}")
