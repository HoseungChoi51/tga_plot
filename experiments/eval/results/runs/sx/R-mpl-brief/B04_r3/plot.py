import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from scipy.signal import find_peaks
import os

# 데이터 파일 경로 및 출력 디렉토리 설정
DATA_FILE = "/home/chs/Work/tga_plot/eval/inputs_b/xrd.csv"
OUT_DIR = "/home/chs/Work/tga_plot/eval/results/runs/sx/R-mpl-brief/B04_r3/out"

# 한글 폰트 설정
plt.rcParams['font.family'] = 'Noto Sans CJK KR'
plt.rcParams['axes.unicode_minus'] = False

def plot_xrd():
    # 1. 데이터 읽기
    df = pd.read_csv(DATA_FILE)
    
    # 컬럼명 확인 및 할당 (미리보기 기준: A=2Theta, B=Intensity)
    x_col = df.columns[0]
    y_col = df.columns[1]
    
    two_theta = df[x_col].values
    intensity = df[y_col].values
    
    # 2. 강한 피크 5개 찾기
    # find_peaks 사용 시 height나 distance 등을 통해 노이즈 필터링 가능
    # 여기서는 가장 높은 값(top 5)을 기준으로 하되, 서로 너무 가까운 피크는 제외하는 로직 적용
    peaks, properties = find_peaks(intensity, distance=10, prominence=50)
    
    if len(peaks) == 0:
        # 피크가 안 잡히면 그냥 최대값 위주로 처리하거나 빈 리스트로 둠
        peak_indices = []
    else:
        # 강도(intensity) 순으로 정렬하여 상위 5개 인덱스 추출
        peak_intensities = intensity[peaks]
        sorted_peak_indices = peaks[np.argsort(peak_intensities)[::-1]]
        top_5_peak_indices = sorted_peak_indices[:5]
        
        # 2theta 값과 해당 강도 저장
        peak_two_thetas = two_theta[top_5_peak_indices]
        peak_intensities_top = intensity[top_5_peak_indices]
    
    # 3. 그래프 그리기
    fig, ax = plt.subplots(figsize=(10, 6))
    
    # XRD 패턴 선 그리기
    ax.plot(two_theta, intensity, color='#1f4e9c', linewidth=1.2, label='XRD Pattern')
    
    # 강한 피크 표시
    for i, (pt, pi) in enumerate(zip(peak_two_thetas, peak_intensities_top)):
        # 마커 표시
        ax.scatter(pt, pi, color='red', s=50, zorder=5)
        # 텍스트 라벨: 2θ 값 표시 (소수점 둘째 자리까지)
        label_text = f"{pt:.2f}°"
        # 위치 조정: 피크 위에 살짝 띄움
        ax.annotate(label_text, 
                    xy=(pt, pi), 
                    xytext=(0, 15), 
                    textcoords='offset points',
                    ha='center', 
                    va='bottom',
                    fontsize=9,
                    color='black',
                    bbox=dict(boxstyle="round,pad=0.3", fc="white", ec="gray", alpha=0.8))

    # 축 라벨 및 제목
    ax.set_xlabel('2Theta (deg)', fontsize=12)
    ax.set_ylabel('Intensity (counts)', fontsize=12)
    ax.set_title('XRD Pattern with Top 5 Peaks', fontsize=14)
    
    # 격자선
    ax.grid(True, linestyle='--', alpha=0.5)
    
    # 범례
    ax.legend(loc='upper right')
    
    # 레이아웃 자동 조절
    plt.tight_layout()
    
    # 4. 파일 저장
    output_filename = "xrd_pattern.png"
    output_path = os.path.join(OUT_DIR, output_filename)
    
    # 디렉토리가 없으면 생성
    os.makedirs(OUT_DIR, exist_ok=True)
    
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close(fig)

if __name__ == "__main__":
    plot_xrd()
