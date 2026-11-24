import pandas as pd
import matplotlib.pyplot as plt
import os
import numpy as np

# 환경 설정
plt.rcParams["font.family"] = "Noto Sans CJK KR"
plt.rcParams["axes.unicode_minus"] = False
OUT_DIR = "out/t1"
os.makedirs(OUT_DIR, exist_ok=True)

# 데이터 로드
file_path = "data/r2_zone_temps.csv"
df = pd.read_csv(file_path)

# 컬럼명 확인 및 정리 (미리보기 기준: A 시각, B 1존(°C), C 2존(°C), D 3존(°C), E 2존 SP(°C))
# 컬럼명이 정확하지 않을 수 있으므로 위치나 키워드로 탐색하는 것이 안전하지만, 미리보기에 따라 가정합니다.
col_time = '시각'
col_temp_2zone = '2존(°C)'
col_sp_2zone = '2존 SP(°C)'

# 시간 컬럼을 datetime으로 변환
df[col_time] = pd.to_datetime(df[col_time])

# 이탈량 계산: 2존 온도 - 2존 SP
df['이탈량'] = df[col_temp_2zone] - df[col_sp_2zone]

# 절대값 기준으로 가장 큰 편차 시점 찾기
idx_max_deviation = df['이탈량'].abs().idxmax()
max_dev_time = df.loc[idx_max_deviation, col_time]
max_dev_value = df.loc[idx_max_deviation, '이탈량']

# 그래프 그리기
fig, ax = plt.subplots(figsize=(14, 7))

ax.plot(df[col_time], df['이탈량'], color='blue', linewidth=0.8, label='2존 온도 이탈량 (측정값 - SP)')

# 0 라인 표시
ax.axhline(y=0, color='gray', linestyle='--', linewidth=1, label='설정값 (SP) 기준선')

# 최대 편차 지점 마커 및 텍스트 표시
ax.scatter([max_dev_time], [max_dev_value], color='red', zorder=5, s=100, marker='x', label=f'최대 편차: {max_dev_value:+.2f} °C')

# 텍스트로 정보 추가
text_str = f'최대 편차 발생 시점:\n{max_dev_time.strftime("%Y-%m-%d %H:%M")}\n편차 값: {max_dev_value:+.2f} °C'
props = dict(boxstyle='round', facecolor='wheat', alpha=0.5)
ax.text(0.05, 0.95, text_str, transform=ax.transAxes, fontsize=12, verticalalignment='top', bbox=props)

# 축 레이블 및 제목
ax.set_title('R2 반응기 2존 온도 이탈량 추이 (측정값 - 설정값)', fontsize=16)
ax.set_xlabel('시간', fontsize=12)
ax.set_ylabel('이탈량 (°C)', fontsize=12)
ax.legend(loc='best', fontsize=10)
ax.grid(True, linestyle=':', alpha=0.6)

# x축 날짜 형식 개선
fig.autofmt_xdate()

# 저장
save_path = os.path.join(OUT_DIR, "r2_2zone_deviation.png")
plt.savefig(save_path, dpi=300, bbox_inches='tight')
plt.close()

print(f"그래프가 저장되었습니다: {save_path}")
print(f"제일 많이 벗어난 시점: {max_dev_time}")
print(f"이탈량: {max_dev_value:.2f} °C")
