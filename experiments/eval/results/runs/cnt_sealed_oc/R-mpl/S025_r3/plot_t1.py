import os
import glob
import pandas as pd
import matplotlib.pyplot as plt

# 설정
OUT_DIR = "out/t1"
os.makedirs(OUT_DIR, exist_ok=True)

plt.rcParams["font.family"] = "Noto Sans CJK KR"
plt.rcParams["axes.unicode_minus"] = False

# 파일 목록 가져오기
file_pattern = "data/raman/*.csv"
files = sorted(glob.glob(file_pattern))

results = []

for filepath in files:
    try:
        # CSV 읽기 (인코딩 이슈 대비 utf-8-sig 또는 cp949 시도, 실패시 latin1 등 기본 utf-8)
        # 헤더가 'A Raman Shift...' 등으로 시작할 수 있음. 컬럼명이 명확하지 않을 수 있으므로 위치 기반으로 처리하거나
        # 첫 번째 컬럼을 x축, 두 번째를 y축으로 간주하는 것이 안전함.
        # 미리보기상 A열이 Raman Shift, B열이 Intensity
        
        df = pd.read_csv(filepath, encoding='utf-8')
        
        # 컬럼명 정리: 만약 컬럼명에 빈칸이나 특수문자가 있어도 인덱스 0, 1을 사용
        if df.shape[1] < 2:
            continue
            
        wavenumber = df.iloc[:, 0].values
        intensity = df.iloc[:, 1].values
        
        # I_G 계산: 1550–1620 cm⁻¹ 범위 내 최대 강도
        mask_g = (wavenumber >= 1550) & (wavenumber <= 1620)
        if not mask_g.any():
            ig = 0
        else:
            ig = intensity[mask_g].max()
            
        # I_D 계산: 1300–1400 cm⁻¹ 범위 내 최대 강도
        mask_d = (wavenumber >= 1300) & (wavenumber <= 1400)
        if not mask_d.any():
            id_ = 0
        else:
            id_ = intensity[mask_d].max()
            
        # I_G/I_D 비율 계산 (분모가 0이면 nan 또는 큰 값 처리, 여기서는 0 나누기 방지)
        ratio = ig / id_ if id_ > 0 else float('inf')
        
        # 파일 이름에서 라벨 추출 (예: R1-260326-1)
        basename = os.path.basename(filepath)
        label = os.path.splitext(basename)[0]
        
        results.append({
            'label': label,
            'ratio': ratio
        })
        
    except Exception as e:
        print(f"Error processing {filepath}: {e}")

if not results:
    raise ValueError("No valid data found.")

df_results = pd.DataFrame(results)
df_results['ratio'] = df_results['ratio'].replace([float('inf'), -float('inf')], float('nan'))
df_results.dropna(subset=['ratio'], inplace=True)

# 높은 순으로 정렬
df_sorted = df_results.sort_values(by='ratio', ascending=False).reset_index(drop=True)

# 막대 그래프 그리기
fig, ax = plt.subplots(figsize=(10, 6))
bars = ax.bar(df_sorted['label'], df_sorted['ratio'], color='steelblue')

ax.set_title('Raman I_G/I_D Ratio (Peak Height Ratio)', fontsize=14)
ax.set_xlabel('Sample', fontsize=12)
ax.set_ylabel('I_G / I_D', fontsize=12)

# x축 레이블 회전 및 크기 조정
plt.xticks(rotation=45, ha='right')

# 막대 위에 값 표시
for bar in bars:
    height = bar.get_height()
    ax.text(bar.get_x() + bar.get_width()/2., height,
            f'{height:.2f}',
            ha='center', va='bottom', fontsize=9)

plt.tight_layout()

output_path = os.path.join(OUT_DIR, "raman_ig_id_ratio.png")
plt.savefig(output_path, dpi=300)
plt.close()
