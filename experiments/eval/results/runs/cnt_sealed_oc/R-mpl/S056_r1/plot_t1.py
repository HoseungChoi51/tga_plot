import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import os

# 설정
OUT_DIR = "out/t1"
os.makedirs(OUT_DIR, exist_ok=True)

plt.rcParams["font.family"] = "Noto Sans CJK KR"
plt.rcParams["axes.unicode_minus"] = False

# 데이터 읽기
file_path = "data/downtime.xlsx"
df = pd.read_excel(file_path, sheet_name="정지이력")

# 정지시간(분) 추출 및 결측치/비수치 제거
downtime_minutes = pd.to_numeric(df['정지시간(분)'], errors='coerce').dropna()

# 히스토그램 그리기
fig, ax = plt.subplots(figsize=(10, 6))

# 로그 스케일 빈 경계 정의
bins = [5, 10, 20, 50, 100, 200, 500, 1000]

# x축을 로그 스케일로 하기 위해 log-transformed 데이터 사용 또는 set_xscale 사용
# matplotlib의 hist는 bins가 직접 적용되므로, set_xscale('log')를 사용하는 것이 더 명확함
ax.hist(downtime_minutes, bins=bins, edgecolor='black', color='steelblue', alpha=0.7)

ax.set_xscale('log')
ax.set_xlabel('정지시간 (분)', fontsize=12)
ax.set_ylabel('빈도 (Count)', fontsize=12)
ax.set_title('CNT 생산 공정 정지시간 분포 (로그 스케일)', fontsize=14)

# 그리드 추가 (x축은 로그 스케일이므로 minor grid 포함 시 가독성 향상 가능하나 기본 major만 켜짐)
ax.grid(True, which='major', linestyle='--', alpha=0.5)
ax.grid(True, which='minor', axis='x', linestyle=':', alpha=0.3) # 로그 스케일의 마이너스 그리드 추가로 세밀한 눈금 확인 용이

# save figure
save_path = os.path.join(OUT_DIR, "downtime_histogram_log.png")
plt.savefig(save_path, dpi=300, bbox_inches='tight')
plt.close(fig)
