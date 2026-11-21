import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import os

# 설정
OUT_DIR = "out/t2"
os.makedirs(OUT_DIR, exist_ok=True)
plt.rcParams["font.family"] = "Noto Sans CJK KR"
plt.rcParams["axes.unicode_minus"] = False

# 데이터 로드
file_path = "data/run_log.xlsx"
sheet_name = "런로그"

df = pd.read_excel(file_path, sheet_name=sheet_name)

# 컬럼명 매칭 (유연하게 처리)
date_col_name = None
humidity_col_name = None
metal_col_name = None

for col in df.columns:
    col_str = str(col)
    if '일자' in col_str:
        date_col_name = col
    elif '외기습도' in col_str:
        humidity_col_name = col
    elif '잔류금속' in col_str:
        metal_col_name = col

if date_col_name is None or humidity_col_name is None or metal_col_name is None:
    raise ValueError("필요한 컬럼(일자, 외기습도, 잔류금속)을 찾을 수 없습니다.")

# 날짜 변환
df[date_col_name] = pd.to_datetime(df[date_col_name], errors='coerce')
df = df.dropna(subset=[date_col_name])

# 수치형 변환 및 결측치 제거
df[humidity_col_name] = pd.to_numeric(df[humidity_col_name], errors='coerce')
df[metal_col_name] = pd.to_numeric(df[metal_col_name], errors='coerce')
df = df.dropna(subset=[humidity_col_name, metal_col_name])

# 날짜별 평균 계산
daily_avg = df.groupby(date_col_name).agg({
    humidity_col_name: 'mean',
    metal_col_name: 'mean'
}).reset_index()

daily_avg = daily_avg.sort_values(by=date_col_name)

# 플롯 생성 (이중 Y축 사용)
fig, ax1 = plt.subplots(figsize=(12, 6))

color_hum = '#1f77b4' # 습도 색상 (파랑)
color_met = '#d62728' # 금속 색상 (빨강)

# 좌측 Y축: 외기습도
ax1.set_xlabel('일자', fontsize=12)
ax1.set_ylabel('외기습도 (%)', color=color_hum, fontsize=12)
line1 = ax1.plot(daily_avg[date_col_name], daily_avg[humidity_col_name], 
                 marker='o', linestyle='-', color=color_hum, linewidth=1.5, markersize=4, label='평균 외기습도')
ax1.tick_params(axis='y', labelcolor=color_hum)
ax1.grid(True, linestyle='--', alpha=0.3)

# 우측 Y축: 잔류금속
ax2 = ax1.twinx()
ax2.set_ylabel('잔류금속 (wt%)', color=color_met, fontsize=12)
line2 = ax2.plot(daily_avg[date_col_name], daily_avg[metal_col_name], 
                 marker='s', linestyle='--', color=color_met, linewidth=1.5, markersize=4, label='평균 잔류금속')
ax2.tick_params(axis='y', labelcolor=color_met)

# 제목 및 범례
fig.suptitle('날짜별 평균 외기습도 및 잔류금속 추이', fontsize=14)
lines = line1 + line2
labels = [l.get_label() for l in lines]
ax1.legend(lines, labels, loc='upper left')

# x축 날짜 형식 간소화
fig.autofmt_xdate(rotation=45)

# 레이아웃 조정
plt.tight_layout(rect=[0, 0, 1, 0.96])

# 저장
save_path = os.path.join(OUT_DIR, "daily_humidity_metal_trend.png")
plt.savefig(save_path, dpi=300)
plt.close()

print(f"그림이 {save_path}에 저장되었습니다.")
