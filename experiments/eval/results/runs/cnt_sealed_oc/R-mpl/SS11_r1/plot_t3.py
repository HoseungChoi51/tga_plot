import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import os

# 설정
OUT_DIR = "out/t3"
os.makedirs(OUT_DIR, exist_ok=True)

# 폰트 설정 (한글 지원)
plt.rcParams["font.family"] = "Noto Sans CJK KR"
plt.rcParams['axes.unicode_minus'] = False  # 마이너스 부호 깨짐 방지

# 데이터 읽기
file_path = "data/doe_temp_h2.csv"
try:
    df = pd.read_csv(file_path, encoding='utf-8')
except UnicodeDecodeError:
    try:
        df = pd.read_csv(file_path, encoding='cp949')
    except Exception as e:
        raise ValueError(f"파일 인코딩 오류: {e}")

# 피벗 테이블 생성: 온도(x축), H2비(y축), 수율(값)
pivot_df = df.pivot_table(values='수율(g/g-cat)', index='H2/C2H4비', columns='2존온도(°C)', aggfunc='mean')

# 그래프 그리기
fig, ax = plt.subplots(figsize=(10, 7))

# 히트맵绘制
im = ax.imshow(pivot_df.values, cmap='YlOrRd', aspect='auto')

# 눈금 및 라벨 설정
ax.set_xticks(np.arange(len(pivot_df.columns)))
ax.set_yticks(np.arange(len(pivot_df.index)))
ax.set_xticklabels(pivot_df.columns)
ax.set_yticklabels(pivot_df.index)

# 회전 없이 중앙 정렬
plt.setp(ax.get_xticklabels(), rotation=0, ha="center", rotation_mode="anchor")

# 각 셀에 값 텍스트 추가
for i in range(len(pivot_df.index)):
    for j in range(len(pivot_df.columns)):
        text = ax.text(j, i, f"{pivot_df.iloc[i, j]:.1f}",
                       ha="center", va="center", color="black" if pivot_df.iloc[i, j] > (pivot_df.max().max() * 0.6) else "white")

# 색상 막대 추가
cbar = ax.figure.colorbar(im, ax=ax)
cbar.ax.set_ylabel('평균 수율 (g/g-cat)', rotation=-90, va="bottom", fontsize=12)

# 축 제목
ax.set_xlabel('2존 온도 (°C)', fontsize=12)
ax.set_ylabel('H2/C2H4 비', fontsize=12)
ax.set_title('DOE 결과: 온도와 H2/C2H4 비에 따른 CNT 수율 히트맵', fontsize=16)

plt.tight_layout()

# 저장
output_filename = os.path.join(OUT_DIR, "doe_yield_heatmap.png")
plt.savefig(output_filename, dpi=300)
plt.close()

print(f"그래프가 저장되었습니다: {output_filename}")
