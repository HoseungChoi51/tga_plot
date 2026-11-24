import pandas as pd
import matplotlib.pyplot as plt
import os

# 데이터 파일 경로 및 출력 디렉토리 설정
DATA_FILE = "/home/chs/Work/tga_plot/eval/inputs_b/isothermal.txt"
OUT_DIR = "/home/chs/Work/tga_plot/eval/results/runs/sx/R-mpl-plain/B06_r1/out"

# 한글 폰트 설정
plt.rcParams['font.family'] = 'Noto Sans CJK KR'
plt.rcParams['axes.unicode_minus'] = False

# 데이터 읽기
try:
    df = pd.read_csv(DATA_FILE, sep='\t', header=0)
except Exception:
    try:
        df = pd.read_csv(DATA_FILE, sep=',', header=0)
    except Exception:
        df = pd.read_csv(DATA_FILE, delim_whitespace=True, header=0)

# 컬럼 이름 정리 (공백 제거 등)
df.columns = [col.strip() for col in df.columns]

# 필요한 컬럼 확인 및 추출
time_col = None
weight_col = None
temp_col = None

for col in df.columns:
    if 'Time' in col or '시간' in col:
        time_col = col
    elif 'Weight' in col or '무게' in col:
        weight_col = col
    elif 'Temperature' in col or '온도' in col:
        temp_col = col

if not all([time_col, weight_col, temp_col]):
    # 만약 명시적 매칭이 실패하면 위치 기반 추론 시도 (일반적으로 Time, Temp, Weight 순서일 수 있으나 헤더가 명확하므로 위 코드로 충분할 것으로 예상)
    pass

# 그래프 생성
fig, ax1 = plt.subplots(figsize=(10, 6))

# 왼쪽 축: 무게 (%)
ax1.plot(df[time_col], df[weight_col], color='blue', label='무게 (%)')
ax1.set_xlabel('시간 (분)', fontsize=12)
ax1.set_ylabel('무게 (%)', color='blue', fontsize=12)
ax1.tick_params(axis='y', labelcolor='blue')

# 오른쪽 축: 온도 (°C)
ax2 = ax1.twinx()
ax2.plot(df[time_col], df[temp_col], color='red', linestyle='--', label='온도 (°C)')
ax2.set_ylabel('온도 (°C)', color='red', fontsize=12)
ax2.tick_params(axis='y', labelcolor='red')

# 140분일 때의 무게 표시
target_time = 140.0
# 가장 가까운 데이터 포인트 찾기
idx = df[time_col].sub(target_time).abs().idxmin()
actual_time = df.loc[idx, time_col]
actual_weight = df.loc[idx, weight_col]

# 점과 텍스트로 표시
ax1.scatter(actual_time, actual_weight, color='green', zorder=5)
ax1.annotate(f'{actual_weight:.2f}%', 
             xy=(actual_time, actual_weight), 
             xytext=(actual_time - 20, actual_weight + 5),
             arrowprops=dict(facecolor='black', shrink=0.05, width=1, headwidth=8),
             fontsize=10, color='black')

# 제목 및 범례
plt.title('등온 열중량 분석(TGA) 결과', fontsize=14)
lines_1, labels_1 = ax1.get_legend_handles_labels()
lines_2, labels_2 = ax2.get_legend_handles_labels()
ax1.legend(lines_1 + lines_2, labels_1 + labels_2, loc='center left')

# 레이아웃 조정
plt.tight_layout()

# 출력 디렉토리가 없으면 생성
os.makedirs(OUT_DIR, exist_ok=True)

# 파일 저장
output_path = os.path.join(OUT_DIR, "isothermal_plot.png")
plt.savefig(output_path, dpi=300)
plt.close()
