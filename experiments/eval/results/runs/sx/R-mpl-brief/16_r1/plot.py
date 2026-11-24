import pandas as pd
import matplotlib.pyplot as plt
import os

# 데이터 파일 경로 및 출력 디렉토리 설정
DATA_FILE = "/home/chs/Work/tga_plot/tests/inputs/TGA.xlsx"
OUT_DIR = "/home/chs/Work/tga_plot/eval/results/runs/sx/R-mpl-brief/16_r1/out"

# 한글 폰트 설정
plt.rcParams['font.family'] = 'Noto Sans CJK KR'

# 시트 이름 정의
sheet_name = "1006R1-V normal"

# 데이터 읽기 (헤더는 1행, 데이터 시작은 2행으로 가정하지만 pandas가 헤더를 자동으로 처리하도록 header=0 사용)
# 미리보기에 따르면 header_rows: [1] 이므로 첫 번째 행이 헤더임.
df = pd.read_excel(DATA_FILE, sheet_name=sheet_name, header=0)

# 열 이름 확인 및 매핑
# A: Time, B: Temperature, C: Weight(%), D: D.W(%/C)
temp_col = 'Temperature'
weight_col = 'Weight(%)'

# 데이터 정제 (NaN 제거 등 필요시 추가 가능하나, 여기서는 기본 그대로 사용)
df = df.dropna(subset=[temp_col, weight_col])

# 그래프 그리기
fig, ax1 = plt.subplots(figsize=(8, 6))

# y1 축 (무게 %) 그리기 - 요청에 따라 y2(DTG) 없이 무게만 그림
ax1.plot(df[temp_col], df[weight_col], color='#1f4e9c', label='Weight (%)')

# 축 라벨 설정
ax1.set_xlabel('Temperature (°C)', fontsize=12)
ax1.set_ylabel('Weight (%)', color='#1f4e9c', fontsize=12)
ax1.tick_params(axis='y', labelcolor='#1f4e9c')

# 제목 설정 (시트 이름)
ax1.set_title(sheet_name, fontsize=14)

# 범례 표시 (범례 위치: center left)
ax1.legend(loc='center left', bbox_to_anchor=(0.02, 0.5), frameon=False)

# 잔류량(residue) 계산 및 표시: 측정된 점 중 800°C에 가장 가까운 점의 무게
target_temp = 800.0
idx_min = (df[temp_col] - target_temp).abs().idxmin()
residue_weight = df.loc[idx_min, weight_col]
residue_temp = df.loc[idx_min, temp_col]

# 잔류량 마커 및 텍스트
ax1.scatter([residue_temp], [residue_weight], color='#1f4e9c', zorder=5, s=30)
ax1.annotate(f'Residue {residue_weight:.1f}%', 
             xy=(residue_temp, residue_weight), 
             xytext=(10, 10), textcoords='offset points',
             fontsize=10, color='#1f4e9c',
             arrowprops=dict(arrowstyle='->', color='#1f4e9c'))

# 피크 표시는 DTG가 없으므로 생략함 (요청사항: y2축 없이 무게만 그려줘)

# 레이아웃 조정
plt.tight_layout()

# 출력 파일명 생성
output_filename = f"{sheet_name.replace(' ', '_')}_weight_only.png"
output_path = os.path.join(OUT_DIR, output_filename)

# 파일 저장
plt.savefig(output_path, dpi=300, bbox_inches='tight')
plt.close(fig)
