import pandas as pd
import matplotlib.pyplot as plt
import os

# 환경 설정
plt.rcParams["font.family"] = "Noto Sans CJK KR"
OUT_DIR = "out/t1"
os.makedirs(OUT_DIR, exist_ok=True)

# 데이터 로드
file_path = "data/diameters.csv"
df = pd.read_csv(file_path)

# 컬럼 이름 공백 제거 및 첫 번째 컬럼 확인 (KeyError 방지용 로직 포함)
# 보통 'A 시료' 같은 헤더가 있지만, 앞뒤 공백이나 다른 명칭일 수 있어 가장 왼쪽 숫자/텍스트 컬럼을 사용하거나
# 에러가 났으므로 컬럼명을 명확히 하는 과정이 필요합니다.
# 미리보기에는 'A 시료'라고 되어 있지만, 실제 CSV 헤더 parsing 시 문제일 수 있습니다.
# 안전한 방법: 컬럼 인덱스 0을 기준으로 잡거나, 컬럼명에서 불필요한 공백 제거
df.columns = df.columns.str.strip()

sample_col = None
diameter_col = None

for col in df.columns:
    if '시료' in col or 'Sample' in col:
        sample_col = col
    if '직경' in col or 'Diameter' in col:
        diameter_col = col

# 만약 검색 실패 시 기본값 사용 (미리보기 기준)
if sample_col is None:
    sample_col = df.columns[0] # A 시료
if diameter_col is None:
    diameter_col = df.columns[3] # D 직경(nm) - 위치상 4번째일 가능성 높음, 또는 이름에 'nm' 포함된 것

print(f"Using Sample Column: {sample_col}, Diameter Column: {diameter_col}")

# 시료별 평균 직경 계산
grouped = df.groupby(sample_col)[diameter_col].mean().reset_index()

# 그래프 그리기
fig, ax = plt.subplots(figsize=(10, 6))

bars = ax.bar(grouped[sample_col], grouped[diameter_col], color='skyblue', edgecolor='black')

# 막대 위에 값 표시
for bar in bars:
    height = bar.get_height()
    ax.annotate(f'{height:.2f}',
                xy=(bar.get_x() + bar.get_width() / 2, height),
                xytext=(0, 3),  # 3 points vertical offset
                textcoords="offset points",
                ha='center', va='bottom', fontsize=10)

ax.set_title('시료별 평균 TEM 직경', fontsize=14)
ax.set_xlabel('시료 (Sample)', fontsize=12)
ax.set_ylabel('평균 직경 (nm)', fontsize=12)
ax.grid(axis='y', linestyle='--', alpha=0.7)

plt.tight_layout()

# 저장
output_path = os.path.join(OUT_DIR, 'tem_diameter_mean_bar.png')
plt.savefig(output_path, dpi=300)
plt.close()
