import pandas as pd
import matplotlib.pyplot as plt
import os

# 데이터 파일 경로와 출력 디렉토리 설정
DATA_FILE = "/home/chs/Work/tga_plot/eval/inputs_b/rheology.csv"
OUT_DIR = "/home/chs/Work/tga_plot/eval/results/runs/sx/R-mpl-plain/B03_r1/out"

# 한글 폰트 설정
plt.rcParams['font.family'] = 'Noto Sans CJK KR'
plt.rcParams['axes.unicode_minus'] = False

# 데이터 읽기
df = pd.read_csv(DATA_FILE)

# 컬럼 이름 확인 및 변수 할당
# 예상 컬럼: "Angular frequency (rad/s)", "Storage modulus G' (Pa)", "Loss modulus G'' (Pa)"
freq_col = df.columns[0]
g_prime_col = df.columns[1]
g_double_prime_col = df.columns[2]

omega = df[freq_col]
G_prime = df[g_prime_col]
G_double_prime = df[g_double_prime_col]

# 그래프 그리기
fig, ax1 = plt.subplots(figsize=(8, 6))

# 왼쪽 축: G'
color1 = 'tab:blue'
ax1.set_xlabel('각진 주파수 (rad/s)', fontsize=12)
ax1.set_ylabel("저장 탄성률 G' (Pa)", color=color1, fontsize=12)
line1 = ax1.plot(omega, G_prime, color=color1, label="G'", linewidth=2)
ax1.tick_params(axis='y', labelcolor=color1)
ax1.set_xscale('log')
ax1.set_yscale('log')

# 오른쪽 축: G''
ax2 = ax1.twinx()
color2 = 'tab:red'
ax2.set_ylabel("손실 탄성률 G'' (Pa)", color=color2, fontsize=12)
line2 = ax2.plot(omega, G_double_prime, color=color2, label="G''", linestyle='--', linewidth=2)
ax2.tick_params(axis='y', labelcolor=color2)
ax2.set_yscale('log')

# 제목 및 범례
fig.suptitle('주파수에 따른 저장 탄성률과 손실 탄성률', fontsize=14)
lines = line1 + line2
labels = [l.get_label() for l in lines]
ax1.legend(lines, labels, loc='best')

# 그리드 표시
ax1.grid(True, which="both", ls="-", alpha=0.5)

# 레이아웃 조정
plt.tight_layout(rect=[0, 0, 1, 0.96])

# 출력 디렉토리가 없으면 생성
os.makedirs(OUT_DIR, exist_ok=True)

# 파일 저장
output_path = os.path.join(OUT_DIR, "rheology_plot.png")
plt.savefig(output_path, dpi=300)

print(f"그래프가 {output_path}에 저장되었습니다.")
