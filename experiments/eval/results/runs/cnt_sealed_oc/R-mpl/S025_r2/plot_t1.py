import os
import glob
import pandas as pd
import matplotlib.pyplot as plt

# 설정
OUT_DIR = "out/t1"
os.makedirs(OUT_DIR, exist_ok=True)
plt.rcParams["font.family"] = "Noto Sans CJK KR"
plt.rcParams["axes.unicode_minus"] = False

# 파일 경로 패턴
data_pattern = "data/raman/*.csv"
files = sorted(glob.glob(data_pattern))

results = []

for filepath in files:
    # 파일명에서 라벨 추출 (예: R1-260326-1)
    filename = os.path.basename(filepath)
    label = os.path.splitext(filename)[0]
    
    try:
        # CSV 읽기 (인코딩은 utf-8 또는 euc-kr 시도 가능하지만 일반적으로 utf-8)
        # 헤더가 'A Raman Shift (cm-1)' 같은 형태일 수 있음
        df = pd.read_csv(filepath)
        
        # 컬럼명 자동 감지 (첫 번째 컬럼이 파수, 두 번째가 강도라고 가정)
        # 미리보기에 따르면 A는 Raman Shift, B는 Intensity
        cols = df.columns.tolist()
        if len(cols) >= 2:
            x_col = cols[0]
            y_col = cols[1]
        else:
            continue
            
        shifts = df[x_col].values
        intensities = df[y_col].values
        
        # I_G 계산: 1550–1620 cm⁻¹ 범위의 최대값
        mask_g = (shifts >= 1550) & (shifts <= 1620)
        if not any(mask_g):
            i_g = 0
        else:
            i_g = max(intensities[mask_g])
            
        # I_D 계산: 1300–1400 cm⁻¹ 범위의 최대값
        mask_d = (shifts >= 1300) & (shifts <= 1400)
        if not any(mask_d):
            i_d = 0
        else:
            i_d = max(intensities[mask_d])
            
        # 비율 계산
        if i_d > 0:
            ratio = i_g / i_d
        else:
            ratio = float('inf') if i_g > 0 else 0.0
            
        results.append({'label': label, 'ratio': ratio})
        
    except Exception as e:
        print(f"Error processing {filepath}: {e}")
        continue

if not results:
    print("No data processed.")
else:
    # 데이터 프레임으로 변환 및 정렬 (높은 순서대로)
    df_res = pd.DataFrame(results)
    df_res.sort_values(by='ratio', ascending=False, inplace=True)
    df_res.reset_index(drop=True, inplace=True)
    
    # 막대 그래프 그리기
    fig, ax = plt.subplots(figsize=(10, 6))
    
    bars = ax.bar(df_res['label'], df_res['ratio'], color='steelblue')
    
    # 각 막대 위에 값 표시
    for bar, val in zip(bars, df_res['ratio']):
        height = bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2., height,
                f'{val:.2f}',
                ha='center', va='bottom', fontsize=9)
    
    ax.set_ylabel('I_G / I_D Ratio')
    ax.set_title('Raman I_G/I_D Ratio by Sample (Sorted Descending)')
    ax.set_xlabel('Sample ID')
    
    # X축 레이블 회전 (길어지면 가독성 위해)
    plt.xticks(rotation=45, ha='right')
    
    # Y축 시작점을 0으로 고정하지 않고 데이터 범위 맞게 조절하되, 보통 이 값들은 양수이므로 0 포함해도 됨
    # 높은 순 정렬이므로 자연스럽게 내림차순 배치됨
    
    plt.tight_layout()
    
    output_path = os.path.join(OUT_DIR, "raman_IG_ID_ratio_bar.png")
    plt.savefig(output_path, dpi=300)
    plt.close()
    print(f"Plot saved to {output_path}")
