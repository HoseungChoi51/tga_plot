import pandas as pd
import matplotlib.pyplot as plt
import os
import matplotlib.dates as mdates

# 설정
plt.rcParams["font.family"] = "Noto Sans CJK KR"
OUT_DIR = "out/t2"
os.makedirs(OUT_DIR, exist_ok=True)

# 데이터 읽기
file_path = "data/run_log.xlsx"
df = pd.read_excel(file_path, sheet_name="런로그")

# 열 이름 공백 제거 및 정리
df.columns = df.columns.str.strip()

# 일자 컬럼 변환
if '일자' in df.columns:
    # 미리보기에서 'yyyy-mm-dd' 포맷으로 명시되었으므로 format 지정 후 errors='coerce' 사용
    df['일자'] = pd.to_datetime(df['일자'], format='%Y-%m-%d', errors='coerce')
    df = df.dropna(subset=['일자'])
else:
    raise ValueError("Date column not found.")

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

# 날짜별 평균 외기습도와 평균 잔류금속 계산
daily_stats = df.groupby('일자').agg({
    humidity_col: 'mean',
    metal_col: 'mean'
}).reset_index()

# 플롯팅
fig, ax1 = plt.subplots(figsize=(12, 6))

# 왼쪽 축: 외기습도 (%)
color1 = 'tab:blue'
ax1.set_xlabel('일자')
ax1.set_ylabel('외기습도 (%)', color=color1)
line1 = ax1.plot(daily_stats['일자'], daily_stats[humidity_col], marker='o', linestyle='-', color=color1, label='일간 평균 외기습도')
ax1.tick_params(axis='y', labelcolor=color1)
ax1.grid(True, linestyle='--', alpha=0.7)

# 오른쪽 축: 잔류금속 (wt%)
ax2 = ax1.twinx()
color2 = 'tab:red'
ax2.set_ylabel('잔류금속 (wt%)', color=color2)
line2 = ax2.plot(daily_stats['일자'], daily_stats[metal_col], marker='s', linestyle='--', color=color2, label='일간 평균 잔류금속')
ax2.tick_params(axis='y', labelcolor=color2)

# 제목 설정
plt.title('날짜별 외기습도 및 잔류금속 변화 추이')

# 범례 합치기
lines = line1 + line2
labels = [l.get_label() for l in lines]
ax1.legend(lines, labels, loc='upper left')

# x축 날짜 형식 간소화
ax1.xaxis.set_major_formatter(mdates.DateFormatter('%y-%m-%d'))
fig.autofmt_xdate(rotation=45)

# 저장
output_file = os.path.join(OUT_DIR, "humidity_metal_by_date.png")
plt.tight_layout()
plt.savefig(output_file, dpi=300)
plt.close()
