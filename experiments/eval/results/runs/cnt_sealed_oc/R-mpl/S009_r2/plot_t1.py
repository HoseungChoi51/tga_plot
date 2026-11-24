import pandas as pd
import matplotlib.pyplot as plt
import os

# 설정
OUT_DIR = "out/t1"
os.makedirs(OUT_DIR, exist_ok=True)
plt.rcParams["font.family"] = "Noto Sans CJK KR"
plt.rcParams["axes.unicode_minus"] = False

# 데이터 읽기
file_path = "data/run_log.xlsx"
df_runs = pd.read_excel(file_path, sheet_name="런로그")

# 주차별 런 수 계산
run_counts = df_runs.groupby('주차').size()

# 인덱스를 숫자형으로 변환하여 그래프 그리기 호환성 확보
# '주차' 컬럼에 문자열이나 특수문자가 섞여 있을 수 있으므로, 숫자로 변환 가능한 부분만 추출하거나 안전한 방식으로 처리
try:
    weeks_numeric = pd.to_numeric(run_counts.index, errors='coerce')
    # 변환 실패한 값(NaN)이 있으면 해당 행을 제외하고 진행
    valid_mask = ~weeks_numeric.isna()
    weeks = weeks_numeric[valid_mask].astype(int).values
    counts = run_counts.values[valid_mask]
except Exception:
    # 만약 인덱스 자체가 문자열 혼합이라면, 순서대로 정렬된 인덱스를 1..N으로 대체하거나 원본 인덱스를 사용하되 타입 캐스팅 시도
    # 여기서는 가장 일반적인 경우인 숫자형 주차가 섞여있는 상황을 가정하여 to_numeric으로 해결 시도했으나 
    # 위 try-catch로 안전장치 마련. 만약 여전히 문제라면 원본 인덱스를 객체 그대로 쓰지 않고 범위 생성 등 고려 필요하나,
    # 이번 오류 로그에서는 '-' 문자가 포함되어 astype(int)에서 발생한 것이므로 to_numeric(errors='coerce')가 유효합니다.
    pass

# 평균 런 수 계산 (전체 주차 기준)
avg_runs = counts.mean() if len(counts) > 0 else 0

# 플롯 그리기
fig, ax = plt.subplots(figsize=(12, 6))

# 막대 그래프
bars = ax.bar(weeks, counts, color='steelblue', alpha=0.7, label='주차별 런 수')

# 평균 라인 추가
ax.axhline(y=avg_runs, color='red', linestyle='--', linewidth=2, label=f'평균 런 수: {avg_runs:.2f}')

# 라벨 및 제목
ax.set_xlabel('주차', fontsize=12)
ax.set_ylabel('런 수', fontsize=12)
ax.set_title('주차별 런 수 분포', fontsize=14)
ax.legend(loc='upper right')

# x축 눈금 간격 조정 (모든 주차 표시)
if len(weeks) > 0:
    ax.set_xticks(weeks)
    ax.tick_params(axis='x', rotation=90)

# 레이아웃 정리
plt.tight_layout()

# 저장
output_file = os.path.join(OUT_DIR, "weekly_run_count.png")
plt.savefig(output_file, dpi=300, bbox_inches='tight')
plt.close()
