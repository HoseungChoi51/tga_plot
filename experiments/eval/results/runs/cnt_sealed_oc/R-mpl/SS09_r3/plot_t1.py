import pandas as pd
import matplotlib.pyplot as plt
import os
import matplotlib.dates as mdates

# 설정
OUT_DIR = "out/t1"
os.makedirs(OUT_DIR, exist_ok=True)
plt.rcParams["font.family"] = "Noto Sans CJK KR"
plt.rcParams["axes.unicode_minus"] = False

# 데이터 읽기
file_path = "data/run_log.xlsx"
df = pd.read_excel(file_path, sheet_name="런로그")

# 컬럼명 공백 제거 및 통일 (미리보기에서 '외기습도 (%)'로 보이지만 실제 파일에서는 공백 위치가 다를 수 있음)
df.columns = df.columns.str.strip()

# 일자 컬럼 변환
if not pd.api.types.is_datetime64_any_dtype(df['일자']):
    # 문자열일 경우 yyyy-mm-dd 형식으로 강제 파싱 시도
    try:
        df['일자'] = pd.to_datetime(df['일자'], format='%Y-%m-%d')
    except Exception:
        # 실패 시 기본 파싱
        df['일자'] = pd.to_datetime(df['일자'], errors='coerce')

# 유효한 날짜만 필터링
df_valid = df.dropna(subset=['일자'])

# 외기습도 컬럼 찾기 (정확한 이름이 아니면 유사한 이름을 탐색)
humidity_col = None
for col in df_valid.columns:
    if '외기습도' in str(col):
        humidity_col = col
        break

if humidity_col is None:
    raise ValueError("외기습도 컬럼을 찾을 수 없습니다.")

# 날짜별 평균 외기습도 계산
daily_humidity = df_valid.groupby('일자')[humidity_col].mean().reset_index()

# 플롯 그리기
fig, ax = plt.subplots(figsize=(12, 6))

ax.plot(daily_humidity['일자'], daily_humidity[humidity_col], 
        marker='o', linestyle='-', color='#1f77b4', label='일평균 외기습도')

# 축 레이블 및 제목
ax.set_xlabel("날짜")
ax.set_ylabel("외기습도 (%)")
ax.set_title("날짜별 평균 외기습도 변화")
ax.legend()
ax.grid(True, linestyle='--', alpha=0.7)

# x축 날짜 형식 설정
ax.xaxis.set_major_formatter(mdates.DateFormatter('%m-%d'))
ax.xaxis.set_major_locator(mdates.DayLocator(interval=7))
fig.autofmt_xdate()

plt.tight_layout()
save_path = os.path.join(OUT_DIR, "daily_humidity_trend.png")
plt.savefig(save_path, dpi=300)
plt.close()
