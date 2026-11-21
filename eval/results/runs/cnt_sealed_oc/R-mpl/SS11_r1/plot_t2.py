import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import os

# 설정
OUT_DIR = "out/t2"
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

# H2/C2H4비별 그룹핑하여 온도별 평균 수율 계산
# 각 H2 비율에 대해 온도가 x축이 되는 선을 그리기 위해 피벗 테이블 생성
pivot_df = df.pivot_table(values='수율(g/g-cat)', index='2존온도(°C)', columns='H2/C2H4비', aggfunc='mean').reset_index()

# 그래프 그리기
fig, ax = plt.subplots(figsize=(10, 6))

# 색상 팔레트 정의
colors = plt.cm.viridis(np.linspace(0, 1, len(pivot_df.columns) - 1))

# 각 H2 비율별로 선 그리기
for i, col in enumerate(pivot_df.columns[1:]):
    h2_ratio = pivot_df[col]
    # 유효한 값만 추출 (NaN 제외)
    valid_mask = ~h2_ratio.isna()
    temps = pivot_df['2존온도(°C)'][valid_mask]
    yields = h2_ratio[valid_mask]
    
    if not temps.empty:
        ax.plot(temps, yields, marker='o', linestyle='-', color=colors[i], label=f'H2/C2H4 = {col}', linewidth=2, markersize=6)

# 라벨 및 제목
ax.set_title('DOE 결과: H2/C2H4 비에 따른 CNT 수율 변화', fontsize=16)
ax.set_xlabel('2존 온도 (°C)', fontsize=12)
ax.set_ylabel('수율 (g/g-cat)', fontsize=12)
ax.legend(loc='best', title='H2/C2H4 비', title_fontsize='10', fontsize='10')
ax.grid(True, linestyle='--', alpha=0.6)

# X축 눈금 확인
x_ticks = sorted(df['2존온도(°C)'].unique())
ax.set_xticks(x_ticks)

plt.tight_layout()

# 저장
output_filename = os.path.join(OUT_DIR, "doe_temp_yield_by_h2.png")
plt.savefig(output_filename, dpi=300)
plt.close()

print(f"그래프가 저장되었습니다: {output_filename}")
