import pandas as pd
import matplotlib.pyplot as plt
import os

# 설정
OUT_DIR = "out/t1"
os.makedirs(OUT_DIR, exist_ok=True)

# 한글 폰트 설정
plt.rcParams["font.family"] = "Noto Sans CJK KR"
plt.rcParams['axes.unicode_minus'] = False

# 데이터 읽기
file_path = "data/run_log.xlsx"
df = pd.read_excel(file_path, sheet_name='런로그')

# 컬럼명 공백 및 특수문자 정리 (예: '생산속도 (g/h)' -> '생산속도' 또는 정확한 이름 확인 필요)
# 미리보기에는 공백이 있는 것으로 보이지만, 실제 Excel 파일의 헤더에 줄바꿈이나 다른 공백이 포함될 수 있어
# 정규식으로 모든 비숫자/비한글/비알파벳 문자를 제거하거나 매칭하는 방식을 사용합니다.
# 가장 안전한 방법은 컬럼명을 대조하여 원하는 데이터를 찾습니다.

def find_column(df, target_keyword):
    """컬럼명에서 키워드를 포함하는 컬럼을 반환합니다."""
    cols = [c for c in df.columns if target_keyword in str(c)]
    if not cols:
        raise KeyError(f"Column containing '{target_keyword}' not found.")
    return cols[0]

try:
    col_speed = find_column(df, '생산속도')
    col_time = find_column(df, '가동시간')
except KeyError as e:
    # 만약 키워드만으로는 부족하다면, 미리보기와 동일한 이름을 시도하되 공백 차이를 고려합니다.
    # 하지만 find_column이 더 강력하므로 일반적으로 성공할 것입니다.
    raise e

print(f"Found columns: Speed='{col_speed}', Time='{col_time}'")

# 일자 컬럼 변환
if df['일자'].dtype == object or isinstance(df['일자'].iloc[0], str):
    try:
        df['일자'] = pd.to_datetime(df['일자'], format='mixed', errors='coerce')
    except:
        df['일자'] = pd.to_datetime(df['일자'], errors='coerce')
else:
    df['일자'] = pd.to_datetime(df['일자'], errors='coerce')

# 유효한 날짜만 필터링
df = df.dropna(subset=['일자'])

# 단일 런 생산량(kg) 계산
df['런생산량_kg'] = df[col_speed] * df[col_time] / 1000

# 반응기별, 일자별로 합산하여 일일 총 생산량 구하기
daily_prod = df.groupby(['반응기', '일자'])['런생산량_kg'].sum().reset_index()

# 반응기별로 정렬하고 누적합 계산
daily_prod = daily_prod.sort_values(by=['반응기', '일자'])
daily_prod['누적생산량_kg'] = daily_prod.groupby('반응기')['런생산량_kg'].cumsum()

# 플롯 그리기
plt.figure(figsize=(12, 7))

reactors = ['R1', 'R2', 'R3', 'R4']
colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728'] 

for reactor, color in zip(reactors, colors):
    subset = daily_prod[daily_prod['반응기'] == reactor]
    if not subset.empty:
        plt.plot(subset['일자'], subset['누적생산량_kg'], label=reactor, color=color, linewidth=2)

plt.title('반응기별 누적 생산량 추이', fontsize=15)
plt.xlabel('일자', fontsize=12)
plt.ylabel('누적 생산량 (kg)', fontsize=12)
plt.legend(title='반응기', fontsize=10)
plt.grid(True, linestyle='--', alpha=0.7)
plt.xticks(rotation=45)
plt.tight_layout()

# 저장
output_file = os.path.join(OUT_DIR, "cumulative_production_by_reactor.png")
plt.savefig(output_file, dpi=300)
plt.close()

print(f"Plot saved to {output_file}")
