import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import os
import glob

# 설정
plt.rcParams["font.family"] = "Noto Sans CJK KR"
OUT_DIR = "out/t2"
os.makedirs(OUT_DIR, exist_ok=True)

# 데이터 파일 경로 패턴
data_dir = "data/raman"
pattern = os.path.join(data_dir, "*.csv")
files = glob.glob(pattern)

if not files:
    raise FileNotFoundError(f"No CSV files found in {data_dir}")

fig, ax = plt.subplots(figsize=(12, 8))

# 각 파일을 읽어 그래프에 추가
for filepath in sorted(files):
    # 파일명에서 라벨 생성 (예: R1-260326-1.csv -> R1-260326-1)
    label = os.path.basename(filepath).replace('.csv', '')
    
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
            # G 밴드 데이터가 없는 경우 원본 사용 또는 전체 최대값으로 정규화? 
            # 요청사항은 'G 밴드 최대값이 1'이므로, 해당 구간 데이터가 없으면 정규화 불가.
            # 다만 미리보기상 1000~3000 범위이므로 1550-1620 구간은 포함될 가능성이 높음.
            y_data_norm = y_data
            
        # 플롯팅 (정규화된 데이터 사용)
        ax.plot(x_data, y_data_norm, label=label, linewidth=1.2, alpha=0.8)
        
    except Exception as e:
        print(f"Error processing file {filepath}: {e}")

# 그래프 장식
ax.set_xlabel("Raman Shift (cm⁻¹)", fontsize=12)
ax.set_ylabel("Normalized Intensity (a.u.)", fontsize=12)
ax.set_title("CNT Raman Spectra Normalized to G-band Peak (1550–1620 cm⁻¹)", fontsize=14)
ax.legend(loc="best", fontsize=9)
ax.grid(True, linestyle="--", alpha=0.6)

# 축 범위 조정: 요청된 1200–1700 cm⁻¹ 구간만 표시
ax.set_xlim(1200, 1700)

plt.tight_layout()

# 저장
output_path = os.path.join(OUT_DIR, "raman_spectra_normalized_gband.png")
plt.savefig(output_path, dpi=300, bbox_inches='tight')
print(f"Plot saved to {output_path}")
