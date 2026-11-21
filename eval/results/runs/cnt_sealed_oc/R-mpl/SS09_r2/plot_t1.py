import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import os

# 설정
OUT_DIR = "out/t1"
os.makedirs(OUT_DIR, exist_ok=True)
plt.rcParams["font.family"] = "Noto Sans CJK KR"
plt.rcParams["axes.unicode_minus"] = False

# 데이터 로드
file_path = "data/run_log.xlsx"
sheet_name = "런로그"

df = pd.read_excel(file_path, sheet_name=sheet_name)

# 일자 컬럼이 문자열일 수 있으므로 datetime으로 변환
# 에러 원인: 컬럼명 '일자'가 아닌 다른 형태이거나, 데이터 내부에 'yyyy-mm-dd'라는 문자열이 섞여 있을 가능성 제거
# 실제 헤더는 'B 일자 (yyyy-mm-dd)' 였을 가능성이 높으나 미리보기에서는 '일자'로 표시됨. 
# 안전한 처리를 위해 컬럼명을 확인하고 변환합니다.

date_col_name = None
for col in df.columns:
    if '일자' in str(col):
        date_col_name = col
        break

if date_col_name is None:
    raise ValueError("날짜 컬럼('일자')을 찾을 수 없습니다.")

# 날짜 변환 시 errors='coerce'를 사용하여 잘못된 형식(예: 문자열 헤더 잔존 등)은 NaT로 만들고 이후 드롭
df[date_col_name] = pd.to_datetime(df[date_col_name], errors='coerce')

# NaT 행 제거
df = df.dropna(subset=[date_col_name])

# 외기습도 컬럼명이 정확히 일치하는지 확인하고 처리
humidity_col_name = None
for col in df.columns:
    if '외기습도' in str(col):
        humidity_col_name = col
        break

if humidity_col_name is None:
    raise ValueError("외기습도 컬럼을 찾을 수 없습니다.")

# 수치형으로 변환 (문자열이나 특수문자가 섞여 있을 경우 대비)
df[humidity_col_name] = pd.to_numeric(df[humidity_col_name], errors='coerce')
df = df.dropna(subset=[humidity_col_name])

# 날짜별 평균 습도 계산 (하루에 여러 런이 있어 평균을 사용)
daily_humidity = df.groupby(date_col_name)[humidity_col_name].mean().reset_index()

# 정렬 (날짜순)
daily_humidity = daily_humidity.sort_values(by=date_col_name)

# 플롯 생성
fig, ax = plt.subplots(figsize=(12, 6))

ax.plot(daily_humidity[date_col_name], daily_humidity[humidity_col_name], marker='o', linestyle='-', color='#1f77b4', linewidth=1.5, markersize=4)

# 축 레이블 및 제목
ax.set_title('날짜별 평균 외기습도 추이', fontsize=14)
ax.set_xlabel('일자', fontsize=12)
ax.set_ylabel('외기습도 (%)', fontsize=12)

# x축 날짜 형식 간소화 (필요시 회전)
fig.autofmt_xdate(rotation=45)

# 그리드 추가
ax.grid(True, linestyle='--', alpha=0.7)

# 레이아웃 조정
plt.tight_layout()

# 저장
save_path = os.path.join(OUT_DIR, "daily_humidity_trend.png")
plt.savefig(save_path, dpi=300)
plt.close()

print(f"그림이 {save_path}에 저장되었습니다.")
