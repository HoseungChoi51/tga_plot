import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import os

# 설정
OUT_DIR = "out/t1"
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

# 데이터 전처리 및 통계 계산
# 온도별 수율 평균과 표준편차 계산
stats_df = df.groupby('2존온도(°C)').agg({
    '수율(g/g-cat)': ['mean', 'std', 'count']
}).reset_index()

stats_df.columns = ['Temperature', 'Mean_Yield', 'Std_Yield', 'Count']

# 그래프 그리기
fig, ax = plt.subplots(figsize=(10, 6))

# 에러바 포함 선그래프
ax.errorbar(stats_df['Temperature'], stats_df['Mean_Yield'], 
            yerr=stats_df['Std_Yield'], 
            fmt='-o', color='#1f77b4', ecolor='lightgray', elinewidth=3, capsize=5, markersize=8, label='평균 ± 표준편차')

# 원본 데이터 점 표시 (투명하게)
ax.scatter(df['2존온도(°C)'], df['수율(g/g-cat)'], alpha=0.3, color='gray', s=20, label='원본 데이터 포인트')

# 라벨 및 제목
ax.set_title('DOE 결과: 2존 온도에 따른 CNT 수율 변화', fontsize=16)
ax.set_xlabel('2존 온도 (°C)', fontsize=12)
ax.set_ylabel('수율 (g/g-cat)', fontsize=12)
ax.legend(loc='best', fontsize=10)
ax.grid(True, linestyle='--', alpha=0.6)

# Y축 범위 약간 여유롭게
y_min = df['수율(g/g-cat)'].min()
y_max = df['수율(g/g-cat)'].max()
margin = (y_max - y_min) * 0.1
ax.set_ylim(y_min - margin, y_max + margin)

# X축 눈금 확인
x_ticks = sorted(df['2존온도(°C)'].unique())
ax.set_xticks(x_ticks)

plt.tight_layout()

# 저장
output_filename = os.path.join(OUT_DIR, "doe_temp_yield_plot.png")
plt.savefig(output_filename, dpi=300)
plt.close()

print(f"그래프가 저장되었습니다: {output_filename}")
