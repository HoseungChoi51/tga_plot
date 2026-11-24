import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

# 환경 설정
OUT_DIR = "out/t1"
os.makedirs(OUT_DIR, exist_ok=True)
plt.rcParams["font.family"] = "Noto Sans CJK KR"
plt.rcParams["axes.unicode_minus"] = False

# 파일 경로 정의
files = {
    "R1-260326-1": "data/raman/R1-260326-1.csv",
    "R2-260616-1": "data/raman/R2-260616-1.csv",
    "R4-260721-1": "data/raman/R4-260721-1.csv"
}

fig, ax = plt.subplots(figsize=(10, 6))

for label, path in files.items():
    # 데이터 로드 (CSV 가정, 헤더가 있는 경우 처리)
    try:
        df = pd.read_csv(path)
    except Exception:
        # 만약 세미콜론이나 다른 구분자가 필요한 경우 fallback
        df = pd.read_csv(path, sep=';', decimal=',')
    
    # 컬럼명 자동 감지 또는 고정된 이름 사용
    # 미리보기에 따르면 'A Raman Shift (cm-1)' 및 'B Intensity (a.u.)' 구조와 유사하거나 단순화됨
    # 실제 데이터에서 첫 번째 열이 x, 두 번째 열이 y인 것으로 가정하되, 컬럼명을 명확히 함
    if df.shape[1] >= 2:
        wavenumber_col = df.columns[0]
        intensity_col = df.columns[1]
    else:
        raise ValueError(f"Not enough columns in {path}")
        
    x = df[wavenumber_col].values.astype(float)
    y = df[intensity_col].values.astype(float)
    
    # 1. 베이스라인 보정 (Linear Baseline Correction)
    # 기준점: 1100 cm-1 (+/- 10), 1800 cm-1 (+/- 10)
    def get_mean_intensity_at(center, window=10):
        mask = (x >= center - window) & (x <= center + window)
        if not np.any(mask):
            return 0.0
        return np.mean(y[mask])
    
    baseline_y1 = get_mean_intensity_at(1100)
    baseline_y2 = get_mean_intensity_at(1800)
    
    # 직선 방정식 y = mx + b 계산
    if x.max() == x.min():
        m = 0
        b = baseline_y1
    else:
        # 간단한 선형 회귀 대신 두 점 사이의 기울기 사용 (요청사항: 두 지점 평균을 잇는 선)
        dx = 1800 - 1100
        dy = baseline_y2 - baseline_y1
        m = dy / dx
        b = baseline_y1 - m * 1100
        
    baseline = m * x + b
    y_corrected = y - baseline
    
    # 2. 정규화 (Normalization)
    # G 밴드 영역: 1550–1620 cm-1 에서의 최대값을 1로 만듦
    mask_g_band = (x >= 1550) & (x <= 1620)
    if np.any(mask_g_band):
        max_val_g = np.max(y_corrected[mask_g_band])
        if max_val_g != 0:
            y_normalized = y_corrected / max_val_g
        else:
            y_normalized = y_corrected
    else:
        # G 밴드가 없으면 전체 최소/최대 등으로 대체하거나 그대로 사용 (여기서는 전체 최대 기준으로 할 수 있으나, 
        # 요청은 G 밴드 기준이므로 데이터 부족 시에는 원본 유지 또는 경고 필요. 여기서는 안전장치로 전체 최대 사용)
        max_val_all = np.max(y_corrected)
        if max_val_all != 0:
            y_normalized = y_corrected / max_val_all
        else:
            y_normalized = y_corrected

    # 3. 프로팅 범위 제한 (1000–2000 cm-1)
    plot_mask = (x >= 1000) & (x <= 2000)
    x_plot = x[plot_mask]
    y_plot = y_normalized[plot_mask]
    
    ax.plot(x_plot, y_plot, label=label, linewidth=1.5)

ax.set_title("Raman Spectra Overlay (Baseline Corrected & G-Band Normalized)")
ax.set_xlabel("Raman Shift (cm⁻¹)")
ax.set_ylabel("Normalized Intensity (a.u.)")
ax.legend()
ax.grid(True, linestyle='--', alpha=0.6)
ax.set_xlim(1000, 2000)

output_path = os.path.join(OUT_DIR, "raman_overlay.png")
plt.tight_layout()
plt.savefig(output_path, dpi=300)
plt.close()
