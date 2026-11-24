import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import os

# 설정
OUT_DIR = "out/t2"
os.makedirs(OUT_DIR, exist_ok=True)
plt.rcParams["font.family"] = "Noto Sans CJK KR"
plt.rcParams["axes.unicode_minus"] = False

# 데이터 읽기
file_path = "data/run_log.xlsx"
df = pd.read_excel(file_path, sheet_name="런로그")

# 컬럼명 처리: 등급 컬럼 찾기 (이전 에러 방지 로직 재사용)
grade_col = None
for col in df.columns:
    if '등급' in str(col):
        grade_col = col
        break
if grade_col is None:
    grade_col = df.columns[-1] # 마지막 컬럼 가정

# 데이터 전처리
# 1. 합격 여부 판단 (A, B 등급은 합격)
df['합격 여부'] = df[grade_col].astype(str).str.strip().isin(['A', 'B'])

# 2. 월 추출
# 미리보기상 'yyyy-mm-dd' 형식의 문자열 또는 datetime 객체일 수 있음
# DateParseError가 발생한 경우, 컬럼 값 자체가 'yyyy-mm-dd'라는 문자열 리터럴이거나 파싱 불가능한 형태일 가능성 확인
# 일반적으로 Excel에서 날짜를 텍스트로 저장하면 '2026-03-02' 같은 형태. 
# 만약 실제 값이 'yyyy-mm-dd'라는 문자열이라면 데이터 오류이지만, 보통은 날짜 포맷팅된 문자열임.
# 안전한 방법: errors='coerce' 사용하여 파싱 안 되는 것은 NaT로 만들고, 그 중 유효한 것만 사용하거나
# 문자열 자체에서 '-' 위치로 잘라내어 월을 추출하는 것이 더 robust할 수 있음.
# 하지만 가장 흔한 원인은 datetime 컬럼이 이미 datetime object인데 다시 to_datetime을 시도하거나,
# 혹은 문자열이지만 특정 형식 때문에 파싱 실패.
# 여기서는 문자열인 경우 slicing으로 월을 추출하고, datetime인 경우 dt.month를 사용하는 혼합 방식 적용

date_col = None
for col in df.columns:
    if '일자' in str(col):
        date_col = col
        break

def extract_month(val):
    if isinstance(val, str):
        # 'yyyy-mm-dd' 형태에서 월 부분 추출 (index 5~7)
        try:
            return int(val.split('-')[1])
        except:
            return np.nan
    elif hasattr(val, 'month'):
        # datetime object
        return val.month
    else:
        # pd.Timestamp 등
        try:
            return pd.to_datetime(val).month
        except:
            return np.nan

df['월'] = df[date_col].apply(extract_month)

# 결측치(NaN) 제거
df = df.dropna(subset=['월'])
df['월'] = df['월'].astype(int)

# 반응기 목록 정렬
reactors = sorted(df['반응기'].unique())
months = sorted(df['월'].unique())

# 월별·반응기별 합격률 계산
results = []
for m in months:
    for r in reactors:
        subset = df[(df['월'] == m) & (df['반응기'] == r)]
        total_count = len(subset)
        pass_count = subset['합격 여부'].sum()
        
        if total_count > 0:
            rate = (pass_count / total_count) * 100
        else:
            rate = 0 
        
        results.append({
            '월': m,
            '반응기': r,
            '합격률': rate
        })

res_df = pd.DataFrame(results)

# 피벗 테이블 생성 (행: 월, 열: 반응기)
pivot_df = res_df.pivot(index='월', columns='반응기', values='합격률')

# 순서 재정렬 (반응기 이름대로 R1, R2, R3, 4)
pivot_df = pivot_df.reindex(columns=reactors)

# 그래프 그리기
fig, ax = plt.subplots(figsize=(12, 8))

x = np.arange(len(months))  # 월 위치
width = 0.2  # 막대 너비
multiplier = 0

colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728'] # R1-R4 색상 예시

for i, reactor in enumerate(reactors):
    offset = width * multiplier
    bars = ax.bar(x + offset, pivot_df[reactor], width, label=reactor, color=colors[i % len(colors)], edgecolor='black')
    
    # 값 라벨 추가
    for bar in bars:
        height = bar.get_height()
        if not np.isnan(height) and height > 0:
            ax.text(bar.get_x() + bar.get_width()/2., height + 1,
                    f'{height:.0f}', 
                    ha='center', va='bottom', fontsize=8, rotation=0)
                    
    multiplier += 1

# 축 설정
ax.set_title('월별 반응기별 합격률 (A·B 등급)', fontsize=16, pad=15)
ax.set_xlabel('월', fontsize=14)
ax.set_ylabel('합격률 (%)', fontsize=14)
ax.set_xticks(x)
ax.set_xticklabels([f'{m}월' for m in months])
ax.set_ylim(0, 110) # 상단 여백 확보
ax.legend(title='반응기', loc='upper right', ncol=len(reactors))
ax.grid(axis='y', linestyle='--', alpha=0.7)

plt.tight_layout()

# 저장
output_file = os.path.join(OUT_DIR, "monthly_reactor_pass_rate.png")
plt.savefig(output_file, dpi=300)
plt.close()
