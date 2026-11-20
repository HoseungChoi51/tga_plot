import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

# 설정
OUT_DIR = "out/t1"
os.makedirs(OUT_DIR, exist_ok=True)

plt.rcParams["font.family"] = "Noto Sans CJK KR"
plt.rcParams["axes.unicode_minus"] = False

data_dir = "data/raman"
results = []

# 파일 목록 가져오기
try:
    files = [f for f in os.listdir(data_dir) if f.endswith('.csv')]
except FileNotFoundError:
    print(f"Directory not found: {data_dir}")
    files = []

for filename in sorted(files):
    filepath = os.path.join(data_dir, filename)
    try:
        # CSV 읽기 (인코딩 및 구분자 자동 감지 시도)
        df = pd.read_csv(filepath)
        
        # 컬럼명 확인 및 데이터 추출
        # 미리보기에 따르면 'Raman Shift (cm-1)'와 'Intensity (a.u.)' 또는 유사한 이름이 있을 수 있음
        shift_col = None
        intensity_col = None
        
        for col in df.columns:
            col_str = str(col).lower()
            if 'shift' in col_str or 'wavenumber' in col_str:
                shift_col = col
            elif 'intensity' in col_str or 'a.u.' in col_str:
                intensity_col = col
        
        if shift_col is None or intensity_col is None:
            continue
            
        shifts = df[shift_col].values
        intensities = df[intensity_col].values
        
        # I_G 계산: 1550–1620 cm⁻¹ 범위 내 최대 강도
        mask_g = (shifts >= 1550) & (shifts <= 1620)
        if not np.any(mask_g):
            continue
        i_g = np.max(intensities[mask_g])
        
        # I_D 계산: 1300–1400 cm⁻¹ 범위 내 최대 강도
        mask_d = (shifts >= 1300) & (shifts <= 1400)
        if not np.any(mask_d):
            continue
        i_d = np.max(intensities[mask_d])
        
        # 비율 계산
        ratio = i_g / i_d
        
        # 라벨 생성 (파일명에서 확장자 제거 등)
        label = os.path.splitext(filename)[0]
        
        results.append({'Label': label, 'I_G/I_D': ratio})
        
    except Exception as e:
        print(f"Error processing {filename}: {e}")
        continue

if not results:
    print("No data processed.")
else:
    res_df = pd.DataFrame(results)
    
    # 높은 순으로 정렬
    res_df = res_df.sort_values(by='I_G/I_D', ascending=False).reset_index(drop=True)
    
    # 그래프 그리기
    fig, ax = plt.subplots(figsize=(10, 6))
    
    bars = ax.bar(res_df['Label'], res_df['I_G/I_D'], color='#4C72B0', edgecolor='black')
    
    # 값 텍스트 표시
    for bar, value in zip(bars, res_df['I_G/I_D']):
        height = bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2., height,
                f'{value:.2f}',
                ha='center', va='bottom', fontsize=9)
    
    ax.set_title('라만 스펙트럼 기반 I_G/I_D 비율 비교', fontsize=14)
    ax.set_xlabel('샘플 명', fontsize=12)
    ax.set_ylabel('I_G / I_D 비율', fontsize=12)
    
    # x축 라벨 회전하여 가독성 확보
    plt.xticks(rotation=45, ha='right')
    
    plt.tight_layout()
    
    save_path = os.path.join(OUT_DIR, 'raman_ratio_barplot.png')
    plt.savefig(save_path, dpi=300)
    plt.close()
    print(f"Plot saved to {save_path}")
