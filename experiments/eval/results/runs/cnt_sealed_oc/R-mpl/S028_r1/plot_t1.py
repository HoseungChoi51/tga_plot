import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import os

# 설정
OUT_DIR = "out/t1"
os.makedirs(OUT_DIR, exist_ok=True)
plt.rcParams["font.family"] = "Noto Sans CJK KR"

# 데이터 로드
file_path = "data/run_log.xlsx"
df = pd.read_excel(file_path, sheet_name="런로그")

# 컬럼명 확인 및 정규화 (KeyError 방지)
col_target = None
for col in df.columns:
    if '산화개시온도' in str(col):
        col_target = col
        break

if col_target is None:
    raise ValueError("데이터에서 '산화개시온도' 관련 컬럼을 찾을 수 없습니다.")

# 반응기 컬럼명 확인
reactor_col = None
for col in df.columns:
    if '반응기' in str(col):
        reactor_col = col
        break

if reactor_col is None:
    # 기본값으로 시도하거나 오류 처리 가능하지만, 미리보기상 '반응기'가 있음
    reactor_col = '반응기'

# 데이터 준비
# R4 그룹과 나머지(R1-R3) 그룹으로 분리
mask_r4 = df[reactor_col] == 'R4'
df_r4 = df[mask_r4]
df_others = df[~mask_r4]

# 산화개시온도 추출
# 중요: 히스토그램을 그리려면 값이 숫자(float/int)여야 합니다.
# Excel에서 텍스트로 저장되었거나 빈 문자열이 섞여 있을 수 있으므로 pd.to_numeric으로 강제 변환합니다.
temp_r4 = pd.to_numeric(df_r4[col_target], errors='coerce').dropna()
temp_others = pd.to_numeric(df_others[col_target], errors='coerce').dropna()

# 만약 모든 데이터가 NaN이면 에러 방지용 체크 (선택사항, 정상적인 데이터라면 통과)
if len(temp_r4) == 0 and len(temp_others) == 0:
    raise ValueError("변환된 산화개시온도 데이터가 비어 있습니다.")

# 히스토그램 그리기
bins = np.arange(535, 611, 5) # 535부터 610까지 5 간격

fig, ax = plt.subplots(figsize=(10, 6))

ax.hist(temp_others, bins=bins, alpha=0.6, label='R1-R3', color='steelblue', edgecolor='black')
ax.hist(temp_r4, bins=bins, alpha=0.6, label='R4', color='darkorange', edgecolor='black')

# 축 라벨 및 제목
ax.set_xlabel('산화개시온도 (°C)', fontsize=12)
ax.set_ylabel('빈도 (Count)', fontsize=12)
ax.set_title('반응기별 산화개시온도 분포 비교', fontsize=14)

# 범례
ax.legend(loc='upper right', fontsize=11)

# 격자선 추가
ax.grid(True, linestyle='--', alpha=0.7)

# 범위 설정
ax.set_xlim(535, 610)

# 저장
output_file = os.path.join(OUT_DIR, "oxidation_onset_temp_histogram.png")
plt.tight_layout()
plt.savefig(output_file, dpi=300)
plt.close()
