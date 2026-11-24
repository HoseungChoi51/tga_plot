import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import os

# 설정
plt.rcParams["font.family"] = "Noto Sans CJK KR"
OUT_DIR = "out/t3"
os.makedirs(OUT_DIR, exist_ok=True)

# 파일 경로 및 시트 이름
file_path = "data/tga_batches.xlsx"
sheets = ["R3-260428-1", "R3-260810-2"]

# 색상 정의
colors = ['blue', 'green'] # R3-260428-1: blue, R3-260810-2: green

fig, ax1 = plt.subplots(figsize=(10, 6))
ax2 = ax1.twinx()

all_tg_lines = []
all_dtg_lines = []
tg_labels = []
dtg_labels = []

for i, sheet_name in enumerate(sheets):
    color = colors[i]
    
    # 데이터 읽기
    df = pd.read_excel(file_path, sheet_name=sheet_name)
    
    # 컬럼명 확인 및 매핑
    cols = df.columns.tolist()
    temp_col = [c for c in cols if '온도' in str(c)][0]
    weight_col = [c for c in cols if '중량' in str(c) and '미분' not in str(c)][0]
    dtg_col = [c for c in cols if '미분' in str(c)][0]
    
    x = df[temp_col].values
    y_tg = df[weight_col].values
    y_dtg = df[dtg_col].values
    
    # TG 곡선 (좌측 Y축, 실선)
    line_tg, = ax1.plot(x, y_tg, color=color, linestyle='-', label=f'TG ({sheet_name})')
    all_tg_lines.append(line_tg)
    tg_labels.append(f'TG ({sheet_name})')
    
    # DTG 곡선 (우측 Y축, 점선)
    line_dtg, = ax2.plot(x, y_dtg, color=color, linestyle='--', label=f'DTG ({sheet_name})')
    all_dtg_lines.append(line_dtg)
    dtg_labels.append(f'DTG ({sheet_name})')

# 축 라벨 및 그리드
ax1.set_xlabel('온도 (°C)')
ax1.set_ylabel('중량 (%)', color='black')
ax1.grid(True, linestyle=':', alpha=0.5)

ax2.set_ylabel('미분중량 (%/°C)', color='black')
# ax2의 tick color를 유지하되, 텍스트 색상은 검정으로 통일하거나 각자 지정 가능. 
# 여기서는 단순히 라벨만 추가했습니다.

# 제목
plt.title(f'TG/DTG Curves Comparison: {", ".join(sheets)}')

# 범례 처리
# ax1과 ax2의 handles와 labels를 모두 가져와서 합침
lines_1, labels_1 = ax1.get_legend_handles_labels()
lines_2, labels_2 = ax2.get_legend_handles_labels()
ax1.legend(lines_1 + lines_2, labels_1 + labels_2, loc='center right')

# 주요 지표 표시 (각 배치별 잔류량 및 피크 온도)
# 주석은 복잡해지므로 핵심 수치인 800도 잔류량과 최대 DTG 피크 위주만 간단히 표시하거나 생략할 수 있음.
# 요청에는 "겹쳐 주세요"가 메인이라 지표 텍스트는 생략하거나 최소화함. 기존 대화에서 지표 표기가 있었지만,
# 여러 배치를 겹치면 지저분해질 수 있어 일단 곡선 비교에 집중합니다. 필요하면 추가 로직을 넣을 수 있으나,
# 명확한 요청("색 구분", "실선/점선")에 충실합니다.

plt.tight_layout()

# 저장
output_filename = os.path.join(OUT_DIR, "TGA_R3_Comparison.png")
plt.savefig(output_filename, dpi=300)
print(f"Saved plot to {output_filename}")

plt.close(fig)
