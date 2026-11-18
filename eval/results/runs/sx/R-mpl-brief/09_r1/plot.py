import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

# 설정
DATA_FILE = "/home/chs/CNT/Plot/tests/inputs/TGA.xlsx"
OUT_DIR = "/home/chs/CNT/Plot/eval/results/runs/sx/R-mpl-brief/09_r1/out"
os.makedirs(OUT_DIR, exist_ok=True)

plt.rcParams['font.family'] = 'Noto Sans CJK KR'
plt.rcParams['axes.unicode_minus'] = False

def process_sheet(df, sheet_name):
    # 데이터 추출 (Temperature, Weight(%), D.W(%/C))
    x = df['Temperature'].values
    y1 = df['Weight(%)'].values
    y2 = df['D.W(%/C)'].values
    
    # 그림 생성
    fig, ax1 = plt.subplots(figsize=(8, 6))
    
    # Y1: Weight (%) - 왼쪽 축
    color1 = '#1f4e9c'
    line1, = ax1.plot(x, y1, color=color1, label='Weight (%)')
    ax1.set_xlabel('Temperature (°C)', fontsize=10)
    ax1.set_ylabel('Weight (%)', color=color1, fontsize=10)
    ax1.tick_params(axis='y', labelcolor=color1)
    
    # Y2: DTG (%/C) * -1 - 오른쪽 축
    ax2 = ax1.twinx()
    color2 = '#c0392b'
    line2, = ax2.plot(x, -y2, color=color2, label='DTG (%/C)')
    ax2.set_ylabel('DTG (%/C)', color=color2, fontsize=10)
    ax2.tick_params(axis='y', labelcolor=color2)
    
    # 제목
    ax1.set_title(sheet_name, fontsize=12)
    
    # 틱 방향 바깥쪽으로, 틱 라벨 크기 9 적용
    for ax in [ax1, ax2]:
        ax.tick_params(direction='out', labelsize=9)
    ax1.tick_params(axis='x', direction='out', labelsize=9)
    
    # 잔류량 표시 (Residue at ~800°C)
    idx_800 = np.argmin(np.abs(x - 800))
    residue_val = y1[idx_800]
    temp_residue = x[idx_800]
    ax1.plot(temp_residue, residue_val, 'o', color=color1, markersize=5)
    ax1.annotate(f'Residue {residue_val:.1f}%', 
                 xy=(temp_residue, residue_val), 
                 xytext=(temp_residue + 50, residue_val + 5),
                 arrowprops=dict(facecolor=color1, shrink=0.05, width=1, headwidth=5),
                 fontsize=9, color=color1)
    
    # 피크 표시 (Highest DTG peak above 150°C)
    mask_peak = x > 150
    if np.any(mask_peak):
        dtg_peaks = -y2[mask_peak]  # 부호 반전된 값들 중 최대값 찾기
        temps_peaks = x[mask_peak]
        
        max_dtg_idx_local = np.argmax(dtg_peaks)
        peak_temp = temps_peaks[max_dtg_idx_local]
        peak_val_original = y2[mask_peak][max_dtg_idx_local] # 원본 값
        
        # 그래프上的 위치는 반전된 값이므로 -peak_val_original 사용
        plot_y2_pos = -peak_val_original
        
        ax2.plot(peak_temp, plot_y2_pos, 'v', color=color2, markersize=7)
        ax2.annotate(f'{peak_temp:.0f} °C', 
                     xy=(peak_temp, plot_y2_pos), 
                     xytext=(peak_temp + 50, plot_y2_pos + abs(min(-y2))*0.1),
                     arrowprops=dict(facecolor=color2, shrink=0.05, width=1, headwidth=5),
                     fontsize=9, color=color2)

    # 범례
    lines = [line1, line2]
    labels = [l.get_label() for l in lines]
    ax1.legend(lines, labels, loc='center left', bbox_to_anchor=(0.02, 0.5), fontsize=9)
    
    # 저장
    safe_name = sheet_name.replace('/', '_').replace('\\', '_').replace(':', '_')
    out_path = os.path.join(OUT_DIR, f"{safe_name}.png")
    plt.tight_layout()
    plt.savefig(out_path, dpi=300)
    plt.close(fig)

# 파일 읽기 및 시트별 처리
xls = pd.ExcelFile(DATA_FILE)
for sheet in xls.sheet_names:
    df = pd.read_excel(xls, sheet_name=sheet)
    process_sheet(df, sheet)
