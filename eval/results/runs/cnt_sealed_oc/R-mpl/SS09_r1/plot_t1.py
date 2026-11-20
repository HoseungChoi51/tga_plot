import pandas as pd
import matplotlib.pyplot as plt
import os
import matplotlib.dates as mdates

# 설정
plt.rcParams["font.family"] = "Noto Sans CJK KR"
OUT_DIR = "out/t1"
os.makedirs(OUT_DIR, exist_ok=True)

# 데이터 읽기
file_path = "data/run_log.xlsx"
df = pd.read_excel(file_path, sheet_name="런로그")

# 열 이름 공백 제거 (미리보기에는 공백이 있지만 실제 파일에서는 다를 수 있음)
df.columns = df.columns.str.strip()

# 데이터 전처리: 일자 컬럼 변환
# 미리보기에서 '일자 (yyyy-mm-dd)'로 되어 있어 실제 값이 문자열일 수 있으므로 errors='coerce' 사용 후 제거
if '일자' in df.columns:
    df['일자'] = pd.to_datetime(df['일자'], format='%Y-%m-%d', errors='coerce')
    df = df.dropna(subset=['일자'])
else:
    # 만약 열 이름이 다르다면 첫 번째 컬럼을 날짜로 가정하거나 에러 처리
    raise ValueError("Date column not found. Please check the column names.")

# 외기습도 컬럼 찾기 (공백 variations 고려)
humidity_col = None
for col in df.columns:
    if '외기습도' in col:
        humidity_col = col
        break

if humidity_col is None:
    raise ValueError("Humidity column not found.")

# 날짜별 평균 외기습도 계산
daily_humidity = df.groupby('일자')[humidity_col].mean().reset_index()

# 플롯팅
fig, ax = plt.subplots(figsize=(12, 6))

ax.plot(daily_humidity['일자'], daily_humidity[humidity_col], marker='o', linestyle='-', color='b', label='일간 평균 외기습도')

# 축 설정
ax.set_xlabel('일자')
ax.set_ylabel(humidity_col)
ax.set_title('날짜별 외기습도 변화 추이')
ax.grid(True, linestyle='--', alpha=0.7)
ax.legend()

# x축 날짜 형식 간소화
ax.xaxis.set_major_formatter(mdates.DateFormatter('%y-%m-%d'))
fig.autofmt_xdate(rotation=45)

# 저장
output_file = os.path.join(OUT_DIR, "humidity_by_date.png")
plt.tight_layout()
plt.savefig(output_file, dpi=300)
plt.close()
