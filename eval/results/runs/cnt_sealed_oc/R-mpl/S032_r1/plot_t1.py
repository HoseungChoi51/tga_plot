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
file_path = "data/r2_zone_temps.csv"
df = pd.read_csv(file_path, encoding='utf-8-sig') # utf-8-sig for potential BOM

# 시각 컬럼이 datetime 형식으로 파싱되도록 변환
# 데이터 미리보기에 'A 시각'이라고 되어 있으므로 해당 컬럼명 사용
time_col = df.columns[0] 
zone2_col = [col for col in df.columns if '2존(°C)' in col][0]
sp_col = [col for col in df.columns if '2존 SP' in col][0]

df[time_col] = pd.to_datetime(df[time_col])

# 계산: 2존 온도 - SP (편차)
df['deviation'] = df[zone2_col] - df[sp_col]

# 가장 크게 벗어난 시점 찾기 (절댓값 기준)
max_abs_idx = df['deviation'].abs().idxmax()
max_time = df.loc[max_abs_idx, time_col]
max_dev = df.loc[max_abs_idx, 'deviation']

print(f"가장 많이 벗어난 시점: {max_time}")
print(f"해당 시점의 편차: {max_dev:.2f} °C")

# 그래프 그리기
fig, ax = plt.subplots(figsize=(14, 7))

ax.plot(df[time_col], df['deviation'], color='blue', linewidth=1, label='2존 온도 편차 (실제 - SP)')

# 최대 편차 시점 강조
ax.scatter([max_time], [max_dev], color='red', zorder=5, s=100, label=f'최대 편차 시점 ({max_time.strftime("%Y-%m-%d %H:%M")}, {max_dev:.2f}°C)')

# 참조선 (0 편차)
ax.axhline(y=0, color='black', linestyle='--', linewidth=0.8, alpha=0.5)

ax.set_xlabel('시간')
ax.set_ylabel('온도 편차 (°C)')
ax.set_title('R2 반응기 2존 온도의 설정값(SP) 대비 시간별 편차')
ax.legend(loc='best')
ax.grid(True, linestyle=':', alpha=0.6)

# X축 날짜 형식 최적화
fig.autofmt_xdate(rotation=30, ha="right")

plt.tight_layout()
output_filename = os.path.join(OUT_DIR, "r2_zone2_deviation.png")
plt.savefig(output_filename, dpi=300)
plt.close()

print(f"그래프 저장 완료: {output_filename}")
