import pandas as pd
import matplotlib.pyplot as plt
import os

# 설정
plt.rcParams["font.family"] = "Noto Sans CJK KR"
OUT_DIR = "out/t1"
os.makedirs(OUT_DIR, exist_ok=True)

# 데이터 읽기 (CSV는 sheet_name 인자를 지원하지 않음)
file_path = "data/raman/R2-260617-1.csv"
df = pd.read_csv(file_path)

# 컬럼명 확인 및 정리 (공백 제거 등)
df.columns = df.columns.str.strip()

# Raman Shift와 Intensity 컬럼 추출
# 실제 CSV 헤더가 'A Raman Shift (cm-1)'가 아닐 수 있으므로, 첫 번째와 두 번째 컬럼을 사용하거나 부분 일치로 찾음
shift_col = None
intensity_col = None

for col in df.columns:
    if 'Raman Shift' in col or 'Shift' in col:
        shift_col = col
    elif 'Intensity' in col:
        intensity_col = col

# 만약 명시적으로 못 찾으면 위치 기반 (첫번째, 두번째)
if shift_col is None:
    shift_col = df.columns[0]
if intensity_col is None:
    intensity_col = df.columns[1]

# 데이터 정렬 (Raman Shift 기준 오름차순)
df_sorted = df.sort_values(by=shift_col).reset_index(drop=True)

# 플롯 생성
fig, ax = plt.subplots(figsize=(3.5, 2.5))

# 스펙트럼 그리기
ax.plot(df_sorted[shift_col], df_sorted[intensity_col], color='black', linewidth=1.0)

# 밴드 위치 정의
bands = {
    'D': 1350,
    'G': 1580,
    '2D': 2690
}

# 세로 점선과 라벨 추가
for name, pos in bands.items():
    # 세로 점선
    ax.axvline(x=pos, color='red', linestyle='--', linewidth=0.8, alpha=0.7)
    
    # 라벨 위치 계산: 해당 파장 근처의 최대 강도 위에 표시하거나, 고정된 높이 사용
    # 여기서는 y축 상단에 가깝게 배치하기 위해 현재 축 범위를 기준으로 함
    y_min, y_max = ax.get_ylim()
    label_y = y_max * 0.95
    
    ax.text(pos, label_y, name, ha='center', va='top', fontsize=8, color='red')

# 축 레이블 및 제목
ax.set_xlabel('Raman Shift (cm$^{-1}$)', fontsize=9)
ax.set_ylabel('Intensity (a.u.)', fontsize=9)
ax.set_xlim(1000, 3000)
ax.tick_params(axis='both', which='major', labelsize=8)

# 레이아웃 조정
plt.tight_layout()

# 저장
output_filename = os.path.join(OUT_DIR, "R2-260617-1_raman_spectrum.tiff")
plt.savefig(output_filename, dpi=600, format='tiff')
plt.close(fig)
