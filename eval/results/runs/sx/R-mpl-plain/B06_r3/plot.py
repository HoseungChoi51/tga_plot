import pandas as pd
import matplotlib.pyplot as plt
import os

# 데이터 파일 경로와 출력 디렉토리 설정
DATA_FILE = "/home/chs/Work/tga_plot/eval/inputs_b/isothermal.txt"
OUT_DIR = "/home/chs/Work/tga_plot/eval/results/runs/sx/R-mpl-plain/B06_r3/out"

# 한국어 폰트 설정
plt.rcParams['font.family'] = 'Noto Sans CJK KR'
plt.rcParams['axes.unicode_minus'] = False

# 데이터 읽기 (isothermal.txt는 탭 또는 공백 구분자일 가능성이 높으므로 sep=None과 engine='python' 사용)
try:
    df = pd.read_csv(DATA_FILE, sep=r'\s+', header=0, encoding='utf-8')
except Exception:
    # 만약 위 방식이 실패하면 일반 csv로 시도하거나 다른 구분자 시도
    try:
        df = pd.read_csv(DATA_FILE, header=0, encoding='utf-8')
    except Exception:
        raise ValueError("파일을 읽을 수 없습니다.")

# 컬럼명 정리 (공백 제거 등)
df.columns = [col.strip() for col in df.columns]

# 필요한 컬럼 확인 및 매핑
cols = df.columns.tolist()
time_col = None
weight_col = None
temp_col = None

for c in cols:
    if 'Time' in c or '시간' in c:
        time_col = c
    elif 'Weight' in c or '무게' in c:
        weight_col = c
    elif 'Temperature' in c or '온도' in c:
        temp_col = c

if not all([time_col, weight_col, temp_col]):
    # 마지막 수단으로 위치 기반 할당
    if len(cols) >= 3:
        time_col, weight_col, temp_col = cols[0], cols[1], cols[2]
    else:
        raise ValueError(f"필요한 컬럼을 찾을 수 없습니다. Available columns: {cols}")

# 그래프 생성
fig, ax1 = plt.subplots(figsize=(10, 6))

# 왼쪽 축: 무게 (%)
color_weight = 'tab:blue'
ax1.set_xlabel('시간 (분)', fontsize=12)
ax1.set_ylabel('무게 (%)', color=color_weight, fontsize=12)
line1 = ax1.plot(df[time_col], df[weight_col], color=color_weight, label='무게 (%)')
ax1.tick_params(axis='y', labelcolor=color_weight)
ax1.grid(True, linestyle='--', alpha=0.5)

# 오른쪽 축: 온도 (°C)
ax2 = ax1.twinx()
color_temp = 'tab:red'
ax2.set_ylabel('온도 (°C)', color=color_temp, fontsize=12)
line2 = ax2.plot(df[time_col], df[temp_col], color=color_temp, linestyle='--', label='온도 (°C)')
ax2.tick_params(axis='y', labelcolor=color_temp)

# 140분일 때의 무게 표시
target_time = 140.0
# 가장 가까운 시간 값 찾기 (정확히 140이 없을 수 있으므로)
idx = (df[time_col] - target_time).abs().idxmin()
weight_at_140 = df.loc[idx, weight_col]
time_at_140 = df.loc[idx, time_col]

# 점과 텍스트로 표시
ax1.scatter([time_at_140], [weight_at_140], color='green', s=100, zorder=5)
ax1.annotate(f'{weight_at_140:.2f}%', 
             xy=(time_at_140, weight_at_140), 
             xytext=(10, 10), 
             textcoords='offset points',
             arrowprops=dict(arrowstyle='->', color='black'),
             fontsize=10,
             bbox=dict(boxstyle='round,pad=0.3', fc='yellow', alpha=0.7))

# 범례 추가
lines = line1 + line2
labels = [l.get_label() for l in lines]
ax1.legend(lines, labels, loc='lower left')

# 제목
plt.title('등온 조건에서의 열중량 분석(TGA) 결과', fontsize=14)

# 레이아웃 조정
plt.tight_layout()

# 출력 디렉토리가 없으면 생성
os.makedirs(OUT_DIR, exist_ok=True)

# 그림 저장
output_path = os.path.join(OUT_DIR, "tga_isothermal.png")
plt.savefig(output_path, dpi=300)
plt.close()
