import pandas as pd
import matplotlib.pyplot as plt
import os
import matplotlib.dates as mdates

# 설정
OUT_DIR = "out/t2"
os.makedirs(OUT_DIR, exist_ok=True)
plt.rcParams["font.family"] = "Noto Sans CJK KR"
plt.rcParams["axes.unicode_minus"] = False

# 데이터 읽기
file_path = "data/run_log.xlsx"
df = pd.read_excel(file_path, sheet_name="런로그")

# 컬럼명 공백 제거 및 통일
df.columns = df.columns.str.strip()

# 일자 컬럼 변환
if not pd.api.types.is_datetime64_any_dtype(df['일자']):
    try:
        df['일자'] = pd.to_datetime(df['일자'], format='%Y-%m-%d')
    except Exception:
        df['일자'] = pd.to_datetime(df['일자'], errors='coerce')

# 유효한 날짜만 필터링
df_valid = df.dropna(subset=['일자'])

# 외기습도 컬럼 찾기
humidity_col = None
for col in df_valid.columns:
    if '외기습도' in str(col):
        humidity_col = col
        break

if humidity_col is None:
    raise ValueError("외기습도 컬럼을 찾을 수 없습니다.")

# 잔류금속 컬럼 찾기
metal_col = None
for col in df_valid.columns:
    if '잔류금속' in str(col):
        metal_col = col
        break

if metal_col is None:
    raise ValueError("잔류금속 컬럼을 찾을 수 없습니다.")

# 날짜별 평균 계산
daily_stats = df_valid.groupby('일자').agg({
    humidity_col: 'mean',
    metal_col: 'mean'
}).reset_index()

# 플롯 그리기 (Dual Y-axis)
fig, ax1 = plt.subplots(figsize=(12, 6))

color_humidity = '#1f77b4'
ax1.set_xlabel("날짜")
ax1.set_ylabel("외기습도 (%)", color=color_humidity)
line1 = ax1.plot(daily_stats['일자'], daily_stats[humidity_col], 
                 marker='o', linestyle='-', color=color_humidity, label='일평균 외기습도', alpha=0.8)
ax1.tick_params(axis='y', labelcolor=color_humidity)
ax1.grid(True, linestyle='--', alpha=0.3)

# 두 번째 Y축 생성
ax2 = ax1.twinx()
color_metal = '#d62728'
ax2.set_ylabel("잔류금속 (wt%)", color=color_metal)
line2 = ax2.plot(daily_stats['일자'], daily_stats[metal_col], 
                 marker='s', linestyle='--', color=color_metal, label='일평균 잔류금속', alpha=0.8)
ax2.tick_params(axis='y', labelcolor=color_metal)

# 제목
ax1.set_title("날짜별 외기습도 및 잔류금속 평균 변화")

# 범례 통합
lines = line1 + line2
labels = [l.get_label() for l in lines]
ax1.legend(lines, labels, loc='upper left')

# x축 날짜 형식 설정
ax1.xaxis.set_major_formatter(mdates.DateFormatter('%m-%d'))
ax1.xaxis.set_major_locator(mdates.DayLocator(interval=7))
fig.autofmt_xdate()

plt.tight_layout()
save_path = os.path.join(OUT_DIR, "daily_humidity_and_metal_trend.png")
plt.savefig(save_path, dpi=300)
plt.close()
