import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import os
import glob

# 설정
plt.rcParams["font.family"] = "Noto Sans CJK KR"
OUT_DIR = "out/t1"
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
        # CSV 읽기 (세미콜론 구분자 또는 쉼표 구분자 모두 지원 시도)
        # 미리보기에 따르면 일반적인 CSV 형식으로 보임. 
        # 만약 세미콜론과 소수점 콤마 문제라면 sep=';' 및 decimal=',' 필요할 수 있으나,
        # 미리보기가 [수치]로 표시되었으므로 표준 float 파싱이 가능하다고 가정.
        # 안전을 위해 기본 인자로 읽고 실패하면 대안 시도
        
        df = pd.read_csv(filepath)
        
        # 컬럼 이름 확인 (미리보기: 'A Raman Shift (cm-1)', 'B Intensity (a.u.)')
        # 실제 컬럼명이 이대로 올 수도 있고, 공백 처리 등 변동 있을 수 있음.
        # 일반적으로 첫 번째 컬럼은 x, 두 번째는 y
        
        cols = df.columns.tolist()
        if len(cols) < 2:
            continue
            
        x_col = cols[0]
        y_col = cols[1]
        
        # 데이터 정렬 (x축 오름차순)
        sort_idx = df[x_col].argsort()
        x_data = df.iloc[sort_idx][x_col].values
        y_data = df.iloc[sort_idx][y_col].values
        
        # 플롯팅
        ax.plot(x_data, y_data, label=label, linewidth=1.2, alpha=0.8)
        
    except Exception as e:
        print(f"Error processing file {filepath}: {e}")

# 그래프 장식
ax.set_xlabel("Raman Shift (cm⁻¹)", fontsize=12)
ax.set_ylabel("Intensity (a.u.)", fontsize=12)
ax.set_title("CNT Raman Spectra Comparison (All Samples)", fontsize=14)
ax.legend(loc="best", fontsize=9)
ax.grid(True, linestyle="--", alpha=0.6)

# 축 범위 조정 (데이터 기반이지만 보통 1000~3000 영역)
ax.set_xlim(1000, 3000) 

plt.tight_layout()

# 저장
output_path = os.path.join(OUT_DIR, "raman_spectra_all.png")
plt.savefig(output_path, dpi=300, bbox_inches='tight')
print(f"Plot saved to {output_path}")
