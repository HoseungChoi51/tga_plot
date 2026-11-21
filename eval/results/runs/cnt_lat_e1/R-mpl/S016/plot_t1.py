import pandas as pd
import matplotlib.pyplot as plt
import os

# 설정
plt.rcParams["font.family"] = "Noto Sans CJK KR"
OUT_DIR = "out/t1"
os.makedirs(OUT_DIR, exist_ok=True)

file_path = "data/tga_batches.xlsx"
sheets_to_plot = ['R4-260407-1', 'R4-260721-1']

fig, ax = plt.subplots(figsize=(10, 6))

colors = ['#1f77b4', '#ff7f0e'] # 파랑, 주황

for i, sheet_name in enumerate(sheets_to_plot):
    df = pd.read_excel(file_path, sheet_name=sheet_name)
    
    # 컬럼명 확인 및 데이터 추출 (미리보기 기준: B 온도, C 중량)
    temp_col = '온도 (°C)'
    weight_col = '중량 (%)'
    
    if temp_col not in df.columns or weight_col not in df.columns:
        raise ValueError(f"Columns {temp_col} or {weight_col} not found in sheet {sheet_name}")
        
    x = df[temp_col]
    y = df[weight_col]
    
    ax.plot(x, y, label=sheet_name, color=colors[i], linewidth=1.5)

# 축 범위 고정
ax.set_xlim(30, 900)
ax.set_ylim(0, 105)

# 라벨 및 제목
ax.set_xlabel('온도 (°C)', fontsize=12)
ax.set_ylabel('중량 (%)', fontsize=12)
ax.set_title('TGA 곡선 비교: R4-260407-1 vs R4-260721-1', fontsize=14)

# 격자 및 범례
ax.grid(True, linestyle='--', alpha=0.6)
ax.legend(loc='upper right', title='배치')

# 저장
output_filename = os.path.join(OUT_DIR, "tga_overlay_R4.png")
plt.tight_layout()
plt.savefig(output_filename, dpi=300)
plt.close()
