import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import os

# 환경 설정
plt.rcParams["font.family"] = "Noto Sans CJK KR"
plt.rcParams["axes.unicode_minus"] = False

OUT_DIR = "out/t1"
os.makedirs(OUT_DIR, exist_ok=True)

# 데이터 읽기
file_path = "data/diameters.csv"
df = pd.read_csv(file_path)

# 컬럼 이름 정리 (공백 제거 등)
df.columns = df.columns.str.strip()

# 'A 시료' 컬럼 찾기 (정확한 매칭 또는 부분 매칭 시도)
sample_col = None
for col in df.columns:
    if '시료' in str(col) or 'Sample' in str(col):
        sample_col = col
        break

if sample_col is None:
    # 혹시 첫 번째 컬럼이 시료명일 가능성 고려 (데이터 미리보기 기준 A 시료가 첫번째)
    if len(df.columns) > 0:
        sample_col = df.columns[0]

diameter_col = None
for col in df.columns:
    if '직경' in str(col) or 'Diameter' in str(col):
        diameter_col = col
        break

if diameter_col is None:
    # 미리보기상 D 직경(nm)가 네 번째 컬럼이므로 인덱스 접근도 고려 가능하지만, 이름 기반이 안전함
    raise ValueError("Could not find diameter column")

# 타입 변환 및 결측치 처리
df[sample_col] = df[sample_col].astype(str).str.strip()
df[diameter_col] = pd.to_numeric(df[diameter_col], errors='coerce')

# TEM-03 필터링
mask_tem03 = df[sample_col] == 'TEM-03'
data_tem03 = df.loc[mask_tem03, diameter_col].dropna()

if data_tem03.empty:
    print("TEM-03 데이터를 찾을 수 없습니다.")
else:
    # 직경 분포 히스토그램 그리기
    fig, ax = plt.subplots(figsize=(10, 6))
    
    # 구간(bin)을 자동으로 적절히 나눔 (Sturges's rule or similar default behavior in numpy/pandas)
    bins = 20  # 적절한 개수의 bin
    
    ax.hist(data_tem03, bins=bins, color='skyblue', edgecolor='black', alpha=0.7)
    
    # 통계 정보 계산
    mean_d = data_tem03.mean()
    std_d = data_tem03.std()
    median_d = data_tem03.median()
    
    # 평균선 표시
    ax.axvline(mean_d, color='red', linestyle='dashed', linewidth=1.5, label=f'평균: {mean_d:.2f} nm')
    ax.axvline(median_d, color='green', linestyle='dotted', linewidth=1.5, label=f'중위값: {median_d:.2f} nm')
    
    # 차트 제목 및 축 레이블
    ax.set_title('TEM-03 시료 직경 분포', fontsize=14)
    ax.set_xlabel('직경 (nm)', fontsize=12)
    ax.set_ylabel('빈도 (Count)', fontsize=12)
    
    # 범례
    ax.legend(loc='upper right')
    
    # 그래프 저장
    save_path = os.path.join(OUT_DIR, 'tem03_diameter_distribution.png')
    plt.tight_layout()
    plt.savefig(save_path, dpi=300)
    plt.close()
    print(f"그래프가 저장되었습니다: {save_path}")
