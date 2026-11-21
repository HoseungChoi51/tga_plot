import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import os
import glob

# 설정
plt.rcParams["font.family"] = "Noto Sans CJK KR"
OUT_DIR = "out/t3"
os.makedirs(OUT_DIR, exist_ok=True)

# 데이터 파일 경로 패턴
data_dir = "data/raman"
pattern = os.path.join(data_dir, "*.csv")
files = glob.glob(pattern)

if not files:
    raise FileNotFoundError(f"No CSV files found in {data_dir}")

fig, ax = plt.subplots(figsize=(12, 8))

# 색상 정의
colors_red = ['#d62728', '#ff9999'] # 빨간 계열 두 가지
color_gray = '#a0a0a0'              # 회색

red_file_count = 0

# 각 파일을 읽어 그래프에 추가
for filepath in sorted(files):
    # 파일명에서 라벨 생성 (예: R1-260326-1.csv -> R1-260326-1)
    filename = os.path.basename(filepath)
    label = filename.replace('.csv', '')
    
    try:
        df = pd.read_csv(filepath)
        
        cols = df.columns.tolist()
        if len(cols) < 2:
            continue
            
        x_col = cols[0]
        y_col = cols[1]
        
        # 데이터 정렬 (x축 오름차순)
        sort_idx = df[x_col].argsort()
        x_data = df.iloc[sort_idx][x_col].values
        y_data = df.iloc[sort_idx][y_col].values
        
        # G 밴드 정규화: 1550-1620 cm-1 구간에서의 최대값으로 나누어 최대값이 1이 되도록 함
        g_band_mask = (x_data >= 1550) & (x_data <= 1620)
        if np.any(g_band_mask):
            max_intensity_g = np.max(y_data[g_band_mask])
            if max_intensity_g > 0:
                y_data_norm = y_data / max_intensity_g
            else:
                y_data_norm = y_data
        else:
            y_data_norm = y_data
            
        # 색상 및 스타일 결정
        # R4로 시작하는 파일인지 확인
        if label.startswith("R4"):
            # 빨간 계열 사용 (순서대로 또는 임의로 배정 가능하나, 여기서는 인덱스 기반으로 순환)
            # 사용자가 '두 개만 빨간 계열'이라고 했으므로, 첫 번째 R4는 진한 빨강, 두 번째는 연한 빨강 등으로 구분하거나
            # 단순히 빨간색 계열 톤을 다르게 적용. 
            # 간단한 접근: R4 파일들은 빨간색 계열, 나머지는 회색.
            # 만약 여러 R4가 있을 경우를 대비해 색상을 조금씩 다르게 하거나 동일한 빨간계열 사용.
            # 문제에서는 '두 개만'이라고 명시했으므로 해당 조건 만족시 빨간계열 적용.
            
            color = colors_red[red_file_count % len(colors_red)]
            linewidth = 1.5
            alpha = 0.9
            red_file_count += 1
        else:
            color = color_gray
            linewidth = 1.0
            alpha = 0.6
            
        # 플롯팅
        ax.plot(x_data, y_data_norm, label=label, color=color, linewidth=linewidth, alpha=alpha)
        
    except Exception as e:
        print(f"Error processing file {filepath}: {e}")

# 세로 점선 추가 (D band ~1350, G band ~1580)
ax.axvline(x=1350, color='black', linestyle='--', linewidth=1, alpha=0.7, label='D Band (1350 cm⁻¹)')
ax.axvline(x=1580, color='black', linestyle='--', linewidth=1, alpha=0.7, label='G Band (1580 cm⁻¹)')

# 그래프 장식
ax.set_xlabel("Raman Shift (cm⁻¹)", fontsize=12)
ax.set_ylabel("Normalized Intensity (a.u.)", fontsize=12)
ax.set_title("CNT Raman Spectra Normalized to G-band Peak (R4 highlighted)", fontsize=14)

# 범례 위치 조정 등
ax.legend(loc="best", fontsize=9)
ax.grid(True, linestyle="--", alpha=0.3)

# 축 범위 조정: 요청된 1200–1700 cm⁻¹ 구간만 표시
ax.set_xlim(1200, 1700)

plt.tight_layout()

# 저장
output_path = os.path.join(OUT_DIR, "raman_spectra_r4_highlighted.png")
plt.savefig(output_path, dpi=300, bbox_inches='tight')
print(f"Plot saved to {output_path}")
