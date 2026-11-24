import pandas as pd
import matplotlib.pyplot as plt
import os

# 설정
DATA_FILE = "/home/chs/Work/tga_plot/tests/inputs/TGA.xlsx"
OUT_DIR = "/home/chs/Work/tga_plot/eval/results/runs/sx/R-mpl-plain/10_r2/out"
os.makedirs(OUT_DIR, exist_ok=True)

# 한글 폰트 설정
plt.rcParams['font.family'] = 'Noto Sans CJK KR'
plt.rcParams['axes.unicode_minus'] = False

# 데이터 읽기
xls = pd.ExcelFile(DATA_FILE)
sheet_names = xls.sheet_names

# 그래프 생성
fig, ax1 = plt.subplots(figsize=(10, 6))

colors = ['#1f77b4', '#ff7f0e', '#2ca02c']
labels = ['Normal', 'Acid', '750C']

residual_data = []

for i, sheet_name in enumerate(sheet_names):
    df = pd.read_excel(DATA_FILE, sheet_name=sheet_name, header=1)
    
    # 열 이름이 숫자(float)인 경우를 대비하여 문자열로 변환 후 strip 적용
    new_columns = []
    for col in df.columns:
        if isinstance(col, float):
            new_columns.append(str(col))
        else:
            new_columns.append(str(col).strip())
    df.columns = new_columns
    
    # 실제 열 이름을 찾기 위해 대소문자 무시하고 검색하거나, 미리보기에 나온 대로 사용
    # 미리보기에 따르면 'Temperature', 'Weight(%)', 'D.W(%/C)' 여야 함
    # 만약 공백이나 특수문자가 섞여 있을 수 있으므로 정규화 시도
    
    def find_col(df, target):
        # 정확히 일치하는 것이 있으면 반환
        if target in df.columns:
            return target
        # 소문자로 비교
        lower_map = {col.lower(): col for col in df.columns}
        if target.lower() in lower_map:
            return lower_map[target.lower()]
        # 부분 일치 검색 (예: 'Temp' 포함)
        for col in df.columns:
            if target.lower().replace(' ', '') in col.lower().replace(' ', ''):
                return col
        raise ValueError(f"Column '{target}' not found in {df.columns.tolist()}")

    temp_col = find_col(df, 'Temperature')
    weight_col = find_col(df, 'Weight(%)')
    dtg_col = find_col(df, 'D.W(%/C)')
    
    x = df[temp_col]
    y_weight = df[weight_col]
    y_dtg = df[dtg_col]
    
    # TGA 곡선 (왼쪽 Y축)
    color = colors[i % len(colors)]
    line_tga, = ax1.plot(x, y_weight, label=f'TGA - {labels[i]}', color=color, linewidth=2)
    
    # DTG 곡선 (오른쪽 Y축)
    ax2 = ax1.twinx()
    line_dtg, = ax2.plot(x, y_dtg, linestyle='--', alpha=0.6, color=color)
    
    # 700도에서의 잔류량 계산
    # 700도에 가장 가까운 데이터 포인트 찾기
    idx_700 = (df[temp_col] - 700).abs().idxmin()
    residual_700 = df.loc[idx_700, weight_col]
    residual_data.append((labels[i], residual_700))

# 축 레이블 및 제목
ax1.set_xlabel('Temperature (°C)', fontsize=12)
ax1.set_ylabel('Weight (%)', fontsize=12)
ax2.set_ylabel('Derivative Weight (%/°C)', fontsize=12)
plt.title('TGA and DTG Curves with Residual Mass at 700°C', fontsize=14)

# 범례 추가
handles, labels_orig = ax1.get_legend_handles_labels()
ax1.legend(handles, labels_orig, loc='upper right')

# 잔류량 텍스트 박스 추가
text_str = "Residual Mass at 700°C:\n"
for label, val in residual_data:
    text_str += f"{label}: {val:.2f}%\n"

props = dict(boxstyle='round', facecolor='wheat', alpha=0.5)
ax1.text(0.05, 0.95, text_str, transform=ax1.transAxes, fontsize=10,
         verticalalignment='top', bbox=props)

plt.tight_layout()
output_path = os.path.join(OUT_DIR, "tga_residual_700.png")
plt.savefig(output_path, dpi=300)
plt.close()
