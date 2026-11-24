import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import os

# 설정
OUT_DIR = "out/t1"
os.makedirs(OUT_DIR, exist_ok=True)

plt.rcParams["font.family"] = "Noto Sans CJK KR"
plt.rcParams["axes.unicode_minus"] = False

# 데이터 로드
file_path = "data/diameters.csv"
df = pd.read_csv(file_path)

# 컬럼명 확인 및 매핑 (미리보기에 따라 실제 컬럼명은 '시료', '반응기' 등으로 변경될 수 있음)
# 미리보기 설명: A 시료 | B 반응기 | C 촉매로트 | D 직경(nm)
# 보통 pandas는 첫 번째 행을 헤더로 읽으므로 컬럼명이 실제로는 다른 이름일 가능성이 높습니다.
# 안전한 처리를 위해 컬럼명을 명시적으로 지정하거나, 기존 컬럼명을 기반으로 찾습니다.
# 만약 컬럼명이 'A', 'B', 'C', 'D'가 아니라면, 아래 코드로 수정합니다.

# 1. 컬럼이 'A', 'B', 'C', 'D'인 경우
if 'A' in df.columns:
    sample_col = 'A'
    diameter_col = 'D'
else:
    # 컬럼명이 한글이나 다른 이름일 경우를 대비하여 위치 기반 접근 또는 키워드 검색 시도
    # 미리보기에서 "A 시료", "D 직경(nm)"이라고 했으므로, 
    # 실제 CSV의 헤더가 "시료", "직경(nm)" 혹은 그 변형일 수 있습니다.
    # 가장 확실한 방법은 컬럼 인덱스나 이름을 유연하게 찾는 것입니다.
    
    # 예시: 컬럼명이 "시료", "반응기", "촉매로트", "직경(nm)" 라고 가정하고 코드 작성
    # 하지만 문제 상황에서는 KeyErrors가 발생했으므로, 실제 컬럼명을 알아야 합니다.
    # 일반적으로 이런 파일은 컬럼명이 명확할 것이므로, '시료'와 '직경'으로 찾아봅니다.
    
    found_sample = None
    found_diameter = None
    
    for col in df.columns:
        if '시료' in str(col):
            found_sample = col
        if '직경' in str(col):
            found_diameter = col
            
    if found_sample is None or found_diameter is None:
        # 마지막 수단으로 컬럼 순서 사용 (미리보기 순서: 시료, 반응기, 촉매로트, 직경)
        cols_list = df.columns.tolist()
        if len(cols_list) >= 4:
            found_sample = cols_list[0]
            found_diameter = cols_list[3]
        else:
            raise ValueError("데이터 형식을 인식할 수 없습니다.")
            
    sample_col = found_sample
    diameter_col = found_diameter

# TEM-03 시료만 필터링
tem_03_df = df[df[sample_col] == 'TEM-03']

if tem_03_df.empty:
    print("TEM-03 데이터가 없습니다.")
    # 빈 그림 저장
    fig, ax = plt.subplots(figsize=(10, 6))
    ax.text(0.5, 0.5, 'No Data for TEM-03', ha='center', va='center')
    ax.set_title('TEM-03 Diameter Distribution')
    save_path = os.path.join(OUT_DIR, "tem_03_diameter_distribution.png")
    plt.savefig(save_path, dpi=300)
    plt.close(fig)
else:
    diameters = tem_03_df[diameter_col].dropna()

    # 직경 분포 히스토그램 그리기
    fig, ax = plt.subplots(figsize=(10, 6))
    
    bins = 50 
    
    ax.hist(diameters, bins=bins, edgecolor='black', color='steelblue', alpha=0.7)
    
    # 평균과 중앙값 표시
    mean_val = diameters.mean()
    median_val = diameters.median()
    
    ax.axvline(mean_val, color='red', linestyle='dashed', linewidth=2, label=f'평균: {mean_val:.2f} nm')
    ax.axvline(median_val, color='green', linestyle='dashed', linewidth=2, label=f'중앙값: {median_val:.2f} nm')
    
    ax.set_title('TEM-03 시료의 CNT 직경 분포', fontsize=16)
    ax.set_xlabel('직경 (nm)', fontsize=14)
    ax.set_ylabel('빈도 (개수)', fontsize=14)
    ax.legend(loc='upper right')
    
    # 그리드 표시
    ax.grid(axis='y', linestyle='--', alpha=0.5)
    
    plt.tight_layout()
    
    # 저장
    save_path = os.path.join(OUT_DIR, "tem_03_diameter_distribution.png")
    plt.savefig(save_path, dpi=300)
    plt.close(fig)
    
    print(f"그림이 저장되었습니다: {save_path}")
    print(f"사용된 샘플 컬럼: {sample_col}, 직경 컬럼: {diameter_col}")
    print(f"데이터 포인트 수: {len(diameters)}")
    print(f"평균 직경: {mean_val:.2f} nm")
    print(f"표준 편차: {diameters.std():.2f} nm")
