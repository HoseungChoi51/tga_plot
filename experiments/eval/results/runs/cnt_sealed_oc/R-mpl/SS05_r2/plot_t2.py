import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import os

# 설정
plt.rcParams["font.family"] = "Noto Sans CJK KR"
OUT_DIR = "out/t2"
os.makedirs(OUT_DIR, exist_ok=True)

# 파일 경로 및 시트 이름
file_path = "data/tga_batches.xlsx"
sheet_name = "R3-260428-1"

# 데이터 읽기
df = pd.read_excel(file_path, sheet_name=sheet_name)

# 컬럼명 확인 및 매핑 (미리보기 기준: A 시간, B 온도, C 중량, D 미분중량)
cols = df.columns.tolist()
time_col = [c for c in cols if '시간' in str(c)]
temp_col = [c for c in cols if '온도' in str(c)]
weight_col = [c for c in cols if '중량' in str(c) and '미분' not in str(c)]
dtg_col = [c for c in cols if '미분' in str(c)]

if not time_col or not temp_col or not weight_col or not dtg_col:
    raise ValueError("필요한 컬럼을 찾을 수 없습니다.")

time_col = time_col[0]
temp_col = temp_col[0]
weight_col = weight_col[0]
dtg_col = dtg_col[0]

x = df[temp_col].values
y_tg = df[weight_col].values
y_dtg = df[dtg_col].values

# 플롯 생성
fig, ax1 = plt.subplots(figsize=(10, 6))

# TG 곡선 (좌측 Y축)
ax1.plot(x, y_tg, color='blue', label='TG (중량 %)')
ax1.set_xlabel('온도 (°C)')
ax1.set_ylabel('중량 (%)', color='blue')
ax1.tick_params(axis='y', labelcolor='blue')
ax1.grid(True, linestyle='--', alpha=0.5)

# DTG 곡선 (우측 Y축)
ax2 = ax1.twinx()
ax2.plot(x, y_dtg, color='red', label='DTG (미분중량 %/°C)')
ax2.set_ylabel('미분중량 (%/°C)', color='red')
ax2.tick_params(axis='y', labelcolor='red')

# 제목 및 범례
plt.title(f'TG/DTG Curves for {sheet_name}')

# 두 축의 레이블을 하나로 묶어서 표시하기 위해 범례 처리
lines_1, labels_1 = ax1.get_legend_handles_labels()
lines_2, labels_2 = ax2.get_legend_handles_labels()
ax1.legend(lines_1 + lines_2, labels_1 + labels_2, loc='center right')

# 잔류량 (800°C에서의 무게) 계산 및 표시
idx_800 = np.argmin(np.abs(x - 800))
residual_weight = y_tg[idx_800]
temp_at_residual = x[idx_800]

ax1.text(temp_at_residual, residual_weight, f'잔류량 @ 800°C\n{residual_weight:.2f}%', 
         fontsize=10, verticalalignment='bottom', horizontalalignment='right',
         bbox=dict(boxstyle="round,pad=0.3", fc="yellow", ec="black", lw=1))

# 피크 (DTG 최대값) 계산 및 표시
max_dtg_idx = np.argmax(y_dtg)
peak_temp = x[max_dtg_idx]
peak_val = y_dtg[max_dtg_idx]

ax2.text(peak_temp, peak_val, f'DTG Peak\n{peak_temp:.1f}°C, {peak_val:.2f}%/°C', 
         fontsize=10, verticalalignment='top', horizontalalignment='left',
         bbox=dict(boxstyle="round,pad=0.3", fc="cyan", ec="black", lw=1))

plt.tight_layout()

# 저장
output_filename = os.path.join(OUT_DIR, f"TGA_{sheet_name}.png")
plt.savefig(output_filename, dpi=300)
print(f"Saved plot to {output_filename}")

plt.close(fig)
